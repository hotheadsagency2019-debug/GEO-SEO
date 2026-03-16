"""
Google Sheets loader for HotHeads Band case studies.

Reads a private Google Sheet using a Service Account and returns
a list of CaseStudy objects for use in agent_cases_matcher.

Required Google Sheet columns:
  url         — /keisi/yandex-direct-ecom/
  title       — Case study headline
  description — 2-3 sentence summary
  industry    — e-commerce / недвижимость / B2B SaaS …
  services    — Яндекс Директ / SEO / Telegram Ads …
  result      — Key metric / outcome
  keywords    — Comma-separated topical tags

Setup:
  1. Create a Service Account in Google Cloud Console
  2. Download the JSON key file
  3. Share the Google Sheet with the service account email (Viewer access)
  4. Set GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json  (or --credentials CLI flag)
  5. Set CASES_SHEET_ID=<your sheet ID>  (or --cases-sheet CLI flag)
"""
from __future__ import annotations

import os
from typing import List, Optional

import gspread
from google.oauth2.service_account import Credentials

from .models import CaseStudy

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def _extract_sheet_id(sheet_id_or_url: str) -> str:
    """Accept a bare sheet ID or any Google Sheets URL, return just the ID."""
    if "spreadsheets/d/" in sheet_id_or_url:
        part = sheet_id_or_url.split("spreadsheets/d/")[1]
        return part.split("/")[0].split("?")[0]
    return sheet_id_or_url.strip()


def load_cases(
    sheet_id_or_url: str,
    credentials_path: Optional[str] = None,
) -> List[CaseStudy]:
    """
    Load all case studies from the first sheet of the Google Spreadsheet.

    Args:
        sheet_id_or_url: Sheet ID or full Google Sheets URL.
        credentials_path: Path to service account JSON key file.
                          Falls back to GOOGLE_APPLICATION_CREDENTIALS env var.

    Returns:
        List of CaseStudy objects (rows with empty url or title are skipped).
    """
    creds_path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        raise ValueError(
            "Google service account credentials not found.\n"
            "  Option A: set GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json\n"
            "  Option B: pass --credentials /path/to/key.json via CLI"
        )

    sheet_id = _extract_sheet_id(sheet_id_or_url)
    creds = Credentials.from_service_account_file(creds_path, scopes=_SCOPES)
    gc = gspread.authorize(creds)
    worksheet = gc.open_by_key(sheet_id).sheet1
    records = worksheet.get_all_records()

    cases: List[CaseStudy] = []
    for row in records:
        url   = str(row.get("url",   "")).strip()
        title = str(row.get("title", "")).strip()
        if not url or not title:
            continue
        cases.append(CaseStudy(
            url=url,
            title=title,
            description=str(row.get("description", "")),
            industry=str(row.get("industry", "")),
            services=str(row.get("services", "")),
            result=str(row.get("result", "")),
            keywords=str(row.get("keywords", "")),
        ))
    return cases
