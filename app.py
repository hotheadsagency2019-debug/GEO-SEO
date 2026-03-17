"""
GEO-SEO Pipeline · Streamlit Web App
Обложка над pipeline для запуска без командной строки.
"""
from __future__ import annotations

import io
import json
import os
import zipfile
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ─── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="GEO-SEO Pipeline · HotHeads Band",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Helpers ──────────────────────────────────────────────────────────────────

AGENT_LABELS = {
    "0": "Agent 0 · Cases Matcher",
    "1": "Agent 1 · Keyword Analyzer",
    "2": "Agent 2 · LSI Expansion",
    "3": "Agent 3 · Fact Collector",
    "4": "Agent 4 · Article Writer",
    "5": "Agent 5 · SEO Editor",
    "6": "Agent 6 · HTML Formatter",
    "7": "Agent 7 · Internal Linking",
    "8": "Agent 8 · Link Inserter",
    "9": "Agent 9 · Final QA",
}

STATUS_ICON = {
    "running": "⏳",
    "done":    "✅",
    "skipped": "⏭",
    "error":   "❌",
}


def zip_folder(folder: Path) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(folder.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(folder.parent))
    return buf.getvalue()


def keyword_to_slug(keyword: str) -> str:
    return keyword.lower().replace(" ", "-")[:50]


def get_final_html(output_dir: str, keyword: str) -> Optional[str]:
    slug = keyword_to_slug(keyword)
    folder = Path(output_dir) / slug
    html_files = list(folder.glob("*_final.html"))
    if html_files:
        return html_files[0].read_text(encoding="utf-8"), html_files[0].name
    return None, None


def run_single_pipeline(
    row_data: dict,
    output_dir: str,
    sitemap_pages: Optional[list],
    cases_sheet: str,
    api_key: str,
    progress_placeholder,
):
    """Execute pipeline and stream agent progress into a Streamlit placeholder."""
    os.environ["ANTHROPIC_API_KEY"] = api_key

    from seo_pipeline.cases_loader import load_cases
    from seo_pipeline.models import KeywordRow
    from seo_pipeline.pipeline import run_pipeline

    row = KeywordRow(**row_data)

    all_cases = None
    if cases_sheet.strip():
        try:
            all_cases = load_cases(cases_sheet.strip())
        except Exception:
            pass

    # Build progress tracker in session state
    agent_statuses: dict[str, str] = {}

    def on_progress(step_num: str, step_name: str, status: str):
        agent_statuses[step_num] = status
        lines = []
        for num, label in AGENT_LABELS.items():
            st = agent_statuses.get(num, "pending")
            if st == "pending":
                lines.append(f"○ {label}")
            else:
                lines.append(f"{STATUS_ICON.get(st, '?')} {label}")
        progress_placeholder.markdown("\n\n".join(lines))

    ctx = run_pipeline(
        row=row,
        output_dir=Path(output_dir),
        sitemap_pages=sitemap_pages,
        all_cases=all_cases,
        progress_callback=on_progress,
    )
    return ctx


def render_qa(ctx) -> None:
    """Display QA checklist table + issues + summary."""
    if ctx.qa_report is None:
        st.warning("QA-отчёт не сформирован")
        return

    qa = ctx.qa_report

    if qa.overall_passed:
        st.success("✅ QA PASSED — статья готова к публикации")
    else:
        st.error("❌ QA FAILED — найдены проблемы")

    rows = []
    for item in qa.checklist:
        rows.append({
            "Проверка": item.check,
            "Статус": "✅" if item.passed else "❌",
            "Заметки": item.note or "",
        })
    if rows:
        st.dataframe(
            pd.DataFrame(rows),
            hide_index=True,
            use_container_width=True,
            column_config={
                "Статус": st.column_config.TextColumn(width="small"),
            },
        )

    if qa.issues:
        with st.expander(f"⚠️ Проблемы ({len(qa.issues)})", expanded=not qa.overall_passed):
            for issue in qa.issues:
                st.markdown(f"- {issue}")

    if qa.summary:
        st.info(qa.summary)


def render_downloads(ctx, output_dir: str) -> None:
    """Download buttons for HTML + ZIP artifacts."""
    keyword = ctx.row.main_keyword
    slug = keyword_to_slug(keyword)
    folder = Path(output_dir) / slug

    html_content, html_filename = get_final_html(output_dir, keyword)

    col1, col2 = st.columns(2)

    if html_content and html_filename:
        col1.download_button(
            label="⬇️ HTML статья",
            data=html_content,
            file_name=html_filename,
            mime="text/html",
            use_container_width=True,
            type="primary",
        )

    if folder.exists():
        zip_data = zip_folder(folder)
        col2.download_button(
            label="⬇️ Все артефакты (ZIP)",
            data=zip_data,
            file_name=f"{slug}_artifacts.zip",
            mime="application/zip",
            use_container_width=True,
        )

    if html_content:
        with st.expander("👁 Предпросмотр HTML", expanded=False):
            st.components.v1.html(html_content, height=820, scrolling=True)


# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ Настройки")

    api_key = st.text_input(
        "Anthropic API Key *",
        type="password",
        value=os.getenv("ANTHROPIC_API_KEY", ""),
        placeholder="sk-ant-api03-...",
        help="Обязателен для работы. Получить: console.anthropic.com",
    )

    if api_key and not api_key.startswith("sk-ant-"):
        st.warning("Ключ должен начинаться с `sk-ant-`")

    st.divider()

    cases_sheet = st.text_input(
        "Google Sheet ID (кейсы)",
        value="",
        placeholder="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms",
        help=(
            "ID публичной Google Таблицы с кейсами агентства.\n"
            "Таблица должна быть открыта по ссылке.\n"
            "Колонки: url, title, description, industry, services, result, keywords"
        ),
    )

    sitemap_upload = st.file_uploader(
        "Sitemap JSON (необязательно)",
        type=["json"],
        help='Массив объектов [{"url": "/page/", "title": "Заголовок"}] '
             'для подбора внутренних ссылок. Без файла используются демо-страницы.',
    )

    st.divider()

    output_dir = st.text_input(
        "Папка вывода",
        value="output",
        help="Относительный путь для сохранения HTML и артефактов",
    )

    st.divider()
    st.caption("GEO-SEO Pipeline · HotHeads Band")
    st.caption("Использует Claude Opus 4 · 9 AI-агентов")

# ─── Sitemap loading ──────────────────────────────────────────────────────────

sitemap_pages = None
if sitemap_upload is not None:
    try:
        sitemap_pages = json.load(sitemap_upload)
        st.sidebar.success(f"Sitemap загружен: {len(sitemap_pages)} страниц")
    except Exception as e:
        st.sidebar.error(f"Ошибка парсинга sitemap: {e}")

# ─── Header ───────────────────────────────────────────────────────────────────

st.title("🎯 GEO-SEO Content Pipeline")
st.caption(
    "Генерация SEO и GEO/AEO-статей через 9 специализированных AI-агентов · "
    "[HotHeads Band](https://hot-head.ru/)"
)

if not api_key:
    st.info("Введите Anthropic API Key в боковой панели, чтобы начать.", icon="🔑")

# ─── Tabs ─────────────────────────────────────────────────────────────────────

