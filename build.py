#!/usr/bin/env python3
"""MyToolPad build: one tools list -> nav, footer, search index, category hubs,
home page grid, sitemap. Safe to run any number of times.

Usage:  python3 build.py
Add a tool: put the HTML file in this folder, add an entry to TOOLS below, run the build.
"""
import hashlib, json, os, re, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = 'https://www.mytoolpad.com'
TODAY = datetime.date.today().isoformat()

CATS = [
    # id, nav label, hub file, hub title, hub intro
    ('study', 'Study', 'study-tools.html', 'Study tools',
     'Calculators and focus tools for Australian uni and school students: GPA, WAM, the mark you need on your final, and a Pomodoro timer.'),
    ('money', 'Money', 'money-tools.html', 'Money tools',
     'Australian money calculators that run in your browser: take-home pay, HECS-HELP repayments, GST, NSW stamp duty, loans and budgets.'),
    ('images', 'Images', 'image-tools.html', 'Image tools',
     'Compress, resize and convert images, turn iPhone HEIC photos into JPG, and preview wallpapers on any screen. Nothing is uploaded.'),
    ('productivity', 'Productivity', 'productivity-tools.html', 'Productivity tools',
     'A to-do list, notes, a focus timer and countdowns that save in your browser. No account needed.'),
    ('everyday', 'Everyday', 'everyday-tools.html', 'Everyday tools',
     'Quick everyday calculators: age, dates, units, BMI, tips, percentages and a decision wheel.'),
    ('text', 'Text & Dev', 'text-and-dev-tools.html', 'Text and developer tools',
     'Count words, format JSON, generate passwords and pick colours.'),
]
CAT = {c[0]: c for c in CATS}

