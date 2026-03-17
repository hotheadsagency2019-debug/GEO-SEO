"""
Google Sheets loader for HotHeads Band case studies.

Читает публичный Google Sheet (доступ «Все, у кого есть ссылка — просматривать»).
Никаких credentials не нужно.

Колонки Google Sheet:
  url         — /keisi/yandex-direct-ecom/
  title       — Заголовок кейса
  description — 2-3 предложения о кейсе
  industry    — e-commerce / недвижимость / B2B SaaS ...
  services    — Яндекс Директ / SEO / Telegram Ads ...
  result      — Ключевой результат / метрика
  keywords    — Теги через запятую

Настройка:
  1. Файл → Настройки доступа → «Все, у кого есть ссылка» → Просматривать
  2. Скопировать ID таблицы из URL (между /d/ и /edit)
  3. Передать через --cases-sheet или CASES_SHEET_ID в .env
"""
from __future__ import annotations

import re
from typing import List

import pandas as pd

from .models import CaseStudy


def _to_csv_export_url(sheet_id_or_url: str) -> str:
    """Принимает ID листа или любую ссылку на Google Sheets, возвращает CSV export URL."""
    # Извлекаем ID если передана полная ссылка
    m = re.search(r"spreadsheets/d/([^/]+)", sheet_id_or_url)
    sheet_id = m.group(1) if m else sheet_id_or_url.strip()
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"


def load_cases(sheet_id_or_url: str) -> List[CaseStudy]:
    """
    Загружает кейсы из публичного Google Sheet.

    Args:
        sheet_id_or_url: ID таблицы или полная ссылка на Google Sheets.

    Returns:
        Список CaseStudy (строки без url или title пропускаются).
    """
    url = _to_csv_export_url(sheet_id_or_url)
    df = pd.read_csv(url, dtype=str).fillna("")

    cases: List[CaseStudy] = []
    for _, row in df.iterrows():
        url_val   = str(row.get("url",   "")).strip()
        title_val = str(row.get("title", "")).strip()
        if not url_val or not title_val:
            continue
        cases.append(CaseStudy(
            url=url_val,
            title=title_val,
            description=str(row.get("description", "")),
            industry=str(row.get("industry",    "")),
            services=str(row.get("services",    "")),
            result=str(row.get("result",      "")),
            keywords=str(row.get("keywords",    "")),
        ))
    return cases
