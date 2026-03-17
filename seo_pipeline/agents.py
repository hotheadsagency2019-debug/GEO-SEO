"""
Nine specialized SEO/GEO agents for HotHeads Band blog (hot-head.ru).

Each agent:
  - receives a PipelineContext with all upstream results
  - calls Claude claude-opus-4-6 with adaptive thinking + streaming
  - returns a structured Pydantic model
  - updates the PipelineContext in place

Output: Tilda Zero Block-compatible HTML with HotHeads Band branding.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional, Type, TypeVar

import anthropic
from pydantic import BaseModel

from .brand_config import (
    AVAILABLE_CLASSES,
    CONTENT_RULES,
    GEO_CONTENT_RULES,
    HTML_CLOSE,
    HTML_OPEN,
)
from .models import (
    CaseStudy,
    DraftArticle,
    EditedArticle,
    ExampleItem,
    FactData,
    FactItem,
    HTMLArticle,
    InternalLink,
    KeywordAnalysis,
    LinkData,
    LinkedHTMLArticle,
    LSIData,
    MatchedCase,
    MatchedCases,
    PipelineContext,
    QAChecklistItem,
    QAReport,
    StatItem,
)

MODEL = "claude-opus-4-6"
T = TypeVar("T", bound=BaseModel)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _stream_call(client: anthropic.Anthropic, system: str, user: str) -> str:
    """Stream a Claude response and return the full text."""
    full_text = ""
    with client.messages.stream(
        model=MODEL,
        max_tokens=8192,
        thinking={"type": "adaptive"},
        system=system,
        messages=[{"role": "user", "content": user}],
    ) as stream:
        for text in stream.text_stream:
            full_text += text
    return full_text


def _parse_json_response(raw: str) -> Dict[str, Any]:
    """Extract the first JSON object or array from the model output."""
    # Strip outermost markdown code fence (first and last occurrence only)
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*\n?", "", raw)
    raw = re.sub(r"\n?```\s*$", "", raw)
    raw = raw.strip()

    # Find the first JSON start character and parse exactly one value,
    # ignoring any trailing text (e.g. Claude's post-JSON commentary).
    decoder = json.JSONDecoder()
    for i, ch in enumerate(raw):
        if ch in ("{", "["):
            try:
                obj, _ = decoder.raw_decode(raw, i)
                return obj
            except json.JSONDecodeError:
                continue
    raise ValueError(f"No valid JSON found in model response. First 300 chars: {raw[:300]}")


def _call_structured(
    client: anthropic.Anthropic,
    system: str,
    user: str,
    model_cls: Type[T],
) -> T:
    system_with_json = (
        system
        + "\n\nIMPORTANT: Your entire response MUST be valid JSON matching the schema "
        "described. Do not add any text before or after the JSON object."
    )
    raw = _stream_call(client, system_with_json, user)
    data = _parse_json_response(raw)
    return model_cls.model_validate(data)


# ─── Agent 0: Cases Matcher ───────────────────────────────────────────────────
# Runs only when a Google Sheets cases list is provided.
# Selects the 3-5 most topically relevant case studies so they can be
# mentioned naturally in the article (Agent 4) and linked internally (Agent 7).

SYSTEM_CASES_MATCHER = f"""You are an SEO strategist for HotHeads Band agency (hot-head.ru).
Given a new article topic and a full list of published agency case studies,
select the 3-5 most relevant cases to mention and link in the article.

{CONTENT_RULES}

Selection criteria (in order of priority):
1. Topical match — the case covers the same service, channel, or industry as the article
2. Problem-solution fit — the case demonstrates solving the problem the article discusses
3. Authority signal — the case proves HotHeads Band expertise in the article's topic

For each selected case, write a natural Russian anchor text that could appear
inside a sentence of the article (not the page title, not a call-to-action).

