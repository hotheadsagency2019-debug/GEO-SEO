"""
HotHeads Band brand configuration.
The BRAND_CSS constant is the canonical, verbatim stylesheet — never modify it from agents.
The HTML formatter generates only inner content; this module wraps it with the style block.
"""

# ─── Brand colours ────────────────────────────────────────────────────────────
COLORS = {
    "dark":        "#3e3e3e",
    "light_bg":    "#e9e9e9",
    "orange":      "#e27829",
    "dark_gray":   "#3C3C3C",
    "border":      "#c8cdd9",
}

# ─── Canonical CSS (verbatim — do NOT edit) ───────────────────────────────────
BRAND_CSS = """\
/* ── Zero Block height fix ── */
.t-zeroblock, .t-zeroblock__container,
.t-zeroblock__grid, .t-zeroblock__window,
.t-zeroblock > div, .t-zeroblock__content {
  height: auto !important;
  min-height: 0 !important;
  max-height: none !important;
  overflow: visible !important;
  position: relative !important;
  max-width: 100% !important;
  width: 100% !important;
}

/* ── Break out of Tilda fixed container ── */
.hu-article {
  width: 100vw !important;
  max-width: 100vw !important;
  position: relative !important;
  left: 50% !important;
  right: 50% !important;
  margin-left: -50vw !important;
  margin-right: -50vw !important;
  overflow-x: hidden;
}

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.hu-article {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 17px;
  line-height: 1.75;
  color: #1a1a2e;
  background: #fff;
}

.hu-article .container {
  max-width: 820px;
  width: 100%;
  margin: 0 auto;
  padding: 40px 24px 80px;
  overflow-x: hidden;
}

/* ── Global overflow fix ── */
.hu-article * { max-width: 100%; }
.hu-article img { max-width: 100%; height: auto; }
.hu-article .table-wrap {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  margin: 28px 0;
  width: 100%;
}
.hu-article table { min-width: 480px; }

/* ── Header ── */
.hu-article .article-header {
  margin-bottom: 40px;
  padding-bottom: 32px;
  border-bottom: 2px solid #f0f0f5;
}
.hu-article .article-tag {
  display: inline-block;
  background: #e9e9e9;
  color: #3e3e3e;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: .04em;
  text-transform: uppercase;
  padding: 4px 12px;
  border-radius: 20px;
  margin-bottom: 18px;
}
.hu-article h1 {
  font-size: clamp(26px, 4vw, 38px);
  font-weight: 900;
  line-height: 1.2;
  color: #0d0d1a;
  margin-bottom: 20px;
}
.hu-article .article-meta {
  font-size: 14px;
  color: #666;
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}
.hu-article .article-meta span { display: flex; align-items: center; gap: 5px; }
.hu-article .article-meta a { color: #3e3e3e; text-decoration: none; font-weight: 700; }

/* ── Lead ── */
.hu-article .lead {
  font-size: 19px;
  line-height: 1.65;
  color: #333;
  margin-bottom: 40px;
  padding: 24px 28px;
  background: #e9e9e9;
  border-left: 4px solid #3e3e3e;
  border-radius: 0 8px 8px 0;
}

/* ── TOC ── */
.hu-article .toc {
  background: #e9e9e9;
  border: 1px solid #c8cdd9;
  border-radius: 10px;
  padding: 24px 28px;
  margin-bottom: 48px;
}
.hu-article .toc h2 {
  font-size: 13px;
  font-weight: 800;
  color: #3e3e3e;
  text-transform: uppercase;
  letter-spacing: .06em;
  margin-bottom: 12px;
  border: none;
  padding: 0;
}
.hu-article .toc ol { padding-left: 20px; display: grid; gap: 6px; }
.hu-article .toc a { color: #3e3e3e; text-decoration: none; font-size: 15px; }
.hu-article .toc a:hover { text-decoration: underline; }

/* ── Headings ── */
.hu-article h2 {
  font-size: clamp(21px, 3vw, 27px);
  font-weight: 800;
  color: #0d0d1a;
  margin: 52px 0 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #f0f0f5;
}
.hu-article h3 { font-size: 19px; font-weight: 700; color: #1a1a2e; margin: 32px 0 12px; }
.hu-article h4 {
  font-size: 13px;
  font-weight: 800;
  color: #3e3e3e;
  margin: 24px 0 8px;
  text-transform: uppercase;
  letter-spacing: .05em;
}

/* ── Body text ── */
.hu-article p { margin-bottom: 18px; }
.hu-article p:last-child { margin-bottom: 0; }
.hu-article strong { font-weight: 700; }
.hu-article a { color: #3e3e3e; }

/* ── Stats grid ── */
.hu-article .stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin: 28px 0;
}
.hu-article .stat-card {
  background: #e9e9e9;
  border: 1px solid #c8cdd9;
  border-radius: 10px;
  padding: 20px;
  text-align: center;
}
.hu-article .stat-number { font-size: 30px; font-weight: 900; color: #3e3e3e; line-height: 1.1; display: block; }
.hu-article .stat-label  { font-size: 13px; color: #555; margin-top: 6px; line-height: 1.35; }

/* ── Network cards ── */
.hu-article .network-grid { display: grid; gap: 20px; margin: 28px 0; }
.hu-article .network-card {
  border: 1px solid #e8e8f0;
  border-radius: 12px;
  padding: 24px;
  position: relative;
  transition: box-shadow .2s;
}
.hu-article .network-card:hover { box-shadow: 0 4px 20px rgba(120,132,164,.15); }
.hu-article .network-card .badge { position: absolute; top: 20px; right: 20px; font-size: 12px; font-weight: 700; padding: 4px 10px; border-radius: 20px; }
.hu-article .badge-top   { background: #e9e9e9; color: #3e3e3e; }
.hu-article .badge-grow  { background: #fdf0e8; color: #e27829; }
.hu-article .badge-niche { background: #f3f3f3; color: #555; }
.hu-article .network-name  { font-size: 18px; font-weight: 800; color: #0d0d1a; margin-bottom: 6px; }
.hu-article .network-reach { font-size: 13px; color: #888; margin-bottom: 12px; font-weight: 600; }
.hu-article .network-card p { font-size: 15px; margin-bottom: 10px; }
.hu-article .network-card p:last-child { margin-bottom: 0; }
.hu-article .pros-list { list-style: none; padding: 0; margin: 10px 0 0; display: flex; flex-wrap: wrap; gap: 8px; }
.hu-article .pros-list li { background: #e9e9e9; color: #3e3e3e; font-size: 13px; font-weight: 600; padding: 4px 12px; border-radius: 20px; }

/* ── Tables ── */
.hu-article th { background: #3C3C3C; color: #fff; font-weight: 700; padding: 12px 16px; text-align: left; white-space: nowrap; }
.hu-article td { padding: 11px 16px; border-bottom: 1px solid #f0f0f5; vertical-align: top; }
.hu-article tr:nth-child(even) td { background: #f7f8fa; }
.hu-article tr:last-child td { border-bottom: none; }

/* ── Callouts ── */
.hu-article .callout { border-radius: 10px; padding: 20px 24px; margin: 28px 0; font-size: 15px; line-height: 1.65; }
.hu-article .callout-tip  { background: #e9e9e9; border-left: 4px solid #3e3e3e; }
.hu-article .callout-warn { background: #fdf6e8; border-left: 4px solid #e8a020; }
.hu-article .callout-info { background: #fdf0e8; border-left: 4px solid #e27829; }
.hu-article .callout strong { display: block; margin-bottom: 6px; color: #0d0d1a; }

/* ── Step list ── */
.hu-article .step-list { list-style: none; padding: 0; margin: 20px 0; counter-reset: steps; }
.hu-article .step-list li {
  counter-increment: steps;
  padding: 14px 16px 14px 60px;
  position: relative;
  border-bottom: 1px solid #f0f0f5;
  font-size: 15px;
}
.hu-article .step-list li:last-child { border-bottom: none; }
.hu-article .step-list li::before {
  content: counter(steps);
  position: absolute; left: 14px; top: 18px;
  width: 30px; height: 30px;
  background: #3e3e3e; color: #fff;
  font-weight: 800; font-size: 14px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
}

/* ── Expert quote ── */
.hu-article .expert-quote {
  margin: 36px 0;
  padding: 28px 32px;
  background: #fdf0e8;
  border-left: 4px solid #e27829;
  border-radius: 0 12px 12px 0;
  position: relative;
}
.hu-article .expert-quote::before {
  content: "\201C";
  font-size: 72px;
  line-height: 1;
  color: #c9b8e8;
  position: absolute; top: 12px; left: 18px;
  font-family: Georgia, serif;
}
.hu-article .expert-quote blockquote {
  font-size: 17px;
  line-height: 1.7;
  color: #1a1a2e;
  font-style: italic;
  margin: 0 0 14px 28px;
}
.hu-article .expert-quote cite { font-style: normal; font-size: 14px; color: #555; margin-left: 28px; display: block; }
.hu-article .expert-quote cite strong { color: #3e3e3e; }

/* ── FAQ ── */
.hu-article .faq-item { border-bottom: 1px solid #f0f0f5; padding: 20px 0; }
.hu-article .faq-item:last-child { border-bottom: none; }
.hu-article .faq-q { font-size: 17px; font-weight: 700; color: #0d0d1a; margin-bottom: 10px; }
.hu-article .faq-a { font-size: 15px; color: #444; }

/* ── Forecast ── */
.hu-article .forecast-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin: 24px 0; }
.hu-article .forecast-card { background: #fff; border: 1px solid #e8e8f0; border-radius: 10px; padding: 20px; }
.hu-article .forecast-card h4 { font-size: 13px; color: #3e3e3e; font-weight: 800; text-transform: uppercase; letter-spacing: .05em; margin: 0 0 8px; border: none; padding: 0; }
.hu-article .forecast-card p { font-size: 14px; color: #444; margin: 0; }

/* ── Cases ── */
.hu-article .cases-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 28px 0; }
.hu-article .case-card { border: 1px solid #e8e8f0; border-radius: 14px; padding: 24px; background: #fff; transition: box-shadow .2s, transform .15s; }
.hu-article .case-card:hover { box-shadow: 0 6px 28px rgba(120,132,164,.2); transform: translateY(-2px); }
.hu-article .case-card-nda { background: #fafafa; border-style: dashed; }
.hu-article .case-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 10px; flex-wrap: wrap; }
.hu-article .case-name     { display: block; font-size: 18px; font-weight: 800; color: #0d0d1a; line-height: 1.2; }
.hu-article .case-category { display: block; font-size: 13px; color: #888; margin-top: 3px; }
.hu-article .case-tags     { display: flex; flex-wrap: wrap; gap: 6px; justify-content: flex-end; }
.hu-article .case-tag      { font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 20px; background: #e9e9e9; color: #3e3e3e; white-space: nowrap; }
.hu-article .tag-geo       { background: #fdf0e8; color: #e27829; }
.hu-article .case-duration { font-size: 12px; color: #aaa; font-weight: 600; letter-spacing: .03em; text-transform: uppercase; margin-bottom: 16px; }
.hu-article .case-results  { display: flex; gap: 16px; margin-bottom: 16px; padding: 16px; background: #e9e9e9; border-radius: 10px; }
.hu-article .case-result   { flex: 1; text-align: center; }
.hu-article .result-number { display: block; font-size: 24px; font-weight: 900; color: #3e3e3e; line-height: 1.1; }
.hu-article .result-label  { display: block; font-size: 11px; color: #666; margin-top: 4px; line-height: 1.3; }
.hu-article .case-logo     { width: 52px; height: 52px; border-radius: 12px; object-fit: cover; flex-shrink: 0; border: 1px solid #e8e8f0; }
.hu-article .case-app-info { display: flex; align-items: center; gap: 12px; }
.hu-article a.case-card-link {
  display: block; text-decoration: none; color: inherit;
  border: 1px solid #e8e8f0; border-radius: 14px; padding: 24px; background: #fff;
  transition: box-shadow .2s, transform .15s;
}
.hu-article a.case-card-link:hover { box-shadow: 0 6px 28px rgba(120,132,164,.2); transform: translateY(-2px); }
.hu-article a.case-card-link.case-card-nda { background: #fafafa; border-style: dashed; }

/* ── CTA ── */
.hu-article .cta-block {
  margin: 48px 0 0;
  background: linear-gradient(135deg, #3C3C3C 0%, #4a4a4a 60%, #3C3C3C 100%);
  border-radius: 16px;
  padding: 36px 40px;
  display: flex; align-items: center; gap: 32px; flex-wrap: wrap;
  position: relative; overflow: hidden;
}
.hu-article .cta-block::before {
  content: "";
  position: absolute; top: 0; right: 0; width: 300px; height: 100%;
  background: linear-gradient(135deg, transparent, rgba(120,132,164,.25));
  pointer-events: none;
}
.hu-article .cta-text  { flex: 1; min-width: 200px; position: relative; }
.hu-article .cta-title { font-size: 20px; font-weight: 800; color: #fff; margin-bottom: 8px; }
.hu-article .cta-body  { font-size: 15px; color: rgba(255,255,255,.8); line-height: 1.6; margin: 0; }
.hu-article .cta-btn {
  display: inline-block;
  background: transparent; color: #fff;
  border: 2px solid #fff;
  font-weight: 800; font-size: 15px;
  padding: 12px 28px; border-radius: 10px;
  text-decoration: none; white-space: nowrap;
  transition: background .15s, transform .15s;
  position: relative;
}
.hu-article .cta-btn:hover { background: rgba(255,255,255,.15); transform: translateY(-1px); }
.hu-article .cta-buttons { display: flex; gap: 12px; flex-wrap: wrap; }

/* ── Footer ── */
.hu-article .article-footer { margin-top: 60px; padding-top: 32px; border-top: 2px solid #f0f0f5; font-size: 13px; color: #888; }

/* ══ TABLET 768px ══ */
@media (max-width: 768px) {
  .hu-article .container { padding: 28px 20px 60px; }
  .hu-article h1 { font-size: 28px; }
  .hu-article h2 { font-size: 22px; margin: 40px 0 16px; }
  .hu-article h3 { font-size: 17px; }
  .hu-article .lead { font-size: 17px; padding: 18px 20px; }
  .hu-article .stats-grid { grid-template-columns: repeat(2,1fr); gap: 12px; }
  .hu-article .forecast-grid { grid-template-columns: repeat(2,1fr); }
  .hu-article .cases-grid { grid-template-columns: 1fr; }
  .hu-article .network-card { padding: 18px; }
  .hu-article .toc { padding: 18px 20px; }
  .hu-article .callout { padding: 16px 18px; }
  .hu-article .cta-block { padding: 28px 24px; gap: 24px; }
  .hu-article .expert-quote { padding: 20px 20px 20px 24px; }
  .hu-article .expert-quote::before { font-size: 52px; top: 8px; left: 12px; }
  .hu-article .expert-quote blockquote { margin-left: 16px; font-size: 15px; }
  .hu-article .expert-quote cite { margin-left: 16px; }
}

/* ══ MOBILE 480px ══ */
@media (max-width: 480px) {
  .hu-article .container { padding: 20px 16px 48px; }
  .hu-article h1 { font-size: 24px; line-height: 1.25; }
  .hu-article .article-meta { flex-direction: column; gap: 6px; font-size: 13px; }
  .hu-article .article-tag { font-size: 11px; padding: 3px 10px; }
  .hu-article .lead { font-size: 16px; padding: 16px; border-left-width: 3px; }
  .hu-article .toc { padding: 16px; }
  .hu-article .toc ol { padding-left: 16px; }
  .hu-article .toc a { font-size: 14px; }
  .hu-article h2 { font-size: 20px; margin: 32px 0 14px; }
  .hu-article h3 { font-size: 16px; margin: 24px 0 10px; }
  .hu-article p { font-size: 16px; }
  .hu-article .stats-grid { grid-template-columns: repeat(2,1fr); gap: 10px; }
  .hu-article .stat-card { padding: 14px 10px; }
  .hu-article .stat-number { font-size: 22px; }
  .hu-article .stat-label { font-size: 12px; }
  .hu-article .table-wrap { margin: 16px -16px; border-radius: 0; }
  .hu-article table { font-size: 13px; min-width: 480px; }
  .hu-article th, .hu-article td { padding: 9px 12px; }
  .hu-article .forecast-grid { grid-template-columns: 1fr; gap: 10px; }
  .hu-article .forecast-card { padding: 14px; }
  .hu-article .network-card { padding: 16px; }
  .hu-article .network-card .badge { position: static; display: inline-block; margin-bottom: 10px; }
  .hu-article .network-name { font-size: 16px; }
  .hu-article .network-card p { font-size: 14px; }
  .hu-article .pros-list li { font-size: 12px; padding: 3px 10px; }
  .hu-article .expert-quote { padding: 16px; border-left-width: 3px; }
  .hu-article .expert-quote::before { display: none; }
  .hu-article .expert-quote blockquote { margin-left: 0; font-size: 15px; }
  .hu-article .expert-quote cite { margin-left: 0; }
  .hu-article .callout { padding: 14px 16px; font-size: 14px; border-left-width: 3px; }
  .hu-article .step-list li { padding: 12px 12px 12px 50px; font-size: 14px; }
  .hu-article .step-list li::before { left: 10px; top: 14px; width: 26px; height: 26px; font-size: 13px; }
  .hu-article .faq-q { font-size: 15px; }
  .hu-article .faq-a { font-size: 14px; }
  .hu-article .cases-grid { grid-template-columns: 1fr; gap: 14px; }
  .hu-article a.case-card-link { padding: 16px; }
  .hu-article .case-header { flex-direction: column; align-items: flex-start; gap: 10px; }
  .hu-article .case-tags { justify-content: flex-start; }
  .hu-article .case-logo { width: 44px; height: 44px; }
  .hu-article .case-name { font-size: 16px; }
  .hu-article .result-number { font-size: 20px; }
  .hu-article .case-results { padding: 12px; gap: 10px; }
  .hu-article .case-desc { font-size: 13px; }
  .hu-article .cta-block { flex-direction: column; align-items: flex-start; padding: 20px; gap: 16px; }
  .hu-article .cta-title { font-size: 18px; }
  .hu-article .cta-body { font-size: 14px; }
  .hu-article .cta-btn { width: 100%; text-align: center; padding: 14px; }
  .hu-article .article-footer { font-size: 12px; }
}

/* ══ VERY SMALL 360px ══ */
@media (max-width: 360px) {
  .hu-article .stats-grid { grid-template-columns: 1fr 1fr; }
  .hu-article .stat-number { font-size: 20px; }
  .hu-article h1 { font-size: 22px; }
}"""

