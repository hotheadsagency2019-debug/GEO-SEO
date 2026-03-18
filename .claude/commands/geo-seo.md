Запусти 9-агентный SEO/GEO пайплайн HotHeads Band для генерации статьи.

## Аргументы

$ARGUMENTS

## Как разобрать аргументы

Извлеки из аргументов выше:

| Флаг | Короткий | По умолчанию | Описание |
|------|----------|-------------|----------|
| `--keyword` | `-k` | **обязателен** | Главный ключевой запрос статьи |
| `--type` | `-t` | `seo` | Тип статьи: `seo` или `geo` |
| `--cluster` | `-c` | `""` | Кластер ключей через запятую |
| `--intent` | `-i` | `информационный` | Поисковый интент |
| `--page-type` | `-p` | `статья` | Тип страницы |
| `--sitemap` | — | нет | Путь к sitemap JSON |
| `--cases-sheet` | — | нет | ID Google Sheet с кейсами агентства |
| `--output` | — | `output` | Папка для результатов |
| `--csv` | — | нет | CSV-файл с несколькими запросами |
| `--row` | — | нет | Индекс строки (0-based) в CSV |

Если аргументы не переданы — спроси пользователя о ключевом слове и типе статьи (seo/geo) прежде чем продолжить.

## Шаги выполнения

### 1. Проверь окружение

Убедись что:
- Переменная `ANTHROPIC_API_KEY` установлена (проверь через `echo $ANTHROPIC_API_KEY`)
- Файл `main.py` существует в текущей директории
- Установлены зависимости (`pip install -r requirements.txt` если нужно)

Если ключ не найден — сообщи пользователю и остановись.

### 2. Собери команду

**Одиночный запрос (по умолчанию):**
```
python main.py single \
  --keyword "<keyword>" \
  --article-type <seo|geo> \
  --cluster "<cluster>" \
  --intent "<intent>" \
  --page-type "<page-type>" \
  [--sitemap <path>] \
  [--cases-sheet <id>] \
  [--output <dir>]
```

**Из CSV (если передан --csv):**
```
python main.py run \
  --csv <path> \
  [--row <index>] \
  [--sitemap <path>] \
  [--cases-sheet <id>] \
  [--output <dir>]
```

### 3. Запусти пайплайн

Выполни команду через Bash и выводи прогресс в реальном времени. Пайплайн проходит 9 агентов — это занимает несколько минут.

### 4. Покажи результаты

После завершения:
- Укажи путь к готовому HTML-файлу: `output/<slug>/<slug>_final.html`
- Покажи итоги QA-чеклиста (9 критериев)
- Сообщи о любых ошибках или предупреждениях

---

## Справка по пайплайну

9 агентов работают последовательно, передавая `PipelineContext` друг другу:

| # | Агент | Результат |
|---|-------|-----------|
| 0 | Cases Matcher | Подбирает 3-5 релевантных кейсов агентства (только при `--cases-sheet`) |
| 1 | Keyword Analyzer | Структура статьи: H1, H2, мета, ключи |
| 2 | LSI Expansion | LSI-термины, сущности, вопросы пользователей |
| 3 | Fact Collector | Факты, статистика, примеры для рынка РФ |
| 4 | Article Writer | Полный черновик на Markdown (SEO или GEO формат) |
| 5 | SEO Editor | Редактура: FAQ, таблицы, читабельность |
| 6 | HTML Formatter | Конвертация в семантический HTML с CSS HotHeads Band |
| 7 | Internal Linker | Анализ 4-8 внутренних ссылок по sitemap |
| 8 | Link Inserter | Вставка ссылок в HTML |
| 9 | Final QA | 9-пунктовый чеклист качества, финальный HTML |

**Выходные файлы** сохраняются в `output/<slug>/`:
- `step0_matched_cases.json` … `step9_qa_report.json` — промежуточные результаты
- `pipeline_context.json` — полный контекст для отладки
- `<slug>_final.html` — готовая статья для публикации в Tilda

---

## Примеры запуска

```
/geo-seo --keyword "нейросети для контекстной рекламы"

/geo-seo --keyword "лучшие сервисы email-маркетинга 2026" --type geo --cluster "email рассылки, платформы email маркетинга, unisender, sendpulse"

/geo-seo --keyword "Яндекс Директ настройка 2026" --intent "коммерческий" --cluster "директ кабинет, настройка рекламы яндекс"

/geo-seo --csv keywords.csv --row 0

/geo-seo --csv keywords.csv --sitemap sitemap_example.json --cases-sheet 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms
```