Return JSON:
{{
  "cases": [
    {{
      "url": "/keisi/some-case/",
      "title": "Case title",
      "description": "Brief case description",
      "result": "Key result / metric",
      "suggested_anchor": "natural anchor text in Russian",
      "relevance_reason": "Why this case is relevant to the article topic"
    }}
  ],
  "reasoning": "Overall reasoning for the selection"
}}"""


def agent_cases_matcher(
    client: anthropic.Anthropic,
    ctx: PipelineContext,
    all_cases: list,          # List[CaseStudy] — typed loosely to avoid circular import
) -> PipelineContext:
    row = ctx.row

    cases_text = "\n".join(
        f"- URL: {c.url}\n"
        f"  Title: {c.title}\n"
        f"  Industry: {c.industry or '—'}\n"
        f"  Services: {c.services or '—'}\n"
        f"  Result: {c.result or '—'}\n"
        f"  Keywords: {c.keywords or '—'}\n"
        f"  Description: {c.description or '—'}"
        for c in all_cases
    )

    user = f"""New article topic: {row.main_keyword}
Article type: {row.article_type}
Cluster keywords: {row.cluster_keywords}
Search intent: {row.search_intent}

PUBLISHED CASE STUDIES ({len(all_cases)} total):
{cases_text}

Select 3-5 most relevant cases. Write natural Russian anchor text for each."""
    ctx.matched_cases = _call_structured(client, SYSTEM_CASES_MATCHER, user, MatchedCases)
    return ctx


# ─── Agent 1: Keyword Analyzer ────────────────────────────────────────────────

SYSTEM_KEYWORD_ANALYZER = f"""You are a senior SEO strategist and content architect for HotHeads Band agency (hot-head.ru).
Analyse a keyword cluster and produce a complete article structure.

{CONTENT_RULES}

SEO Title rules:
- Max 60 chars, include main keyword
- For GEO articles: include year (2026), word «Лучшие» / «Лучший», max 70 chars

H2 rules: every H2 MUST contain a search keyword. No generic headings.
❌ «Введение» → ✅ «Введение в Telegram Ads 2026: как это работает»

Return JSON:
{{
  "title": "SEO title (max 60 chars for SEO, 70 for GEO)",
  "h1": "H1 heading — includes main keyword",
  "h2_sections": ["Section with keyword 1", "Section with keyword 2", ...],
  "primary_keywords": ["kw1", "kw2"],
  "secondary_keywords": ["kw1", ...],
  "meta_description": "150-160 chars with keywords",
  "intent": "refined intent label",
  "article_tag": "short category tag (e.g. Контекстная реклама)"
}}"""


def agent_keyword_analyzer(client: anthropic.Anthropic, ctx: PipelineContext) -> PipelineContext:
    row = ctx.row
    user = f"""Keyword data:
main_keyword: {row.main_keyword}
cluster_keywords: {row.cluster_keywords}
search_intent: {row.search_intent}
page_type: {row.page_type}
article_type: {row.article_type}

{"GEO article: title must contain year 2026 and word «Лучшие» / «Best». 5-8 H2 sections — each a product or comparison angle." if row.is_geo else "SEO article: 5-7 H2 sections covering the topic comprehensively."}

Produce the article structure JSON."""
    ctx.keyword_analysis = _call_structured(client, SYSTEM_KEYWORD_ANALYZER, user, KeywordAnalysis)
    return ctx


# ─── Agent 2: LSI & Semantic Expansion ───────────────────────────────────────

SYSTEM_LSI_EXPANSION = f"""You are an expert in semantic SEO and topical authority for Russian digital marketing content.
Expand a keyword topic with LSI terms, entities, and user questions.

{CONTENT_RULES}

Simulate data from: top-10 Yandex/Google results, «Люди также спрашивают», related searches.

ЗАПРЕЩЕНО упоминать: Meta, Facebook, Instagram, Threads, WhatsApp.
Используй вместо них: VK Реклама, Яндекс Директ, Telegram Ads, MyTarget, ВКонтакте.