# ─── HTML wrappers (CSS injected verbatim) ───────────────────────────────────
HTML_OPEN  = f'<style>\n{BRAND_CSS}\n</style>\n\n<div class="hu-article">\n  <div class="container">\n'
HTML_CLOSE = "\n  </div>\n</div>"

# ─── Available CSS classes (passed to the formatter agent) ───────────────────
AVAILABLE_CLASSES = """
ДОСТУПНЫЕ CSS-КЛАССЫ (использовать ТОЛЬКО их, не добавлять inline-стили):

Обёртка: .hu-article > .container
Шапка:   .article-header, .article-tag, h1, .article-meta
Лид:     .lead
TOC:     .toc > h2 + ol > li > a[href="#id"]
Статистика: .stats-grid > .stat-card > .stat-number + .stat-label
Callout:    .callout.callout-tip (серый) | .callout.callout-warn (оранжевый) | .callout.callout-info
Цитата:     .expert-quote > blockquote + cite > strong
Сети:       .network-grid > .network-card > .badge(.badge-top|.badge-grow|.badge-niche) + .network-name + .network-reach + p + .pros-list
Таблицы:    .table-wrap > table > thead + tbody
FAQ:        .faq-item > .faq-q + .faq-a
Кейсы:      .cases-grid > a.case-card-link > .case-header + .case-duration + .case-results + p.case-desc
Прогноз:    .forecast-grid > .forecast-card > h4 + p
Шаги:       ol.step-list > li
CTA:        .cta-block > .cta-text(.cta-title + .cta-body) + .cta-buttons > a.cta-btn (×2: Telegram + VK)
Футер:      .article-footer
""".strip()

