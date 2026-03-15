"""
SEO Content Pipeline Orchestrator.

Runs all 9 agents in sequence, passes the accumulated PipelineContext
from one agent to the next, and saves artefacts to disk.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Callable, List, Optional

import anthropic
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from .agents import (
    agent_article_writer,
    agent_fact_collector,
    agent_final_qa,
    agent_html_formatter,
    agent_internal_linking,
    agent_keyword_analyzer,
    agent_link_inserter,
    agent_lsi_expansion,
    agent_seo_editor,
)
from .models import KeywordRow, PipelineContext

console = Console()

# ─── Pipeline step registry ───────────────────────────────────────────────────

PIPELINE_STEPS: List[tuple[str, str, Callable]] = [
    ("1", "Keyword Analyzer",            agent_keyword_analyzer),
    ("2", "LSI & Semantic Expansion",    agent_lsi_expansion),
    ("3", "Fact Collector",              agent_fact_collector),
    ("4", "Article Writer",              agent_article_writer),
    ("5", "SEO Editor",                  agent_seo_editor),
    ("6", "HTML Formatter",              agent_html_formatter),
    ("7", "Internal Linking Analyzer",   agent_internal_linking),
    ("8", "Link Inserter",               agent_link_inserter),
    ("9", "Final QA",                    agent_final_qa),
]


# ─── Single-row runner ────────────────────────────────────────────────────────

def run_pipeline(
    row: KeywordRow,
    output_dir: Path,
    sitemap_pages: Optional[list] = None,
    verbose: bool = False,
) -> PipelineContext:
    """
    Run the full 9-agent pipeline for a single keyword row.
    Saves intermediate JSON and final HTML artefacts to output_dir.
    """
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    ctx = PipelineContext(row=row)

    # Slugify keyword for file names
    slug = row.main_keyword.lower().replace(" ", "-")[:50]
    row_dir = output_dir / slug
    row_dir.mkdir(parents=True, exist_ok=True)

    console.rule(f"[bold cyan]Pipeline: {row.main_keyword}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        for step_num, step_name, step_fn in PIPELINE_STEPS:
            task = progress.add_task(
                f"  [yellow]Agent {step_num}[/yellow]: {step_name}", total=None
            )
            start = time.time()
            try:
                if step_fn is agent_internal_linking:
                    ctx = step_fn(client, ctx, sitemap_pages)
                else:
                    ctx = step_fn(client, ctx)
            except Exception as exc:
                progress.stop()
                console.print(f"[red]✗ Agent {step_num} ({step_name}) failed: {exc}[/red]")
                raise
            elapsed = time.time() - start
            progress.remove_task(task)
            console.print(
                f"  [green]✓[/green] Agent {step_num}: {step_name}  "
                f"[dim]({elapsed:.1f}s)[/dim]"
            )

            # Save per-step artefact
            _save_step_artefact(ctx, step_num, step_name, row_dir)

    # Save final output
    _save_final_output(ctx, row_dir, slug)
    _print_qa_summary(ctx)

    return ctx


# ─── Helpers ──────────────────────────────────────────────────────────────────

_STEP_FIELD_MAP = {
    "1": "keyword_analysis",
    "2": "lsi_data",
    "3": "fact_data",
    "4": "draft_article",
    "5": "edited_article",
    "6": "html_article",
    "7": "link_data",
    "8": "linked_html",
    "9": "qa_report",
}


def _save_step_artefact(ctx: PipelineContext, step_num: str, step_name: str, out_dir: Path) -> None:
    field = _STEP_FIELD_MAP.get(step_num)
    if not field:
        return
    data = getattr(ctx, field)
    if data is None:
        return
    fname = out_dir / f"step{step_num}_{field}.json"
    fname.write_text(data.model_dump_json(indent=2), encoding="utf-8")


def _save_final_output(ctx: PipelineContext, out_dir: Path, slug: str) -> None:
    if ctx.qa_report:
        html_path = out_dir / f"{slug}_final.html"
        html_path.write_text(ctx.qa_report.final_html, encoding="utf-8")
        console.print(f"\n[bold green]Final HTML →[/bold green] {html_path}")

    # Full context JSON for debugging / replay
    ctx_path = out_dir / "pipeline_context.json"
    ctx_path.write_text(ctx.model_dump_json(indent=2), encoding="utf-8")


def _print_qa_summary(ctx: PipelineContext) -> None:
    if not ctx.qa_report:
        return

    qa = ctx.qa_report
    table = Table(title="QA Checklist", show_lines=True)
    table.add_column("Check", style="cyan", no_wrap=False)
    table.add_column("Status", justify="center")
    table.add_column("Note")

    for item in qa.checklist:
        icon = "[green]✓[/green]" if item.passed else "[red]✗[/red]"
        table.add_row(item.check, icon, item.note or "")

    console.print(table)

    overall = "[bold green]PASSED[/bold green]" if qa.overall_passed else "[bold red]FAILED[/bold red]"
    console.print(f"\nOverall QA: {overall}")
    if qa.issues:
        for issue in qa.issues:
            console.print(f"  [red]• {issue}[/red]")
    console.print(f"\n[italic]{qa.summary}[/italic]\n")