Return JSON:
{{
  "lsi_keywords": ["term1", ...],        // 20-30 LSI terms
  "entities": ["Entity1", ...],          // named entities & concepts
  "user_questions": ["Question 1?", ...], // 10-15 questions (good for FAQ)
  "related_topics": ["Topic 1", ...]     // 5-10 broader/narrower topics
}}"""


def agent_lsi_expansion(client: anthropic.Anthropic, ctx: PipelineContext) -> PipelineContext:
    ka = ctx.keyword_analysis
    user = f"""Topic: {ctx.row.main_keyword}
Article title: {ka.title}
H2 sections: {', '.join(ka.h2_sections)}
Primary keywords: {', '.join(ka.primary_keywords)}
Article type: {ctx.row.article_type}

Generate LSI keywords, entities, user questions and related topics."""
    ctx.lsi_data = _call_structured(client, SYSTEM_LSI_EXPANSION, user, LSIData)
    return ctx


# ─── Agent 3: Fact Collector ──────────────────────────────────────────────────

SYSTEM_FACT_COLLECTOR = f"""You are an expert research journalist for HotHeads Band agency.
Collect real, verifiable facts, statistics, and case studies for an SEO/GEO article.

{CONTENT_RULES}

Focus on Russian market data: ruble prices, Russian platforms, RU-market statistics.
Sources to simulate: industry reports, official docs, expert analyses, agency case studies.

Return JSON:
{{
  "facts": [{{"text": "fact", "source": "source name"}}],
  "statistics": [{{"value": "42%", "context": "explanation", "source": "Source"}}],
  "examples": [{{"title": "Case title", "description": "Brief description"}}],
  "sources": ["Source 1", ...]
}}

Include min 5 facts, 4 statistics, 3 examples. Prices in rubles where relevant."""


def agent_fact_collector(client: anthropic.Anthropic, ctx: PipelineContext) -> PipelineContext:
    ka = ctx.keyword_analysis
    lsi = ctx.lsi_data
    user = f"""Collect facts for article: {ctx.row.main_keyword}
Article type: {ctx.row.article_type}
Structure: {chr(10).join(f'- {s}' for s in ka.h2_sections)}
Key entities: {', '.join(lsi.entities[:10])}
User questions to answer: {chr(10).join(lsi.user_questions[:5])}

Provide facts, statistics, examples and sources. Russian market focus."""
    ctx.fact_data = _call_structured(client, SYSTEM_FACT_COLLECTOR, user, FactData)
    return ctx


# ─── Agent 4: Article Writer ──────────────────────────────────────────────────

SYSTEM_ARTICLE_WRITER_SEO = f"""You are a professional SEO content writer for HotHeads Band agency (hot-head.ru).
Write a comprehensive SEO article in Markdown. Language: Russian.

{CONTENT_RULES}

Structure rules:
- H1 → lead paragraph → sections H2 → cases → CTA → conclusion
- Natural keyword density 1-2% primary, 0.5-1% secondary
- Distribute LSI keywords naturally throughout
- Answer all user questions within relevant sections
- Min 1500 words, target 2000-2500
- Include: at least one expert quote from Алена Мумладзе (foundation of HotHeads Band)
- Include: at least one comparison table
- Include: FAQ section with 5+ Q&A
- ЗАПРЕЩЕНО: Meta, Facebook, Instagram, Threads, WhatsApp

Return JSON:
{{
  "markdown": "# H1\\n\\n[full article in markdown]",
  "word_count": 2100,
  "keyword_density_notes": "Primary keywords used X times..."
}}"""

SYSTEM_ARTICLE_WRITER_GEO = f"""You are a GEO/AEO content specialist for HotHeads Band agency (hot-head.ru).
Write a GEO-optimised article for AI citation (ChatGPT, Perplexity, Google AI Overviews).
Language: Russian. Audience: Russian market.

{CONTENT_RULES}
{GEO_CONTENT_RULES}