# file, name, short (nav/search label), icon, categories (first = main), description, extra search words
TOOLS = [
    ('todo.html', 'To-Do List', 'To-Do', '✓', ['productivity'], 'Tasks with priorities, drag-to-reorder, and filter by status. Double-click any task to edit it inline.', 'todo tasks checklist list jobs'),
    ('pomodoro.html', 'Pomodoro Focus Timer', 'Focus timer', '◔', ['productivity', 'study'], 'Pomodoro timer with auto long-breaks, session tracking, sound alerts and a built-in task list.', 'pomodoro timer focus study tomato break'),
    ('notes.html', 'Online Notes', 'Notes', '✦', ['productivity', 'study'], 'Multiple notes, instant search, auto-saves as you type. Your private scratchpad.', 'notes notepad scratchpad write memo'),
    ('counter.html', 'Word Counter', 'Word counter', 'Aa', ['text', 'study'], 'Paste any text and see word count, characters, readability score and reading time.', 'word count character count letters essay assignment'),
    ('budget.html', 'Budget Tracker', 'Budget', '◈', ['money'], 'Log income and expenses by month. Private, offline, no bank linking.', 'budget expenses spending money planner'),
    ('spinner.html', 'Decision Spinner Wheel', 'Spinner wheel', '◎', ['everyday'], 'Add your options and spin a wheel to decide. Like Wheel of Names, without the ads.', 'spinner wheel random picker decide names raffle'),
    ('countdown.html', 'Countdown Timer', 'Countdown', '⧖', ['productivity', 'everyday'], 'Year progress, days left in the year, and live countdowns to any date you set.', 'countdown days until timer event'),
    ('password.html', 'Password Generator', 'Password', '⚿', ['text'], 'Generate strong passwords. Choose length and character sets. Never stored or sent anywhere.', 'password generator secure random passphrase'),
    ('converter.html', 'Unit Converter', 'Unit converter', '⇌', ['everyday'], 'Convert length, weight, temperature, volume, area, speed and data.', 'unit converter metric imperial kg lbs cm inches celsius fahrenheit'),
    ('percentage.html', 'Percentage Calculator', 'Percentage', '%', ['everyday', 'money'], 'What is X% of Y, percentage change, discounts, add and subtract percentages.', 'percent percentage discount increase decrease'),
    ('age.html', 'Age Calculator', 'Age', '◷', ['everyday'], 'Your exact age in years, months and days, plus a next-birthday countdown.', 'age birthday born how old'),
    ('tip.html', 'Tip Calculator', 'Tip', '⊘', ['everyday', 'money'], 'Work out the tip and split the bill between any number of people.', 'tip split bill restaurant'),
    ('color.html', 'Color Picker', 'Colour picker', '◐', ['text', 'images'], 'Pick a colour and get HEX, RGB and HSL, shades, tints and a WCAG contrast check.', 'color colour picker hex rgb hsl contrast palette'),
    ('bmi.html', 'BMI Calculator', 'BMI', '⊕', ['everyday'], 'Body Mass Index in metric or imperial, with category and healthy range.', 'bmi body mass index weight height health'),
    ('loan.html', 'Loan Calculator', 'Loan', '⌂', ['money'], 'Monthly repayment, total interest and a full amortisation schedule.', 'loan mortgage repayment interest car loan home loan'),
    ('gpa.html', 'GPA Calculator', 'GPA', '✎', ['study'], 'Add courses, grades and credit points for your weighted GPA, on the Australian 7-point or US 4-point scale.', 'gpa grade point average uni 7 point 4 point'),
    ('wam-calculator.html', 'WAM Calculator', 'WAM', '≈', ['study'], 'Weighted average mark from your unit marks and credit points, plus the average you need to reach a target WAM.', 'wam weighted average mark uni marks credit points honours'),
    ('final-grade.html', 'Final Grade Calculator', 'Final grade', '★', ['study'], 'The mark you need on your final to reach P, C, D, HD or an A.', 'final exam grade mark need hd distinction'),
    ('gst-calculator.html', 'GST Calculator', 'GST', '$', ['money'], 'Add or remove 10% GST from any price in one step. Built for Australian businesses and freelancers.', 'gst tax goods services australia add remove 10%'),
    ('take-home-pay.html', 'Take-Home Pay Calculator', 'Take-home pay', '≡', ['money'], 'Australian salary after tax for 2026-27: weekly, fortnightly, monthly and yearly pay, with super and HELP.', 'take home pay salary after tax income tax wage payg net pay australia'),
    ('help-repayment.html', 'HECS-HELP Repayment Calculator', 'HECS-HELP', '⇣', ['money', 'study'], 'Your compulsory HECS-HELP repayment for 2026-27 and roughly how long it takes to pay off.', 'hecs help student loan uni debt repayment threshold'),
    ('stamp-duty-nsw.html', 'NSW Stamp Duty Calculator', 'Stamp duty', '⌗', ['money'], 'NSW transfer duty for 2026-27, with the first home buyer exemption and premium duty.', 'stamp duty transfer duty nsw property house first home buyer'),
    ('qr-code.html', 'QR Code Generator', 'QR code', '▦', ['images', 'everyday'], 'QR codes for links, text or Wi-Fi. Download PNG or SVG with custom colours. No watermark.', 'qr code generator wifi link barcode'),
    ('image-compressor.html', 'Image Compressor', 'Compress image', '◩', ['images'], 'Shrink JPG, PNG and WebP images in your browser. Nothing is uploaded.', 'compress image reduce size jpg png webp photo smaller'),
    ('image-resizer.html', 'Image Resizer and Converter', 'Resize image', '⤡', ['images'], 'Resize images to exact pixels or a percentage and convert between JPG, PNG and WebP.', 'resize image convert png to jpg webp to jpg jpg to png dimensions crop scale'),
    ('heic-to-jpg.html', 'HEIC to JPG Converter', 'HEIC to JPG', '⇄', ['images'], 'Convert iPhone HEIC photos to JPG or PNG in your browser. Batch convert, nothing uploaded.', 'heic heif to jpg iphone photo convert apple'),
    ('wallpaper-preview.html', 'Wallpaper Preview', 'Wallpaper preview', '▯', ['images'], 'See a wallpaper on any phone, tablet or monitor and check if it is high-res enough.', 'wallpaper background preview resolution phone iphone screen size'),
    ('wallpaper-sizes.html', 'Wallpaper Sizes for Every Device', 'Wallpaper sizes', '⊞', ['images'], 'A reference table of screen resolutions for iPhone, Android, iPad, MacBook and monitors.', 'wallpaper size resolution iphone dimensions pixels screen'),
    ('json-formatter.html', 'JSON Formatter', 'JSON', '{ }', ['text'], 'Beautify, minify, sort and validate JSON. Errors show the exact line and column.', 'json format beautify validate minify pretty print'),
    ('days-between-dates.html', 'Days Between Dates', 'Date calculator', '▤', ['everyday'], 'Count days, weeks and weekdays between dates, or add and subtract time from a date.', 'days between dates date calculator weekdays add days'),
]
assert len({t[0] for t in TOOLS}) == len(TOOLS), 'duplicate tool file'
FEATURED = ['take-home-pay.html', 'help-repayment.html', 'wam-calculator.html', 'pomodoro.html', 'image-compressor.html', 'heic-to-jpg.html']
PAGES = ['index.html', 'about.html', 'privacy.html', '404.html'] + [c[2] for c in CATS]
NO_ASIDE = {'wallpaper-preview.html', 'car-diagnostics-simulator.html'}  # big visual tools keep the full width


