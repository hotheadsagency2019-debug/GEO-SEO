#!/usr/bin/env python3
"""
SEO Content Pipeline — CLI entry point.

Usage examples:
  # Process all rows in a CSV
  python main.py run --csv keywords.csv

  # Process a single keyword row inline
  python main.py single \
      --keyword "нейросети для контекстной рекламы" \
      --cluster "AI для Яндекс Директ, ChatGPT для рекламы" \
      --intent "информационный" \
      --page-type "статья"

  # Provide a custom sitemap JSON file
  python main.py run --csv keywords.csv --sitemap sitemap_pages.json
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd
import typer
from dotenv import load_dotenv
from rich.console import Console

from seo_pipeline import KeywordRow, run_pipeline

load_dotenv()
app = typer.Typer(help="SEO Content Pipeline powered by Claude claude-opus-4-6")
console = Console()


def _check_api_key() -> None:
    if not os.getenv("ANTHROPIC_API_KEY"):
        console.print(
            "[bold red]Error:[/bold red] ANTHROPIC_API_KEY environment variable is not set.\n"
            "Set it in your shell or in a .env file."
        )
        raise typer.Exit(1)


def _load_sitemap(path: str | None) -> list | None:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        console.print(f"[yellow]Warning:[/yellow] sitemap file {path} not found, using demo pages.")
        return None
    with p.open(encoding="utf-8") as f:
        return json.load(f)


@app.command("run")
def run_csv(
    csv_path: str = typer.Option(..., "--csv", help="Path to CSV file with keyword rows"),
    output_dir: str = typer.Option("output", "--output", help="Output directory"),
    sitemap: str = typer.Option(None, "--sitemap", help="Path to sitemap JSON file"),
    row_index: int = typer.Option(None, "--row", help="Process only this row index (0-based)"),
):
    """Process all keyword rows from a CSV file."""
    _check_api_key()
    p = Path(csv_path)
    if not p.exists():
        console.print(f"[red]CSV file not found: {csv_path}[/red]")
        raise typer.Exit(1)

    df = pd.read_csv(p)
    required_cols = {"main_keyword", "cluster_keywords", "search_intent", "page_type"}
    missing = required_cols - set(df.columns)
    if missing:
        console.print(f"[red]Missing CSV columns: {missing}[/red]")
        raise typer.Exit(1)

    sitemap_pages = _load_sitemap(sitemap)
    out = Path(output_dir)

    rows = [df.iloc[row_index]] if row_index is not None else [df.iloc[i] for i in range(len(df))]

    for _, series in enumerate(rows):
        row = KeywordRow(
            main_keyword=str(series["main_keyword"]),
            cluster_keywords=str(series["cluster_keywords"]),
            search_intent=str(series["search_intent"]),
            page_type=str(series["page_type"]),
            article_type=str(series["article_type"]) if "article_type" in series.index else "seo",
        )
        try:
            run_pipeline(row, out, sitemap_pages=sitemap_pages)
        except Exception as exc:
            console.print(f"[red]Pipeline failed for '{row.main_keyword}': {exc}[/red]")
            continue

    console.print(f"\n[bold green]All done! Artefacts saved to: {out.resolve()}[/bold green]")


@app.command("single")
def run_single(
    keyword: str = typer.Option(..., "--keyword", "-k", help="Main keyword"),
    cluster: str = typer.Option("", "--cluster", "-c", help="Comma-separated cluster keywords"),
    intent: str = typer.Option("информационный", "--intent", "-i", help="Search intent"),
    page_type: str = typer.Option("статья", "--page-type", "-p", help="Page type"),
    output_dir: str = typer.Option("output", "--output", help="Output directory"),
    sitemap: str = typer.Option(None, "--sitemap", help="Path to sitemap JSON file"),
):
    """Process a single keyword row provided inline."""
    _check_api_key()
    row = KeywordRow(
        main_keyword=keyword,
        cluster_keywords=cluster,
        search_intent=intent,
        page_type=page_type,
    )
    sitemap_pages = _load_sitemap(sitemap)
    out = Path(output_dir)
    run_pipeline(row, out, sitemap_pages=sitemap_pages)
    console.print(f"\n[bold green]Done! Artefacts saved to: {out.resolve()}[/bold green]")


if __name__ == "__main__":
    app()