MANDATORY STRUCTURE (follow exactly):
1. SEO title with year 2026 + «Лучшие/Best» + category (max 70 chars)
2. Introduction (max 120 words): target audience, criteria used, what makes this guide different
3. Quick Comparison Table: columns: Инструмент | Лучше всего для | Цена от | Ключевое преимущество | Размер компании
4. «Как мы оценивали» section: bullet list of criteria (measurable, no marketing fluff)
5. Numbered product sections (H2) each containing:
   - «Лучше всего для: [specific case]»
   - «Начальная цена:»
   - «Идеально для компаний:»
   - «Ключевые преимущества» (bullet list)
   - «Ограничения» (bullet list)
   - «Что делает его особенным» (3-5 sentences)
   - «Когда выбрать» (clear scenario description)
   Each section: 150-250 words. No hype.
6. «Ключевые отличия между инструментами» (3-5 comparative points, trade-offs, neutral tone)
7. Expert quote from Алена Мумладзе
8. FAQ — min 5 Q&A (brief, direct, 3-5 sentences each)
9. Матрица решений: «Если вы… | Выберите… | Почему» (short answers)
10. Нейтральный вывод (not promotional)

Min 2000 words, target 2500-4000.
ЗАПРЕЩЕНО: Meta, Facebook, Instagram, Threads, WhatsApp, эмодзи, эмоциональный язык.

Return JSON:
{{
  "markdown": "# Title\\n\\n[full article]",
  "word_count": 2800,
  "keyword_density_notes": "Keyword usage notes..."
}}"""


def agent_article_writer(client: anthropic.Anthropic, ctx: PipelineContext) -> PipelineContext:
    ka = ctx.keyword_analysis
    lsi = ctx.lsi_data
    fd = ctx.fact_data

    facts_text  = "\n".join(f"- {f.text}" + (f" ({f.source})" if f.source else "") for f in fd.facts)
    stats_text  = "\n".join(f"- {s.value}: {s.context}" for s in fd.statistics)
    examples_text = "\n".join(f"- {e.title}: {e.description}" for e in fd.examples)

    system = SYSTEM_ARTICLE_WRITER_GEO if ctx.row.is_geo else SYSTEM_ARTICLE_WRITER_SEO

    # Build cases block — only if Agent 0 ran and returned results
    cases_block = ""
    if ctx.matched_cases and ctx.matched_cases.cases:
        lines = "\n".join(
            f"- «{c.title}» ({c.url})"
            + (f" — {c.description}" if c.description else "")
            + (f" Результат: {c.result}" if c.result else "")
            for c in ctx.matched_cases.cases
        )
        cases_block = (
            f"\n\nКЕЙСЫ АГЕНТСТВА (упомяни 1-2 органично в тексте как примеры из практики):\n{lines}"
        )

    user = f"""Write {"a GEO/AEO" if ctx.row.is_geo else "an SEO"} article.

H1: {ka.h1}
H2 sections: {', '.join(ka.h2_sections)}
Primary keywords (density 1-2%): {', '.join(ka.primary_keywords)}
Secondary keywords (density 0.5-1%): {', '.join(ka.secondary_keywords)}
LSI keywords: {', '.join(lsi.lsi_keywords[:20])}

User questions for FAQ:
{chr(10).join(f'- {q}' for q in lsi.user_questions)}

Facts:
{facts_text}

Statistics:
{stats_text}

Examples:
{examples_text}
{cases_block}
{"PRODUCTS TO COMPARE: " + ctx.row.cluster_keywords if ctx.row.is_geo else ""}

Expert quote: include a realistic quote from Алена Мумладзе (основательница HotHeads Band) relevant to the topic."""
    ctx.draft_article = _call_structured(client, system, user, DraftArticle)
    return ctx


# ─── Agent 5: SEO Editor ──────────────────────────────────────────────────────

SYSTEM_SEO_EDITOR_SEO = f"""You are a senior SEO editor for HotHeads Band agency (hot-head.ru).
Edit and enhance the draft article. Language: Russian.

{CONTENT_RULES}

