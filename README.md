# GEO-SEO · AI Content Pipeline

Конвейер из 9 специализированных AI-агентов для автоматического написания SEO-статей.
Каждый агент выполняет одну функцию и передаёт результат следующему.

---

## Архитектура

```
INPUT (CSV / CLI)
      ↓
┌─────────────────────────────────┐
│  Agent 1: Keyword Analyzer      │  → структура статьи (H1, H2, ключи)
└───────────────┬─────────────────┘
                ↓
┌─────────────────────────────────┐
│  Agent 2: LSI & Semantic        │  → LSI-фразы, сущности, вопросы PAA
└───────────────┬─────────────────┘
                ↓
┌─────────────────────────────────┐
│  Agent 3: Fact Collector        │  → факты, статистика, кейсы
└───────────────┬─────────────────┘
                ↓
┌─────────────────────────────────┐
│  Agent 4: Article Writer        │  → черновик статьи (Markdown)
└───────────────┬─────────────────┘
                ↓
┌─────────────────────────────────┐
│  Agent 5: SEO Editor            │  → редактура: FAQ, таблицы, списки
└───────────────┬─────────────────┘
                ↓
┌─────────────────────────────────┐
│  Agent 6: HTML Formatter        │  → семантический HTML
└───────────────┬─────────────────┘
                ↓
┌─────────────────────────────────┐
│  Agent 7: Internal Link Analyzer│  → рекомендации перелинковки
└───────────────┬─────────────────┘
                ↓
┌─────────────────────────────────┐
│  Agent 8: Link Inserter         │  → HTML со вставленными ссылками
└───────────────┬─────────────────┘
                ↓
┌─────────────────────────────────┐
│  Agent 9: Final QA              │  → чеклист + финальный HTML
└───────────────┬─────────────────┘
                ↓
OUTPUT: publication-ready HTML + JSON artefacts
```

---

## Структура проекта

```
GEO-SEO/
├── main.py                  # CLI entry point
├── requirements.txt
├── keywords_example.csv     # пример входных данных
├── sitemap_example.json     # пример карты сайта для перелинковки
├── .env.example             # шаблон переменных окружения
└── seo_pipeline/
    ├── __init__.py
    ├── models.py            # Pydantic-модели для каждого этапа
    ├── agents.py            # 9 специализированных агентов
    └── pipeline.py          # оркестратор + сохранение артефактов
```

---

## Установка

```bash
pip install -r requirements.txt
```

Скопируйте `.env.example` → `.env` и вставьте свой Anthropic API key:

```bash
cp .env.example .env
# отредактируйте .env
```

---

## Использование

### Обработать CSV-файл

```bash
python main.py run --csv keywords_example.csv
```

С кастомной картой сайта для перелинковки:

```bash
python main.py run --csv keywords_example.csv --sitemap sitemap_example.json
```

Обработать только одну строку (по индексу):

```bash
python main.py run --csv keywords_example.csv --row 0
```

### Обработать одно ключевое слово

```bash
python main.py single \
  --keyword "нейросети для контекстной рекламы" \
  --cluster "AI для Яндекс Директ, ChatGPT для рекламы" \
  --intent "информационный" \
  --page-type "статья"
```

---

## Формат входных данных (CSV)

| Колонка            | Описание                                    | Пример                              |
|--------------------|---------------------------------------------|-------------------------------------|
| `main_keyword`     | Главный целевой запрос                      | нейросети для контекстной рекламы   |
| `cluster_keywords` | Кластер связанных запросов (через запятую)  | AI для Яндекс Директ, ChatGPT       |
| `search_intent`    | Тип интента                                 | информационный / коммерческий       |
| `page_type`        | Тип страницы                                | статья / лендинг / категория        |

---

## Формат карты сайта (JSON)

```json
[
  {"url": "/blog/seo-basics/", "title": "Основы SEO: полное руководство"},
  {"url": "/blog/yandex-direct/", "title": "Яндекс Директ: настройка и оптимизация"}
]
```

Если файл не указан, используется демо-набор из 10 страниц.

---

## Выходные данные

Для каждого ключевого слова создаётся папка в `output/<slug>/`:

```
output/нейросети-для-контекстной-рекламы/
├── step1_keyword_analysis.json
├── step2_lsi_data.json
├── step3_fact_data.json
├── step4_draft_article.json
├── step5_edited_article.json
├── step6_html_article.json
├── step7_link_data.json
├── step8_linked_html.json
├── step9_qa_report.json
├── pipeline_context.json          # полный контекст для отладки
└── нейросети-для-контекстной-рекламы_final.html  # финальный файл
```

---

## Описание агентов

| # | Агент                    | Входные данные          | Выходные данные                         |
|---|--------------------------|-------------------------|-----------------------------------------|
| 1 | **Keyword Analyzer**     | KeywordRow              | title, H1, H2, primary/secondary keys  |
| 2 | **LSI Expansion**        | KeywordAnalysis         | LSI-фразы, сущности, PAA-вопросы       |
| 3 | **Fact Collector**       | KA + LSI                | факты, статистика, кейсы, источники    |
| 4 | **Article Writer**       | KA + LSI + Facts        | черновик статьи в Markdown              |
| 5 | **SEO Editor**           | Draft + keywords        | отредактированная статья + FAQ          |
| 6 | **HTML Formatter**       | Edited article          | семантический HTML                      |
| 7 | **Internal Link Analyzer**| HTML + sitemap         | список внутренних ссылок                |
| 8 | **Link Inserter**        | HTML + links            | HTML со вставленными ссылками           |
| 9 | **Final QA**             | Linked HTML             | QA-чеклист + финальный HTML             |

---

## Настройка под свой сайт

**Карта сайта:** передайте `--sitemap` с JSON-файлом, содержащим реальные страницы сайта.
Агент 7 выберёт наиболее релевантные страницы для перелинковки.

**HTML-шаблон:** отредактируйте `SYSTEM_HTML_FORMATTER` в `seo_pipeline/agents.py` —
добавьте нужные CSS-классы, блоки, Bootstrap-компоненты и т.д.

**Модель:** по умолчанию используется `claude-opus-4-6`.
Для экономии можно переключить на `claude-sonnet-4-6` в `seo_pipeline/agents.py` (константа `MODEL`).