# Small-print disclaimers. Money tools get the finance wording, health tools the health wording.
DISCLAIMER_MONEY = ('General information only, not financial, tax or legal advice. Results are estimates and may not suit your '
                    'situation, and rates and rules change. Check with the ATO, Revenue NSW, your lender or a '
                    'qualified adviser before you rely on them. MyToolPad accepts no responsibility for any loss or decision made '
                    'using this tool.')
DISCLAIMER_HEALTH = ('General information only, not medical advice. BMI is a rough screening measure and does not account for '
                     'muscle, age, sex or ethnicity. Talk to a doctor about your health. MyToolPad accepts no responsibility for '
                     'decisions made using this tool.')
DISCLAIMER_STUDY = ('Estimates only. Grading scales and rules differ between universities and courses, so check your official '
                    'results and handbook. MyToolPad accepts no responsibility for decisions made using this tool.')
HEALTH = {'bmi.html'}
CUSTOM_DISCLAIMER = {'car-diagnostics-simulator.html': 'A simplified training simulator. The car, readings and faults are made up for learning and do not match any '
                     'specific vehicle. On a real car, follow the manufacturer\'s repair information and safety rules. MyToolPad accepts no '
                     'responsibility for work done on a vehicle.'}


def disclaimer_for(fname):
    t = next((x for x in TOOLS if x[0] == fname), None)
    if not t:
        return ''
    if fname in CUSTOM_DISCLAIMER:
        return CUSTOM_DISCLAIMER[fname]
    if fname in HEALTH:
        return DISCLAIMER_HEALTH
    if t[4][0] == 'money':
        return DISCLAIMER_MONEY
    if t[4][0] == 'study':
        return DISCLAIMER_STUDY
    return ''