Editing checklist:
1. Every H2/H3 MUST contain a search keyword — rewrite any that don't
2. Fix keyword over-optimisation (stuffing)
3. Improve readability: short paragraphs, varied sentence length
4. Verify keyword distribution across all sections
5. Add/improve FAQ block at the end (min 5 Q&A from user questions)
6. Add at least one comparison table if missing
7. Add bullet/numbered lists where appropriate
8. Add conclusion section if missing
9. Ensure compelling intro hook in first paragraph
10. Add expert quote from Алена Мумладзе if missing
11. ЗАПРЕЩЕНО: Meta, Facebook, Instagram, Threads, WhatsApp
12. Callout blocks only: .callout-warn (orange) and .callout-tip (grey)

Return JSON:
{{
  "markdown": "...improved full article with FAQ...",
  "readability_score": "Good / Needs improvement",
  "seo_notes": ["improvement 1", ...],
  "word_count": 2300
}}"""

SYSTEM_SEO_EDITOR_GEO = f"""You are a senior GEO/AEO editor for HotHeads Band agency (hot-head.ru).
Edit the GEO article for maximum AI citability. Language: Russian.

{CONTENT_RULES}
{GEO_CONTENT_RULES}

GEO editing checklist:
1. Every H2/H3 MUST contain a search keyword
2. Introduction ≤120 words — cut ruthlessly
3. Quick Comparison Table present with all 5 columns
4. Each product section has: «Лучше всего для», «Начальная цена», bullet Плюсы/Минусы, «Когда выбрать»
5. «Ключевые отличия» section with clear trade-offs
6. FAQ: min 5 Q&A, answers 3-5 sentences, direct and factual
7. Матрица решений: «Если вы… | Выберите… | Почему» table
8. Expert quote from Алена Мумладзе
9. Neutral conclusion (no promotional language)
10. No hype words: революционный, game-changing, лучший в своём классе
11. ЗАПРЕЩЕНО: Meta, Facebook, Instagram, Threads, WhatsApp

Return JSON:
{{
  "markdown": "...improved GEO article...",
  "readability_score": "Analytical / Structured",
  "seo_notes": ["improvement 1", ...],
  "word_count": 2800
}}"""


def agent_seo_editor(client: anthropic.Anthropic, ctx: PipelineContext) -> PipelineContext:
    ka = ctx.keyword_analysis
    lsi = ctx.lsi_data
    da = ctx.draft_article
    system = SYSTEM_SEO_EDITOR_GEO if ctx.row.is_geo else SYSTEM_SEO_EDITOR_SEO

    user = f"""Edit this {"GEO/AEO" if ctx.row.is_geo else "SEO"} article draft.

Primary keywords: {', '.join(ka.primary_keywords)}
User questions for FAQ: {chr(10).join(lsi.user_questions)}

DRAFT:
{da.markdown}"""
    ctx.edited_article = _call_structured(client, system, user, EditedArticle)
    return ctx


# ─── Agent 6: HTML Formatter ──────────────────────────────────────────────────
# CSS is NEVER generated by the model — it is injected verbatim from brand_config.py.
# Claude generates ONLY the inner HTML content (no <style> tag, no wrappers).

SYSTEM_HTML_FORMATTER = f"""You are a front-end developer for HotHeads Band agency (hot-head.ru).
Convert a Markdown article into the INNER HTML content for a Tilda Zero Block.

{CONTENT_RULES}

YOUR OUTPUT MUST BE ONLY the content that goes INSIDE:
  <div class="hu-article"><div class="container">  ← already provided
    [YOUR HTML HERE]
  </div></div>                                       ← already provided

DO NOT output:
  - <style> tags or any CSS
  - <html>, <head>, <body>, <meta>, <script>
  - The .hu-article or .container wrapper divs (already added automatically)

USE ONLY these CSS classes (all styles are pre-defined):
{AVAILABLE_CLASSES}

COMPONENT TEMPLATES:

Article header (REQUIRED):
<header class="article-header">
  <span class="article-tag">{{tag}}</span>
  <h1>{{h1 with primary keyword}}</h1>
  <div class="article-meta">
    <span>📅 {{Месяц YYYY}}</span>
    <span>⏱ {{X}} минут чтения</span>
    <span>✍ <a href="https://t.me/hotheads_band" target="_blank">Агентство HotHeads Band</a></span>
  </div>
</header>

Lead: <p class="lead">…</p>

TOC (REQUIRED — ids must match H2 id attributes):
<nav class="toc" aria-label="Содержание">
  <h2>Содержание</h2>
  <ol><li><a href="#section-slug">Section title</a></li></ol>
</nav>

H2 headings: <h2 id="section-slug">Title with keyword</h2>

Stats: <div class="stats-grid"><div class="stat-card"><span class="stat-number">X</span><span class="stat-label">label</span></div></div>

Callouts (ONLY these three — no other variants):
<div class="callout callout-warn"><strong>Title</strong>Text</div>
<div class="callout callout-tip"><strong>Title</strong>Text</div>
<div class="callout callout-info"><strong>Title</strong>Text</div>

Expert quote (REQUIRED — Алена Мумладзе):
<div class="expert-quote">
  <blockquote>Quote text.</blockquote>
  <cite><strong>Алена Мумладзе</strong> — основательница агентства HotHeads Band</cite>
</div>

Tables: <div class="table-wrap"><table><thead><tr><th>Col</th></tr></thead><tbody><tr><td>Data</td></tr></tbody></table></div>

FAQ (REQUIRED — min 5 items):
<div class="faq-item"><p class="faq-q">Question?</p><p class="faq-a">Answer.</p></div>

CTA (REQUIRED at the end — ALWAYS include BOTH buttons):
<div class="cta-block">
  <div class="cta-text">
    <p class="cta-title">Title</p>
    <p class="cta-body">Description.</p>
  </div>
  <div class="cta-buttons">
    <a href="https://t.me/hotheads_band" target="_blank" class="cta-btn">Написать в Telegram →</a>
    <a href="https://vk.me/hotheads_band" target="_blank" class="cta-btn">Написать ВКонтакте →</a>
  </div>
</div>

Footer: <footer class="article-footer">…</footer>

FORBIDDEN:
- <style>, inline style="" attributes, or any CSS
- Meta, Facebook, Instagram, Threads, WhatsApp mentions
- Any classes not listed above

Return JSON:
{{
  "html": "<header class=\\"article-header\\">...</header>\\n...\\n<div class=\\"cta-block\\">...</div>",
  "cms_notes": "Paste into Zero Block. Set height to Авто in Tilda settings."
}}"""


def agent_html_formatter(client: anthropic.Anthropic, ctx: PipelineContext) -> PipelineContext:
    import datetime
    month_ru = ["Январь","Февраль","Март","Апрель","Май","Июнь",
                "Июль","Август","Сентябрь","Октябрь","Ноябрь","Декабрь"]
    now = datetime.datetime.now()
    date_str = f"{month_ru[now.month - 1]} {now.year}"

    ka  = ctx.keyword_analysis
    ea  = ctx.edited_article
    tag = ka.article_tag

    user = f"""Convert to inner HTML content for Tilda Zero Block.

Article tag: {tag}
Date for article-meta: {date_str}
Primary keywords: {', '.join(ka.primary_keywords)}
Article type: {ctx.row.article_type}

MARKDOWN:
{ea.markdown}

Generate ONLY the inner HTML content. No <style>, no wrappers.
Use ONLY the pre-defined CSS classes. The <style> block with all CSS is added automatically."""

    # Ask Claude for inner content only
    inner = _call_structured(client, SYSTEM_HTML_FORMATTER, user, HTMLArticle)

    # Inject the canonical CSS wrapper — never trust Claude's CSS output
    full_html = HTML_OPEN + inner.html + HTML_CLOSE
    ctx.html_article = HTMLArticle(html=full_html, cms_notes=inner.cms_notes)
    return ctx


# ─── Agent 7: Internal Linking Analyzer ──────────────────────────────────────

SYSTEM_INTERNAL_LINKER = f"""You are an SEO internal linking specialist for HotHeads Band agency (hot-head.ru).
Analyse site pages and find the best internal linking opportunities for a new article.

