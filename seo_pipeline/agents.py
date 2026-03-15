"""
Nine specialized SEO agents.  Each agent:
  - receives a PipelineContext with all upstream results
  - calls Claude claude-opus-4-6 with adaptive thinking + streaming
  - returns a structured Pydantic model
  - updates the PipelineContext in place

All agents share one Anthropic client passed in at construction time.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional, Type, TypeVar

import anthropic
from pydantic import BaseModel

from .models import (
    DraftArticle,
    EditedArticle,
    ExampleItem,
    FactData,
    FactItem,
    HTMLArticle,
    InternalLink,
    KeywordAnalysis,
    KeywordRow,
    LinkData,
    LinkedHTMLArticle,
    LSIData,
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
    # strip markdown fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    raw = re.sub(r"\s*```$", "", raw.strip(), flags=re.MULTILINE)
    # find first { or [
    start = min(
        (raw.find("{") if raw.find("{") != -1 else len(raw)),
        (raw.find("[") if raw.find("[") != -1 else len(raw)),
    )
    raw = raw[start:]
    return json.loads(raw)


def _call_structured(
    client: anthropic.Anthropic,
    system: str,
    user: str,
    model_cls: Type[T],
) -> T:
    """
    Call Claude and parse the response as a Pydantic model.
    The system prompt instructs the model to reply with JSON only.
    """
    system_with_json = (
        system
        + "\n\nIMPORTANT: Your entire response MUST be valid JSON that matches "
        "the schema described. Do not add any text before or after the JSON object."
    )
    raw = _stream_call(client, system_with_json, user)
    data = _parse_json_response(raw)
    return model_cls.model_validate(data)


# ─── Agent 1: Keyword Analyzer ────────────────────────────────────────────────

SYSTEM_KEYWORD_ANALYZER = """You are a senior SEO strategist and content architect.
Your task is to analyse a keyword cluster and produce a complete article structure.

Given:
- main_keyword: the primary search term
- cluster_keywords: related terms
- search_intent: the type of search intent
- page_type: the type of page

Produce a JSON object with:
{
  "title": "SEO title (max 60 chars, includes main keyword)",
  "h1": "H1 heading (close to main keyword, compelling)",
  "h2_sections": ["Section 1", "Section 2", ...],  // 5-8 sections
  "primary_keywords": ["kw1", "kw2", ...],         // 3-5 keywords
  "secondary_keywords": ["kw1", ...],              // 5-15 keywords
  "meta_description": "Meta description (max 160 chars)",
  "intent": "refined intent label"
}"""


def agent_keyword_analyzer(client: anthropic.Anthropic, ctx: PipelineContext) -> PipelineContext:
    row = ctx.row
    user = f"""Keyword data:
main_keyword: {row.main_keyword}
cluster_keywords: {row.cluster_keywords}
search_intent: {row.search_intent}
page_type: {row.page_type}

Produce the article structure JSON."""
    ctx.keyword_analysis = _call_structured(client, SYSTEM_KEYWORD_ANALYZER, user, KeywordAnalysis)
    return ctx


# ─── Agent 2: LSI & Semantic Expansion ───────────────────────────────────────

SYSTEM_LSI_EXPANSION = """You are an expert in semantic SEO, NLP, and topical authority.
Your task is to expand a keyword topic with LSI terms, entities, and user questions.

Simulate what you would find in:
- Top-10 Google/Yandex results
- "People Also Ask" boxes
- Related searches
- N-gram analysis of top pages

Produce a JSON object with:
{
  "lsi_keywords": ["term1", "term2", ...],         // 20-30 LSI terms
  "entities": ["Entity1", "Entity2", ...],         // named entities & concepts
  "user_questions": ["Question 1?", ...],          // 10-15 PAA questions
  "related_topics": ["Topic 1", ...]               // 5-10 broader/narrower topics
}"""


def agent_lsi_expansion(client: anthropic.Anthropic, ctx: PipelineContext) -> PipelineContext:
    ka = ctx.keyword_analysis
    user = f"""Topic to expand:
main_keyword: {ctx.row.main_keyword}
article_title: {ka.title}
h2_sections: {', '.join(ka.h2_sections)}
primary_keywords: {', '.join(ka.primary_keywords)}

