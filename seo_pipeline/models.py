"""
Pydantic data models for each stage of the SEO content pipeline.
Every agent produces one of these models and passes it downstream.
"""
from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


# ─── Input ────────────────────────────────────────────────────────────────────

class KeywordRow(BaseModel):
    """One row from the input CSV / Google Sheets table."""
    main_keyword: str
    cluster_keywords: str          # comma-separated string from CSV
    search_intent: str             # информационный / коммерческий / навигационный
    page_type: str                 # статья / лендинг / категория etc.
    article_type: Literal["seo", "geo"] = "seo"
    # "seo" — стандартная SEO-статья для блога HotHeads Band
    # "geo" — GEO/AEO-статья (сравнения, рейтинги, best-of) для AI-цитирования

    @property
    def cluster_list(self) -> List[str]:
        return [k.strip() for k in self.cluster_keywords.split(",") if k.strip()]

    @property
    def is_geo(self) -> bool:
        return self.article_type == "geo"


# ─── Stage 1 · Keyword Analyzer ───────────────────────────────────────────────

class KeywordAnalysis(BaseModel):
    """Output of Agent 1: article structure + keyword grouping."""
    title: str = Field(description="SEO title tag (up to 60 chars)")
    h1: str = Field(description="H1 heading of the article")
    h2_sections: List[str] = Field(description="List of H2 section titles")
    primary_keywords: List[str] = Field(description="Main target keywords (3-5)")
    secondary_keywords: List[str] = Field(description="Supporting keywords (5-15)")
    meta_description: str = Field(description="Meta description (up to 160 chars)")
    intent: str = Field(description="Refined search intent label")
    article_tag: str = Field(description="Short category tag for article header (e.g. Контекстная реклама)")


# ─── Stage 2 · LSI & Semantic Expansion ──────────────────────────────────────

class LSIData(BaseModel):
    """Output of Agent 2: semantic enrichment layer."""
    lsi_keywords: List[str] = Field(description="Latent semantic indexing keywords")
    entities: List[str] = Field(description="Named entities and topical concepts")
    user_questions: List[str] = Field(
        description="PAA-style questions users ask about this topic"
    )
    related_topics: List[str] = Field(description="Broader and narrower topic clusters")


# ─── Stage 3 · Fact Collector ─────────────────────────────────────────────────

class FactItem(BaseModel):
    text: str
    source: Optional[str] = None

class StatItem(BaseModel):
    value: str
    context: str
    source: Optional[str] = None

class ExampleItem(BaseModel):
    title: str
    description: str

class FactData(BaseModel):
    """Output of Agent 3: factual foundation for the article."""
    facts: List[FactItem] = Field(description="Verified facts about the topic")
    statistics: List[StatItem] = Field(description="Numerical data and statistics")
    examples: List[ExampleItem] = Field(description="Real-world cases and examples")
    sources: List[str] = Field(description="Reference source list")


# ─── Stage 4 · Article Writer ─────────────────────────────────────────────────

class DraftArticle(BaseModel):
    """Output of Agent 4: first-draft markdown article."""
    markdown: str = Field(description="Full article in Markdown with H1/H2/H3")
    word_count: int = Field(description="Approximate word count")
    keyword_density_notes: str = Field(
        description="Notes on keyword usage and density"
    )


# ─── Stage 5 · SEO Editor ─────────────────────────────────────────────────────

class EditedArticle(BaseModel):
    """Output of Agent 5: polished article with SEO enhancements."""
    markdown: str = Field(description="Edited Markdown with FAQ, tables, lists added")
    readability_score: str = Field(description="Subjective readability assessment")
    seo_notes: List[str] = Field(description="List of SEO improvements made")
    word_count: int


# ─── Stage 6 · HTML Formatter ─────────────────────────────────────────────────

class HTMLArticle(BaseModel):
    """Output of Agent 6: clean semantic HTML."""
    html: str = Field(description="Full article HTML without <html>/<body> wrappers")
    cms_notes: str = Field(description="Notes for pasting into CMS")


# ─── Stage 7 · Internal Linking Analyzer ─────────────────────────────────────

class InternalLink(BaseModel):
    url: str
    anchor: str
    section: str = Field(description="H2 section where link should be inserted")
    relevance_score: float = Field(ge=0.0, le=1.0)

class LinkData(BaseModel):
    """Output of Agent 7: recommended internal links."""
    internal_links: List[InternalLink]
    sitemap_pages_analyzed: int


# ─── Stage 8 · Link Inserter ──────────────────────────────────────────────────

class LinkedHTMLArticle(BaseModel):
    """Output of Agent 8: HTML with internal links injected."""
    html: str
    links_inserted: int


# ─── Stage 9 · Final QA ───────────────────────────────────────────────────────

class QAChecklistItem(BaseModel):
    check: str
    passed: bool
    note: str = ""

class QAReport(BaseModel):
    """Output of Agent 9: quality gate + final publishable article."""
    checklist: List[QAChecklistItem]
    overall_passed: bool
    issues: List[str] = Field(description="List of issues found, empty if none")
    final_html: str = Field(description="Final publication-ready HTML")
    summary: str = Field(description="One-paragraph QA summary")


# ─── Full Pipeline Context ────────────────────────────────────────────────────

class PipelineContext(BaseModel):
    """Accumulated state passed through the entire pipeline."""
    row: KeywordRow
    keyword_analysis: Optional[KeywordAnalysis] = None
    lsi_data: Optional[LSIData] = None
    fact_data: Optional[FactData] = None
    draft_article: Optional[DraftArticle] = None
    edited_article: Optional[EditedArticle] = None
    html_article: Optional[HTMLArticle] = None
    link_data: Optional[LinkData] = None
    linked_html: Optional[LinkedHTMLArticle] = None
    qa_report: Optional[QAReport] = None