def esc(s):
    return (s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def asset_hash():
    h = hashlib.sha1()
    for f in ['assets/site.css', 'assets/site.js', 'assets/tools.js']:
        p = os.path.join(ROOT, f)
        if os.path.exists(p):
            h.update(open(p, 'rb').read())
    return h.hexdigest()[:8]


def write_tools_js():
    data = [{'f': '/' + t[0], 'n': t[1], 's': t[2], 'i': t[3], 'c': t[4], 'd': t[5], 'k': t[6]} for t in TOOLS]
    cats = [{'id': c[0], 'n': c[1], 'f': '/' + c[2]} for c in CATS]
    js = '/* generated by build.py */\nwindow.MTP_TOOLS=' + json.dumps(data, ensure_ascii=False) + ';\nwindow.MTP_CATS=' + json.dumps(cats, ensure_ascii=False) + ';\n'
    open(os.path.join(ROOT, 'assets/tools.js'), 'w', encoding='utf-8').write(js)


SEARCH_SVG = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>'
THEME_SVG = '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><path d="M12 3.5a8.5 8.5 0 0 1 0 17z" fill="currentColor"/></svg>'
STAR_SVG = '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/></svg>'


def nav_html(fname):
    tool = next((t for t in TOOLS if t[0] == fname), None)
    hub = next((c for c in CATS if c[2] == fname), None)
    active = hub[0] if hub else (tool[4][0] if tool else None)
    cats = ''.join('<a href="/%s"%s>%s</a>' % (c[2], ' class="active" aria-current="page"' if c[0] == active and hub else (' class="active"' if c[0] == active else ''), esc(c[1])) for c in CATS)
    tool_attr = ' data-tool="/%s"' % fname if tool else ''
    pin = ('<button class="mtp-icon-btn" type="button" data-mtp-pin aria-pressed="false" aria-label="Pin this tool to My Pad" title="Pin to My Pad">%s</button>' % STAR_SVG) if tool else ''
    return ('<nav class="mtp-nav" aria-label="Main"%s>'
            '<a href="/" class="mtp-brand">My<em>Tool</em>Pad</a>'
            '<div class="mtp-cats">%s</div>'
            '<button class="mtp-search-btn" type="button" data-mtp-search aria-label="Search tools">%s<span>Search tools</span><kbd>/</kbd></button>'
            '%s<button class="mtp-icon-btn" type="button" data-mtp-theme aria-label="Theme and colour" title="Theme and colour">%s</button>'
            '</nav>') % (tool_attr, cats, SEARCH_SVG, pin, THEME_SVG)


def footer_html():
    cols = ''
    for c in CATS:
        items = [t for t in TOOLS if t[4][0] == c[0]]
        cols += '<div><a class="mtp-fh" href="/%s">%s</a>%s</div>' % (c[2], esc(c[1]), ''.join('<a href="/%s">%s</a>' % (t[0], esc(t[1])) for t in items))
    return ('<footer class="mtp-footer"><div class="mtp-fcols">%s</div>'
            '<p>MyToolPad: free tools for students and everyday life.<br>No sign-up · No pop-ups · Your data stays in your browser<br>'
            '<a href="/about.html">About</a> · <a href="/privacy.html">Privacy</a> · <a href="https://github.com/game9151/mytoolpad/issues" rel="noopener">Feedback</a><br>'
            'Tools are provided as is, for general information, without any warranty.<br>'
            'I design websites. <a href="mailto:officialmeridianstudio@gmail.com">Contact me</a></p></footer>') % cols


def head_html(v):
    return ('<script>(function(){var d=document.documentElement;try{var t=localStorage.getItem("mtp-theme")||"dark",a=localStorage.getItem("mtp-accent")||"lime";'
            'if(t==="auto")t=matchMedia("(prefers-color-scheme: light)").matches?"light":"dark";d.setAttribute("data-theme",t);d.setAttribute("data-accent",a)}'
            'catch(e){d.setAttribute("data-theme","dark")}})()</script>\n'
            '<link rel="stylesheet" href="/assets/site.css?v=%s"/>\n'
            '<link rel="manifest" href="/manifest.webmanifest"/>\n'
            '<link rel="apple-touch-icon" href="/icons/icon-192.png"/>\n'
            '<script src="/assets/tools.js?v=%s" defer></script>\n'
            '<script src="/assets/site.js?v=%s" defer></script>') % (v, v, v)


def replace_block(html, name, inner, fallback):
    """Replace content between <!-- mtp:name --> markers, or install them via fallback(html)."""
    start, end = '<!-- mtp:%s -->' % name, '<!-- /mtp:%s -->' % name
    block = start + '\n' + inner + '\n' + end
    if start in html:
        return re.sub(re.escape(start) + r'.*?' + re.escape(end), lambda m: block, html, count=1, flags=re.S)
    out = fallback(html, block)
    if out == html:
        raise SystemExit('could not place %s block' % name)
    return out


OLD_CSS_LINE = re.compile(r'^\s*(/\* Nav \*/|\.(topnav|nav-brand|nav-links|seo|site-footer)\b[^\n]*\})\s*$', re.M)


def map_colors(css):
    """Point hard-coded dark colours at theme variables (skips :root definitions)."""
    parts = re.split(r'(:root\s*\{[^}]*\})', css)
    for i, p in enumerate(parts):
        if p.lstrip().startswith(':root'):
            continue
        # text sitting on an accent background
        def fix_rule(m):
            body = m.group(2)
            if re.search(r'background(-color)?:\s*(var\(--accent\)|#c8f135)', body):
                body = re.sub(r'(?<![-\w])color:\s*(#0f0f0f|#000|#111|#0d0d0d|var\(--bg\))', 'color:var(--on-accent)', body)
            return m.group(1) + '{' + body + '}'
        p = re.sub(r'([^{}]+)\{([^{}]*)\}', fix_rule, p)
        for a, b in [('#c8f135', 'var(--accent)'), ('#C8F135', 'var(--accent)'), ('rgba(200,241,53,', 'rgba(var(--accent-rgb),'),
                     ('rgba(200, 241, 53,', 'rgba(var(--accent-rgb),'), ('#0f0f0f', 'var(--bg)'), ('#181818', 'var(--surface)'),
                     ('#212121', 'var(--surface2)'), ('#2a2a2a', 'var(--border)'), ('#f0ede6', 'var(--text)'), ('#5a5a5a', 'var(--muted)')]:
            p = p.replace(a, b)
        parts[i] = p
    return ''.join(parts)


def mask_scripts(html):
    return re.sub(r'(<script\b[^>]*>)(.*?)(</script>)', lambda m: m.group(1) + ' ' * len(m.group(2)) + m.group(3), html, flags=re.S)


def wrap_aside(html):
    """Put the tool in .tool-col and let .seo sit beside it on wide screens."""
    if 'class="tool-col"' in html or 'class="seo"' not in html:
        return html
    masked = mask_scripts(html)
    seo_at = masked.index('<div class="seo">')
    stack = []
    for m in re.finditer(r'<div\b[^>]*>|</div>', masked[:seo_at]):
        if m.group(0).startswith('</'):
            stack and stack.pop()
        else:
            stack.append(m)
    if not stack:
        return html
    parent = stack[-1]
    if not re.search(r'class="[^"]*\b(page|container)\b', parent.group(0)):
        return html  # only lay out the main page container side by side
    depth, close_at = 0, None
    for m in re.finditer(r'<div\b[^>]*>|</div>', masked[seo_at:]):
        depth += -1 if m.group(0).startswith('</') else 1
        if depth == 0:
            close_at = seo_at + m.end()
            break
    if close_at is None or not re.match(r'\s*</div>', masked[close_at:]):
        return html  # .seo is not the last child of its parent; leave layout alone
    tag = parent.group(0)
    new_tag = re.sub(r'class="([^"]*)"', lambda m: 'class="%s has-aside"' % m.group(1), tag, count=1) if 'class="' in tag else tag[:-1] + ' class="has-aside">'
    return (html[:parent.start()] + new_tag + '<div class="tool-col">' + html[parent.end():seo_at] + '</div>\n  ' + html[seo_at:])


def process_page(fname, v):
    p = os.path.join(ROOT, fname)
    html = open(p, encoding='utf-8').read()
    html = replace_block(html, 'head', head_html(v), lambda h, b: h.replace('</head>', b + '\n</head>', 1))
    html = replace_block(html, 'nav', nav_html(fname),
                         lambda h, b: re.sub(r'<nav class="topnav">.*?</nav>', lambda m: b, h, count=1, flags=re.S))
    d = disclaimer_for(fname)
    if d or '<!-- mtp:disclaimer -->' in html:
        html = replace_block(html, 'disclaimer', '<p class="mtp-disclaimer">%s</p>' % esc(d) if d else '',
                             lambda h, b: h.replace('<!-- mtp:footer -->', b + '\n<!-- mtp:footer -->', 1))
    html = replace_block(html, 'footer', footer_html(),
                         lambda h, b: re.sub(r'<footer class="site-footer">.*?</footer>', lambda m: b, h, count=1, flags=re.S))
    # one-time clean-ups (no-ops once applied)
    html = re.sub(r'(<style>)(.*?)(</style>)', lambda m: m.group(1) + map_colors(OLD_CSS_LINE.sub('', m.group(2))) + m.group(3), html, flags=re.S)
    html = re.sub(r'style="([^"]*)"', lambda m: 'style="%s"' % map_colors(m.group(1)), html)
    if fname not in PAGES and fname not in NO_ASIDE:
        html = wrap_aside(html)
    open(p, 'w', encoding='utf-8').write(html)


def card(t, pin=True):
    return ('<a href="/%s" class="tool-card" data-file="/%s"><div class="tool-icon" aria-hidden="true">%s</div>'
            '<div class="tool-name">%s</div><div class="tool-desc">%s</div><div class="tool-cta">Open tool →</div>%s</a>') % (
        t[0], t[0], esc(t[3]), esc(t[1]), esc(t[5]),
        ('<button class="mtp-pin" type="button" data-pin="/%s" aria-pressed="false" aria-label="Pin %s to My Pad">%s</button>' % (t[0], esc(t[1]), STAR_SVG)) if pin else '')


def home_html():
    feat = [t for f in FEATURED for t in TOOLS if t[0] == f]
    secs = ''
    for c in CATS:
        items = [t for t in TOOLS if c[0] in t[4]]
        secs += ('<section class="mtp-sec" aria-labelledby="h-%s"><div class="mtp-sec-head"><h2 id="h-%s">%s</h2><a href="/%s">All %s tools →</a></div>'
                 '<div class="tools-grid">%s</div></section>') % (c[0], c[0], esc(c[1]), c[2], esc(c[1].lower()), ''.join(card(t) for t in items))
    return ('<div class="tools-wrap">'
            '<div class="mtp-home-search"><label for="mtp-q" class="mtp-sr">Search tools</label>%s'
            '<input id="mtp-q" type="search" placeholder="Search %d tools: try “hecs”, “stmp duty” or “jsno”" autocomplete="off" spellcheck="false"/></div>'
            '<div id="mtp-results" hidden><div class="mtp-sec-head"><h2>Results</h2></div><div class="tools-grid" id="mtp-results-grid"></div>'
            '<p class="mtp-noresults" id="mtp-noresults" hidden>No tools match that. Try a shorter word, or <a href="https://github.com/game9151/mytoolpad/issues" rel="noopener">suggest a tool</a>.</p></div>'
            '<div id="mtp-browse">'
            '<section class="mtp-sec" id="mtp-mypad" hidden aria-labelledby="h-mypad"><div class="mtp-sec-head"><h2 id="h-mypad">My Pad</h2><span class="mtp-hint">Pinned and recent tools, saved on this device</span></div><div class="tools-grid" id="mtp-mypad-grid"></div></section>'
            '<section class="mtp-sec" aria-labelledby="h-pop"><div class="mtp-sec-head"><h2 id="h-pop">Popular right now</h2><span class="mtp-hint">Tap ☆ on any tool to pin it to My Pad</span></div><div class="tools-grid">%s</div></section>'
            '%s</div></div>') % (SEARCH_SVG, len(TOOLS), ''.join(card(t) for t in feat), secs)


def build_home(v):
    p = os.path.join(ROOT, 'index.html')
    html = open(p, encoding='utf-8').read()
    def fb(h, b):
        i = h.index('<div class="tools-wrap">')
        j = h.index('<!-- mtp:footer -->') if '<!-- mtp:footer -->' in h else h.index('<footer')
        return h[:i] + b + '\n\n' + h[j:]
    html = replace_block(html, 'home', home_html(), fb)
    items = [{'@type': 'ListItem', 'position': i + 1, 'name': t[1], 'url': SITE + '/' + t[0]} for i, t in enumerate(TOOLS)]
    ld = json.dumps({'@context': 'https://schema.org', '@type': 'ItemList', 'name': 'MyToolPad free online tools', 'itemListElement': items}, ensure_ascii=False)
    html = re.sub(r'<script type="application/ld\+json">\{"@context": "https://schema.org", "@type": "ItemList".*?</script>',
                  lambda m: '<script type="application/ld+json">' + ld + '</script>', html, count=1, flags=re.S)
    open(p, 'w', encoding='utf-8').write(html)


HUB_TPL = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{title} | Free, Private | MyToolPad</title>
<meta name="description" content="{intro}"/>
<link rel="canonical" href="{site}/{file}"/>
<meta name="robots" content="index, follow"/>
<meta name="theme-color" content="#0f0f0f"/>
<meta property="og:title" content="{title} | MyToolPad"/>
<meta property="og:description" content="{intro}"/>
<meta property="og:url" content="{site}/{file}"/>
<meta property="og:type" content="website"/>
<meta property="og:site_name" content="MyToolPad"/>
<meta property="og:image" content="{site}/og-image.png"/>
<meta name="twitter:card" content="summary"/>
<link rel="icon" type="image/svg+xml" href="/icons/icon.svg"/>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet"/>
<script type="application/ld+json">{ld}</script>
<script type="application/ld+json">{crumbs}</script>
<script defer src="/_vercel/insights/script.js"></script>
</head>
<body class="mtp-hub">
<!-- mtp:nav -->
<!-- /mtp:nav -->
<main class="mtp-hub-wrap">
  <p class="mtp-crumb"><a href="/">MyToolPad</a> / {label}</p>
  <h1>{title}</h1>
  <p class="mtp-hub-intro">{intro}</p>
  <div class="tools-grid">{cards}</div>
  <p class="mtp-hub-more">Looking for something else? Press <kbd>/</kbd> to search every tool, or browse {others}.</p>
</main>
<!-- mtp:footer -->
<!-- /mtp:footer -->
</body>
</html>
'''


def build_hubs():
    for c in CATS:
        items = [t for t in TOOLS if c[0] in t[4]]
        ld = {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': c[3], 'url': SITE + '/' + c[2], 'description': c[4],
              'mainEntity': {'@type': 'ItemList', 'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': t[1], 'url': SITE + '/' + t[0]} for i, t in enumerate(items)]}}
        crumbs = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'MyToolPad', 'item': SITE + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': c[3], 'item': SITE + '/' + c[2]}]}
        others = ', '.join('<a href="/%s">%s</a>' % (o[2], esc(o[1])) for o in CATS if o[0] != c[0])
        html = HUB_TPL.format(title=esc(c[3]), intro=esc(c[4]), site=SITE, file=c[2], label=esc(c[1]),
                              ld=json.dumps(ld, ensure_ascii=False), crumbs=json.dumps(crumbs, ensure_ascii=False),
                              cards=''.join(card(t) for t in items), others=others)
        p = os.path.join(ROOT, c[2])
        if os.path.exists(p):  # keep the file stable between builds; only refresh generated parts
            old = open(p, encoding='utf-8').read()
            if old.split('<!-- mtp:nav -->')[0] == html.split('<!-- mtp:nav -->')[0] and old.split('<!-- /mtp:nav -->')[1].split('<!-- mtp:footer -->')[0] == html.split('<!-- /mtp:nav -->')[1].split('<!-- mtp:footer -->')[0]:
                continue
        open(p, 'w', encoding='utf-8').write(html)


def build_sitemap():
    urls = [('', '1.0')] + [(c[2], '0.8') for c in CATS] + [(t[0], '0.9') for t in TOOLS] + [('about.html', '0.4'), ('privacy.html', '0.3')]
    old = open(os.path.join(ROOT, 'sitemap.xml'), encoding='utf-8').read() if os.path.exists(os.path.join(ROOT, 'sitemap.xml')) else ''
    def lastmod(u):
        m = re.search(r'<loc>%s</loc>\s*<lastmod>([^<]+)</lastmod>' % re.escape(SITE + '/' + u), old)
        return m.group(1) if m else TODAY
    body = ''.join('  <url>\n    <loc>%s/%s</loc>\n    <lastmod>%s</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>%s</priority>\n  </url>\n' % (SITE, u, lastmod(u), pr) for u, pr in urls)
    open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + '</urlset>\n')


def build_sw(v):
    files = ['/'] + ['/' + t[0] for t in TOOLS] + ['/' + c[2] for c in CATS] + ['/about.html', '/privacy.html', '/404.html',
             '/assets/site.css?v=' + v, '/assets/site.js?v=' + v, '/assets/tools.js?v=' + v, '/vendor/qrcode.min.js', '/icons/icon.svg']
    tpl = open(os.path.join(ROOT, 'assets/sw-template.js'), encoding='utf-8').read()
    open(os.path.join(ROOT, 'sw.js'), 'w', encoding='utf-8').write(
        '/* generated by build.py */\nconst VERSION="%s";\nconst PRECACHE=%s;\n' % (v, json.dumps(files)) + tpl)


def main():
    missing = [t[0] for t in TOOLS if not os.path.exists(os.path.join(ROOT, t[0]))]
    if missing:
        raise SystemExit('missing tool pages: %s' % missing)
    write_tools_js()
    build_hubs()
    v = asset_hash()
    for f in sorted(set([t[0] for t in TOOLS] + PAGES)):
        process_page(f, v)
    build_home(v)
    build_sitemap()
    build_sw(v)
    print('built %d tools, %d hubs, assets v=%s' % (len(TOOLS), len(CATS), v))


if __name__ == '__main__':
    main()