Generate LSI, entities, user questions and related topics."""
    ctx.lsi_data = _call_structured(client, SYSTEM_LSI_EXPANSION, user, LSIData)
    return ctx


# ─── Agent 3: Fact Collector ──────────────────────────────────────────────────

SYSTEM_FACT_COLLECTOR = """You are an expert research journalist and fact-checker.
Your task is to collect real, verifiable facts, statistics, and case studies for an SEO article.

Sources to simulate: research papers, industry reports, official docs, expert analyses.

Produce a JSON object with:
{
  "facts": [
    {"text": "fact text", "source": "Source name or URL"}
  ],
  "statistics": [
    {"value": "42%", "context": "explanation", "source": "Source"}
  ],
  "examples": [
    {"title": "Example title", "description": "Brief description"}
  ],
  "sources": ["Source 1", "Source 2", ...]
}

Include at least 5 facts, 4 statistics, 3 examples."""


def agent_fact_collector(client: anthropic.Anthropic, ctx: PipelineContext) -> PipelineContext:
    ka = ctx.keyword_analysis
    lsi = ctx.lsi_data
    user = f"""Collect facts for an article about: {ctx.row.main_keyword}

Article structure:
{chr(10).join(f'- {s}' for s in ka.h2_sections)}

Key entities to cover: {', '.join(lsi.entities[:10])}
User questions to answer: {chr(10).join(lsi.user_questions[:5])}

Provide facts, statistics, examples and sources."""
    ctx.fact_data = _call_structured(client, SYSTEM_FACT_COLLECTOR, user, FactData)
    return ctx


# ─── Agent 4: Article Writer ──────────────────────────────────────────────────

SYSTEM_ARTICLE_WRITER = """You are a professional SEO content writer.
Write a comprehensive, engaging, factually accurate article in Markdown.

Rules:
- Use H1, H2, H3 headings as provided
- Natural keyword density 1-2% for primary, 0.5-1% for secondary
- Distribute LSI keywords naturally throughout the text
- Answer all user questions within relevant sections
- Minimum 1500 words, target 2000-2500
- Natural reading flow, no keyword stuffing
- Use facts and statistics provided

Produce a JSON object:
{
  "markdown": "# H1\\n\\nIntro...\\n\\n## H2\\n\\nSection text...",
  "word_count": 2100,
  "keyword_density_notes": "Primary keywords used X times each..."
}"""


def agent_article_writer(client: anthropic.Anthropic, ctx: PipelineContext) -> PipelineContext:
    ka = ctx.keyword_analysis
    lsi = ctx.lsi_data
    fd = ctx.fact_data

    facts_text = "\n".join(f"- {f.text}" + (f" ({f.source})" if f.source else "") for f in fd.facts)
    stats_text = "\n".join(f"- {s.value}: {s.context}" for s in fd.statistics)
    examples_text = "\n".join(f"- {e.title}: {e.description}" for e in fd.examples)

    user = f"""Write an article with this structure:

H1: {ka.h1}
H2 sections: {', '.join(ka.h2_sections)}

PRIMARY KEYWORDS (density 1-2%): {', '.join(ka.primary_keywords)}
SECONDARY KEYWORDS (density 0.5-1%): {', '.join(ka.secondary_keywords)}
LSI KEYWORDS (weave naturally): {', '.join(lsi.lsi_keywords[:20])}

USER QUESTIONS TO ANSWER:
{chr(10).join(f'- {q}' for q in lsi.user_questions)}

FACTS TO USE:
{facts_text}

STATISTICS TO USE:
{stats_text}

EXAMPLES TO USE:
{examples_text}

Write the full article markdown, then return JSON."""
    ctx.draft_article = _call_structured(client, SYSTEM_ARTICLE_WRITER, user, DraftArticle)
    return ctx


# ─── Agent 5: SEO Editor ──────────────────────────────────────────────────────

SYSTEM_SEO_EDITOR = """You are a senior SEO editor. Your task is to improve a draft article:

1. Check and fix keyword over-optimisation (keyword stuffing)
2. Improve readability: shorter paragraphs, varied sentence length
3. Verify keyword distribution is even across sections
4. Add a FAQ block at the end (5-7 Q&A pairs from user questions)
5. Add at least one comparison table where relevant
6. Add bullet/numbered lists where appropriate
7. Add a conclusion section
8. Ensure the article starts with a compelling intro hook

Produce a JSON object:
{
  "markdown": "...improved full article with FAQ...",
  "readability_score": "Good / Needs improvement",
  "seo_notes": ["improvement 1", "improvement 2", ...],
  "word_count": 2300
}"""


def agent_seo_editor(client: anthropic.Anthropic, ctx: PipelineContext) -> PipelineContext:
    ka = ctx.keyword_analysis
    lsi = ctx.lsi_data
    da = ctx.draft_article

    user = f"""Edit and improve this article draft.

Primary keywords: {', '.join(ka.primary_keywords)}
User questions for FAQ: {chr(10).join(lsi.user_questions)}

DRAFT ARTICLE:
{da.markdown}

Improve readability, SEO, add FAQ and enhancements."""
    ctx.edited_article = _call_structured(client, SYSTEM_SEO_EDITOR, user, EditedArticle)
    return ctx


# ─── Agent 6: HTML Formatter ──────────────────────────────────────────────────

SYSTEM_HTML_FORMATTER = """You are a front-end developer specialising in CMS content.
Convert the Markdown article to clean, semantic HTML.

Rules:
- Use proper heading tags: <h1>, <h2>, <h3>
- Paragraphs in <p> tags
- Lists as <ul><li> or <ol><li>
- Tables as proper <table><thead><tbody>
- FAQ section: use <div class="faq-item"><h3 class="faq-question">, <p class="faq-answer">
- Add id attributes to H2 headings (slugified title)
- Do NOT include <html>, <head>, <body> tags
- Wrap the whole article in <article class="seo-article">

Produce a JSON object:
{
  "html": "<article class=\\"seo-article\\">...</article>",
  "cms_notes": "Paste into the content area of your CMS..."
}"""


def agent_html_formatter(client: anthropic.Anthropic, ctx: PipelineContext) -> PipelineContext:
    ea = ctx.edited_article
    user = f"""Convert this Markdown article to semantic HTML:

{ea.markdown}

Follow the HTML formatting rules exactly."""
    ctx.html_article = _call_structured(client, SYSTEM_HTML_FORMATTER, user, HTMLArticle)
    return ctx


# ─── Agent 7: Internal Linking Analyzer ──────────────────────────────────────

SYSTEM_INTERNAL_LINKER = """You are an SEO internal linking specialist.
You analyse a site's pages and find the best internal linking opportunities for a new article.

Given a list of site pages (URL + title) and the new article's topic, use semantic similarity
to identify 4-8 most relevant pages for internal links.

For each link provide:
- url: page URL
- anchor: natural anchor text (NOT the exact title – vary it)
- section: which H2 section of the new article to insert the link
- relevance_score: 0.0-1.0

Produce a JSON object:
{
  "internal_links": [
    {
      "url": "/some-page/",
      "anchor": "natural anchor text",
      "section": "H2 section title",
      "relevance_score": 0.85
    }
  ],
  "sitemap_pages_analyzed": 42
}"""


def agent_internal_linking(
    client: anthropic.Anthropic,
    ctx: PipelineContext,
    sitemap_pages: Optional[list] = None,
) -> PipelineContext:
    """
    sitemap_pages: list of dicts with 'url' and 'title'.
    If not provided, a placeholder site map is used for demo purposes.
    """
    ka = ctx.keyword_analysis
    ea = ctx.edited_article

    if not sitemap_pages:
        # Demo sitemap – replace with real sitemap.xml parser in production
        sitemap_pages = [
            {"url": "/blog/seo-basics/", "title": "Основы SEO: полное руководство"},
            {"url": "/blog/content-marketing/", "title": "Контент-маркетинг для бизнеса"},
            {"url": "/blog/google-ads-guide/", "title": "Google Ads: пошаговый гайд"},
            {"url": "/blog/yandex-direct/", "title": "Яндекс Директ: настройка и оптимизация"},
            {"url": "/blog/landing-page-conversion/", "title": "Лендинг: как повысить конверсию"},
            {"url": "/blog/keyword-research/", "title": "Сбор семантики: инструменты и методы"},
            {"url": "/blog/technical-seo/", "title": "Технический SEO-аудит сайта"},
            {"url": "/blog/backlinks/", "title": "Ссылочная масса: как строить ссылки"},
            {"url": "/blog/ai-tools-marketing/", "title": "ИИ-инструменты для маркетолога"},
            {"url": "/blog/social-media-ads/", "title": "Реклама в соцсетях: Facebook и ВКонтакте"},
        ]

    pages_text = "\n".join(f"- URL: {p['url']} | Title: {p['title']}" for p in sitemap_pages)

    user = f"""New article topic: {ctx.row.main_keyword}