{CONTENT_RULES}

Use semantic similarity between the new article and existing pages.
For each recommended link:
- url: page URL
- anchor: natural anchor text (varied, not exact title copy)
- section: which H2 of the new article to insert the link
- relevance_score: 0.0-1.0

Return JSON:
{{
  "internal_links": [
    {{"url": "/some/", "anchor": "natural anchor", "section": "H2 title", "relevance_score": 0.85}}
  ],
  "sitemap_pages_analyzed": 10
}}"""


def agent_internal_linking(
    client: anthropic.Anthropic,
    ctx: PipelineContext,
    sitemap_pages: Optional[list] = None,
) -> PipelineContext:
    ka = ctx.keyword_analysis

    # Build the effective page list
    effective_pages = list(sitemap_pages) if sitemap_pages else [
        {"url": "/blog/seo-basics/",              "title": "Основы SEO: полное руководство"},
        {"url": "/blog/content-marketing/",       "title": "Контент-маркетинг для бизнеса"},
        {"url": "/blog/yandex-direct/",           "title": "Яндекс Директ: настройка и оптимизация"},
        {"url": "/blog/landing-page-conversion/", "title": "Лендинг: как повысить конверсию"},
        {"url": "/blog/keyword-research/",        "title": "Сбор семантики: инструменты и методы"},
        {"url": "/blog/technical-seo/",           "title": "Технический SEO-аудит сайта"},
        {"url": "/blog/backlinks/",               "title": "Ссылочная масса: как строить ссылки"},
        {"url": "/blog/ai-tools-marketing/",      "title": "ИИ-инструменты для маркетолога"},
        {"url": "/blog/telegram-marketing/",      "title": "Маркетинг в Telegram: каналы и боты"},
        {"url": "/blog/analytics-setup/",         "title": "Настройка аналитики: GA4 и Яндекс Метрика"},
        {"url": "/keisi/",                        "title": "Кейсы агентства HotHeads Band"},
    ]

    # Prepend matched case studies (Agent 0 output) as priority link targets
    cases_hint = ""
    if ctx.matched_cases and ctx.matched_cases.cases:
        for mc in ctx.matched_cases.cases:
            # Avoid duplicates if the case is already in the sitemap
            if not any(p["url"] == mc.url for p in effective_pages):
                effective_pages.insert(0, {"url": mc.url, "title": mc.title})
        anchors = "\n".join(
            f"  {mc.url} → suggested anchor: «{mc.suggested_anchor}»"
            for mc in ctx.matched_cases.cases
        )
        cases_hint = f"\nPRIORITY CASE STUDIES (prefer linking to these, use the suggested anchors):\n{anchors}\n"

    pages_text = "\n".join(f"- URL: {p['url']} | Title: {p['title']}" for p in effective_pages)

    user = f"""New article: {ctx.row.main_keyword}
Article H1: {ka.h1}
H2 sections: {', '.join(ka.h2_sections)}
{cases_hint}
Site pages:
{pages_text}

Find 4-8 most relevant internal links. Case study pages are high-priority — linking to them demonstrates agency expertise."""
    ctx.link_data = _call_structured(client, SYSTEM_INTERNAL_LINKER, user, LinkData)
    ctx.link_data.sitemap_pages_analyzed = len(effective_pages)
    return ctx


# ─── Agent 8: Link Inserter ───────────────────────────────────────────────────

SYSTEM_LINK_INSERTER = f"""You are an HTML editor for HotHeads Band agency (hot-head.ru).
Insert internal links into the HTML article at natural positions.

{CONTENT_RULES}

Rules:
- Insert links within paragraph text, NOT as standalone lines
- Anchor text must appear naturally in the sentence (rewrite slightly if needed)
- Each link must appear exactly once
- Do NOT change any other content — only insert the <a href> tags
- Preserve all CSS, brand colours, CTA block, expert quote unchanged