# ─── Content rules (injected into agent system prompts) ──────────────────────
CONTENT_RULES = """
БРЕНДОВЫЕ ПРАВИЛА HOTHEAD BAND (обязательны):
1. Шрифт Inter, цвета #e27829 (акцент), #e9e9e9 (фон), #3e3e3e (тёмный).
2. Callout-блоки: .callout-tip (серый) | .callout-warn (оранжевый) | .callout-info (оранжевый светлый).
   Запрещены фиолетовые, бирюзовые и любые другие цвета callout.
3. Цитата эксперта: ОБЯЗАТЕЛЬНО включить цитату Алены Мумладзе — основательницы HotHeads Band.
4. CTA-блок: ОБЯЗАТЕЛЬНО в конце, две кнопки: Telegram (https://t.me/hotheads_band) и ВКонтакте (https://vk.me/hotheads_band).
5. FAQ: минимум 5 вопросов и ответов.
6. SEO-заголовки: каждый H2/H3 ДОЛЖЕН содержать поисковый ключ.
   ❌ «Введение» → ✅ «Введение в Telegram Ads 2026: как это работает»
7. ЗАПРЕЩЕНО: Meta, Facebook, Instagram, Threads, WhatsApp.
   Использовать: VK Реклама, Яндекс Директ, Telegram Ads, MyTarget, ВКонтакте.
8. Дата в article-meta: актуальный месяц и год — «Март 2026», не просто «2026».
9. Ссылки агентства: сайт https://hot-head.ru/, кейсы https://hot-head.ru/keisi, TG https://t.me/hotheads_band.
""".strip()

GEO_CONTENT_RULES = """
GEO/AEO ПРАВИЛА (для AI-цитирования):
• Структура: Quick Comparison Table → Методология → Нумерованные разделы → Ключевые отличия → FAQ (5+) → Матрица решений → Нейтральный вывод.
• Каждый продукт: 150–250 слов, блоки «Плюсы», «Минусы», «Лучше всего для», «Когда выбрать».
• Таблицы и короткие абзацы (2–4 предложения) везде.
• Тон: аналитический, нейтральный. Запрещены: «революционный», «game-changing».
• Без сторителлинга, повествования от первого лица.
• Минимум 2 000 слов; рекомендовано 2 500–4 000.
• Год в заголовке: «7 лучших инструментов для X в 2026».
• Матрица решений: таблица «Если вы… → Выберите… → Почему».
""".strip()