Article title: {ka.h1}
Article H2 sections: {', '.join(ka.h2_sections)}

Site pages to analyse for internal links:
{pages_text}

Find 4-8 most relevant internal linking opportunities."""
    ctx.link_data = _call_structured(client, SYSTEM_INTERNAL_LINKER, user, LinkData)
    # Fill in the analysed count
    ctx.link_data.sitemap_pages_analyzed = len(sitemap_pages)
    return ctx


# ─── Agent 8: Link Inserter ───────────────────────────────────────────────────

SYSTEM_LINK_INSERTER = """You are an HTML editor specialising in natural internal linking.
Insert internal links into an HTML article at the most natural positions.

Rules:
- Insert links within paragraph text, not as standalone lines
- The anchor text must appear naturally in the existing sentences
  (rewrite surrounding text slightly if needed)
- Each link must appear exactly once
- Do not change any other content
- Return only the modified HTML

Produce a JSON object:
{
  "html": "...full HTML with links inserted...",
  "links_inserted": 5
}"""


def agent_link_inserter(client: anthropic.Anthropic, ctx: PipelineContext) -> PipelineContext:
    html_art = ctx.html_article
    ld = ctx.link_data

    links_text = "\n".join(
        f"- URL: {lnk.url} | Anchor: {lnk.anchor} | Section: {lnk.section}"
        for lnk in ld.internal_links
    )

    user = f"""Insert these internal links into the HTML article:

LINKS TO INSERT:
{links_text}

HTML ARTICLE:
{html_art.html}

Insert each link naturally into the corresponding section."""
    ctx.linked_html = _call_structured(client, SYSTEM_LINK_INSERTER, user, LinkedHTMLArticle)
    return ctx


# ─── Agent 9: Final QA ────────────────────────────────────────────────────────

SYSTEM_FINAL_QA = """You are a senior SEO quality assurance specialist.
Perform a comprehensive check of the final article before publication.

Checklist to verify:
1. H1 tag present and contains primary keyword
2. At least 3 H2 tags present
3. FAQ section present (min 3 Q&A pairs)
4. Internal links present (min 2)
5. Meta description not empty (check article intro as proxy)
6. No duplicate H2 headings
7. Word count ≥ 1500
8. Primary keywords appear in first paragraph
9. Article ends with a conclusion or call to action
10. No broken HTML (no unclosed tags in visible content)

Produce a JSON object:
{
  "checklist": [
    {"check": "H1 tag present with primary keyword", "passed": true, "note": ""},
    ...
  ],
  "overall_passed": true,
  "issues": [],
  "final_html": "...the article HTML (unchanged if passed, or fixed if minor issues)...",
  "summary": "One paragraph QA summary..."
}"""


def agent_final_qa(client: anthropic.Anthropic, ctx: PipelineContext) -> PipelineContext:
    ka = ctx.keyword_analysis
    linked = ctx.linked_html

    user = f"""Perform QA on this article.

Primary keywords: {', '.join(ka.primary_keywords)}
Expected internal links count: {ctx.link_data.links_inserted if ctx.linked_html else 0}

ARTICLE HTML:
{linked.html}

Run all checklist items and return the QA report JSON."""
    ctx.qa_report = _call_structured(client, SYSTEM_FINAL_QA, user, QAReport)
    return ctx