tab_single, tab_csv, tab_help = st.tabs(["📝 Одна статья", "📊 Пакет CSV", "❓ Справка"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 · Single keyword
# ══════════════════════════════════════════════════════════════════════════════

with tab_single:

    st.subheader("Параметры статьи")

    col_main, col_opts = st.columns([3, 1])

    with col_main:
        main_keyword = st.text_input(
            "Основной ключевой запрос *",
            placeholder="нейросети для контекстной рекламы",
            help="Главный поисковый запрос. По нему строится структура статьи.",
        )
        cluster_keywords = st.text_area(
            "Кластерные запросы (через запятую)",
            placeholder="AI для Яндекс Директ, ChatGPT для рекламы, автоматизация контекста",
            height=90,
            help="Похожие запросы из кластера. Включаются в H2, LSI и текст.",
        )

    with col_opts:
        search_intent = st.selectbox(
            "Интент *",
            ["информационный", "коммерческий", "навигационный"],
            help="Цель поиска пользователя",
        )
        page_type = st.selectbox(
            "Тип страницы *",
            ["статья", "лендинг", "категория"],
        )
        article_type = st.radio(
            "Формат *",
            ["seo", "geo"],
            horizontal=True,
            help=(
                "**seo** — классическая статья-руководство (1500-2500 слов)\n\n"
                "**geo** — AEO-формат для цитирования в AI-поиске (2000-4000 слов), "
                "со сравнительными таблицами и матрицей решений"
            ),
        )

    can_run = bool(api_key and main_keyword)

    run_btn = st.button(
        "🚀 Запустить генерацию",
        type="primary",
        disabled=not can_run,
        key="run_single",
    )

    if not api_key:
        st.caption("⚠️ Укажите API Key в боковой панели")
    elif not main_keyword:
        st.caption("⚠️ Введите ключевой запрос")

    # ── Run ──────────────────────────────────────────────────────────────────

    if run_btn and can_run:
        row_data = {
            "main_keyword": main_keyword,
            "cluster_keywords": cluster_keywords or "",
            "search_intent": search_intent,
            "page_type": page_type,
            "article_type": article_type,
        }

        st.divider()
        st.subheader("⏳ Прогресс")

        progress_placeholder = st.empty()
        # Show initial state
        progress_placeholder.markdown(
            "\n\n".join(f"○ {label}" for label in AGENT_LABELS.values())
        )

        error_occurred = False
        try:
            ctx = run_single_pipeline(
                row_data=row_data,
                output_dir=output_dir,
                sitemap_pages=sitemap_pages,
                cases_sheet=cases_sheet,
                api_key=api_key,
                progress_placeholder=progress_placeholder,
            )
            st.session_state["single_ctx"] = ctx
            st.session_state["single_keyword"] = main_keyword
        except Exception as e:
            st.error(f"Ошибка пайплайна: {e}")
            error_occurred = True

        if not error_occurred:
            st.success("Готово!")

    # ── Results ───────────────────────────────────────────────────────────────

    if "single_ctx" in st.session_state and st.session_state.get("single_keyword") == main_keyword:
        ctx = st.session_state["single_ctx"]
        st.divider()
        st.subheader("📋 QA-отчёт")
        render_qa(ctx)
        st.subheader("⬇️ Скачать")
        render_downloads(ctx, output_dir)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 · CSV batch
# ══════════════════════════════════════════════════════════════════════════════

with tab_csv:

    st.subheader("Пакетная обработка")

    with st.expander("📋 Формат CSV-файла", expanded=False):
        st.markdown(
            "Загрузите CSV с колонками (можно скопировать пример ниже):"
        )
        st.code(
            "main_keyword,cluster_keywords,search_intent,page_type,article_type\n"
            '"нейросети для рекламы","AI реклама, автоматизация",информационный,статья,seo\n'
            '"реклама в Telegram Ads","telegram ads цена, реклама в тг",коммерческий,статья,seo\n'
            '"лучшие инструменты 2026","Яндекс Директ, VK, Telegram",информационный,статья,geo',
            language="csv",
        )
        st.markdown(
            "**Допустимые значения:**\n"
            "- `search_intent`: информационный / коммерческий / навигационный\n"
            "- `page_type`: статья / лендинг / категория\n"
            "- `article_type`: seo / geo (по умолчанию seo)"
        )

    csv_file = st.file_uploader(
        "Загрузить CSV",
        type=["csv"],
        key="csv_upload",
    )

    if csv_file:
        try:
            df = pd.read_csv(csv_file)
        except Exception as e:
            st.error(f"Не удалось прочитать CSV: {e}")
            df = None

        if df is not None:
            required_cols = {"main_keyword", "cluster_keywords", "search_intent", "page_type"}
            missing = required_cols - set(df.columns)
            if missing:
                st.error(f"В CSV отсутствуют колонки: {', '.join(missing)}")
            else:
                st.dataframe(df, use_container_width=True, hide_index=True)

                run_csv_btn = st.button(
                    f"🚀 Запустить для {len(df)} строк",
                    type="primary",
                    disabled=not api_key,
                    key="run_csv",
                )

                if not api_key:
                    st.caption("⚠️ Укажите API Key в боковой панели")

                if run_csv_btn and api_key:
                    results = []
                    progress_bar = st.progress(0.0, text="Начинаю обработку...")
                    status_area = st.empty()

                    for i, csv_row in df.iterrows():
                        keyword = str(csv_row.get("main_keyword", ""))
                        progress_bar.progress(
                            float(i) / len(df),
                            text=f"[{i + 1}/{len(df)}] {keyword}",
                        )
                        status_area.info(f"Генерирую: **{keyword}**")

                        row_data = {
                            "main_keyword": keyword,
                            "cluster_keywords": str(csv_row.get("cluster_keywords", "")),
                            "search_intent": str(csv_row.get("search_intent", "информационный")),
                            "page_type": str(csv_row.get("page_type", "статья")),
                            "article_type": str(csv_row.get("article_type", "seo")),
                        }

                        dummy_ph = st.empty()  # progress_placeholder not needed here
                        try:
                            ctx = run_single_pipeline(
                                row_data=row_data,
                                output_dir=output_dir,
                                sitemap_pages=sitemap_pages,
                                cases_sheet=cases_sheet,
                                api_key=api_key,
                                progress_placeholder=dummy_ph,
                            )
                            results.append({"keyword": keyword, "ctx": ctx, "error": None})
                        except Exception as e:
                            results.append({"keyword": keyword, "ctx": None, "error": str(e)})
                        finally:
                            dummy_ph.empty()

                    progress_bar.progress(1.0, text="✅ Все статьи готовы!")
                    status_area.empty()
                    st.session_state["csv_results"] = results

        # ── CSV Results ────────────────────────────────────────────────────

        if "csv_results" in st.session_state:
            results = st.session_state["csv_results"]
            st.divider()
            st.subheader(f"Результаты · {len(results)} статей")

            # Summary table
            summary = []
            for r in results:
                if r["ctx"] and r["ctx"].qa_report:
                    qa = r["ctx"].qa_report
                    summary.append({
                        "Запрос": r["keyword"],
                        "QA": "✅ PASS" if qa.overall_passed else "❌ FAIL",
                        "Проблем": len(qa.issues),
                    })
                else:
                    summary.append({
                        "Запрос": r["keyword"],
                        "QA": "❌ ОШИБКА",
                        "Проблем": r.get("error", "—"),
                    })

            st.dataframe(pd.DataFrame(summary), hide_index=True, use_container_width=True)

            # ZIP all outputs
            out_path = Path(output_dir)
            if out_path.exists():
                st.download_button(
                    label="⬇️ Скачать все статьи (ZIP)",
                    data=zip_folder(out_path),
                    file_name="geo_seo_batch.zip",
                    mime="application/zip",
                    use_container_width=True,
                    type="primary",
                )

            # Per-keyword detail expanders
            for r in results:
                qa_ok = r["ctx"] and r["ctx"].qa_report and r["ctx"].qa_report.overall_passed
                with st.expander(
                    f"{'✅' if qa_ok else '❌'} {r['keyword']}",
                    expanded=False,
                ):
                    if r["ctx"]:
                        render_qa(r["ctx"])
                        render_downloads(r["ctx"], output_dir)
                    else:
                        st.error(f"Ошибка: {r['error']}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 · Help
# ══════════════════════════════════════════════════════════════════════════════

with tab_help:
    st.subheader("Как пользоваться")

    st.markdown("""
### Быстрый старт

1. **Введите API Key** в боковой панели (получить на [console.anthropic.com](https://console.anthropic.com))
2. Перейдите на вкладку **Одна статья** или **Пакет CSV**
3. Заполните поля и нажмите **Запустить генерацию**
4. Скачайте готовую HTML-статью или ZIP со всеми артефактами

---

### Пайплайн из 9 агентов

| Агент | Задача |
|-------|--------|
| 0 · Cases Matcher | Подбирает кейсы из Google Таблицы (если указан Sheet ID) |
| 1 · Keyword Analyzer | Заголовок, H1, H2-структура, мета-описание |
| 2 · LSI Expansion | 20-30 LSI-слов, сущности, вопросы аудитории |
| 3 · Fact Collector | Факты, статистика, примеры |
| 4 · Article Writer | Черновик 1500-4000 слов (Markdown) |
| 5 · SEO Editor | Оптимизация: FAQ, таблицы, плотность ключей |
| 6 · HTML Formatter | Конвертация в семантический HTML (CSS HotHeads) |
| 7 · Internal Linking | 4-8 внутренних ссылок из sitemap |
| 8 · Link Inserter | Вставка `<a>` тегов в текст |
| 9 · Final QA | 9-пунктовый чеклист, итоговый HTML |

---

### SEO vs GEO формат

**SEO-статья** — классический лонгрид с экспертной цитатой, FAQ, CTA.
Длина: 1500-2500 слов.

**GEO/AEO-статья** — оптимизирована для цитирования AI-поисковиками (Perplexity, ChatGPT Search, Яндекс Нейро).
Структура: сравнительная таблица → методология → нумерованные разделы → матрица решений.
Длина: 2000-4000 слов.

---

### Sitemap JSON

Загрузите файл формата:
```json
[
  {"url": "/blog/yandex-direct/", "title": "Яндекс Директ: настройка"},
  {"url": "/keisi/ecom-case/",    "title": "Кейс: e-commerce +240% ROI"}
]
```
Используется для подбора внутренних ссылок (Агент 7).
Без файла агент использует демо-страницы.

---

### Google Sheet (кейсы)

Таблица должна быть публично доступна (режим «Любой с ссылкой»).
Обязательные колонки: `url`, `title`, `description`, `industry`, `services`, `result`, `keywords`.

---

### Куда вставлять HTML

Готовый файл `_final.html` содержит полный CSS HotHeads Band и контент.
Вставляйте в **Tilda Zero Block** как HTML-вставку — стили применятся автоматически.
    """)