Return JSON:
{{
  "html": "...full HTML with links inserted...",
  "links_inserted": 5
}}"""


def agent_link_inserter(client: anthropic.Anthropic, ctx: PipelineContext) -> PipelineContext:
    links_text = "\n".join(
        f"- URL: {lnk.url} | Anchor: {lnk.anchor} | Section: {lnk.section}"
        for lnk in ctx.link_data.internal_links
    )
    user = f"""Insert these internal links naturally into the HTML article:

LINKS:
{links_text}

HTML:
{ctx.html_article.html}"""
    ctx.linked_html = _call_structured(client, SYSTEM_LINK_INSERTER, user, LinkedHTMLArticle)
    return ctx


# ─── Agent 9: Final QA ────────────────────────────────────────────────────────
# The system prompt is built dynamically inside the function so it can
# adapt the checklist to article_type (SEO vs GEO) without module-level hacks.

_QA_SYSTEM_BASE = f"""You are the senior QA editor for HotHeads Band agency (hot-head.ru).
Perform a quality check on the final article before publication.

{CONTENT_RULES}

If minor HTML issues are found — fix them in final_html.
If critical content is missing (FAQ, CTA, expert quote) — add it.

Return JSON:
{{
  "checklist": [
    {{"check": "criterion description", "passed": true, "note": ""}}
  ],
  "overall_passed": true,
  "issues": [],
  "final_html": "...publication-ready HTML...",
  "summary": "One-paragraph QA summary."
}}"""


def _build_qa_system(is_geo: bool) -> str:
    geo_check = (
        "5. GEO article has: FAQ (min 5 Q&A) + Quick Comparison table + Decision Matrix («Если вы… | Выберите… | Почему»)"
        if is_geo else
        "5. Article has: FAQ (min 5 Q&A) + at least one comparison table"
    )
    checklist = f"""HOTHEAD BAND QA CHECKLIST (9 criteria — all must pass before publishing):
1. All H2/H3 contain a search keyword — no generic headings like «Введение» or «Заключение»
2. TOC anchor IDs match the actual H2 id attributes (href="#id" == <h2 id="id">)
3. Callout blocks are only .callout-warn (orange) or .callout-tip/.callout-info (grey/light) — no purple or teal
4. No mentions of Meta, Facebook, Instagram, Threads, WhatsApp anywhere in the text
{geo_check}
6. An expert quote from Алена Мумладзе is present inside <div class="expert-quote">
7. CTA block has TWO buttons: https://t.me/hotheads_band AND https://vk.me/hotheads_band, both inside class="cta-btn"
8. Date in .article-meta contains both a month name AND year (e.g. «Март 2026»), not just the year
9. Internal links (<a href="...">) are present in paragraph text (not standalone lines)"""
    return _QA_SYSTEM_BASE + "\n\n" + checklist


def agent_final_qa(client: anthropic.Anthropic, ctx: PipelineContext) -> PipelineContext:
    ka     = ctx.keyword_analysis
    system = _build_qa_system(ctx.row.is_geo)

    # Prefer linked HTML (Agent 8), fall back to raw HTML (Agent 6)
    if ctx.linked_html:
        html_to_check   = ctx.linked_html.html
        links_inserted  = ctx.linked_html.links_inserted
    elif ctx.html_article:
        html_to_check   = ctx.html_article.html
        links_inserted  = 0
    else:
        html_to_check   = "(no HTML available)"
        links_inserted  = 0

    user   = f"""Run the 9-point HotHeads Band QA checklist on this article.

Topic: {ctx.row.main_keyword}
Article type: {ctx.row.article_type}
Primary keywords: {', '.join(ka.primary_keywords)}
Internal links inserted: {links_inserted}

HTML:
{html_to_check}"""
    ctx.qa_report = _call_structured(client, system, user, QAReport)
    return ctx
