"""Compare the live Wix site with this Astro site and report every difference, with where each one came from.

Read-only: it never edits a page. It writes a report a person (or Claude) uses to copy the changes over by hand.

Usage: python3 scripts/wix-sync/wix_changes.py [--page weddings --page /] [--out wix-changes] [--site URL]

What it checks, per page:
  pages     new pages on Wix (sitemap + every link to the site it finds), pages gone from Wix
  wording   word-by-word diff of the page text (paragraph splits and bold/italic are ignored)
  spacing   words run together on Astro (a space the import lost next to bold or red text)
  photos    Wix photos not on the Astro page (new ones get a download link), Astro photos Wix dropped
  buttons   added, removed or re-linked buttons
  links     links inside the text that changed
  documents PDFs/Word files Wix links to that aren't in public/_files/ugd yet
  title     the page name in the browser tab
  menu      the header menu (checked against src/data/site.ts)

Differences that are fine as they are go in scripts/wix-sync/known-differences.txt (id + reason); they're listed
separately and don't count. When nothing else is left the report says "Everything matches".

Each run remembers what it reported (OUT/state.json), so the report splits into "new since the last run" and
"still different". Wix's page content is saved to OUT/wix/<page>.json for reference.
"""
import argparse
import concurrent.futures as cf
import difflib
import fnmatch
import hashlib
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
SITE_DIR = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', 'wix-import'))
from wix_extract import Extract  # noqa: E402  (the parser the original import used)

PAGES_DIR = os.path.join(SITE_DIR, 'src/content/pages')
PHOTOS_DIR = os.path.join(SITE_DIR, 'src/assets/photos')
FILES_DIR = os.path.join(SITE_DIR, 'public/_files')
REDIRECTS = os.path.join(SITE_DIR, 'public/_redirects')
BOOKING = 'https://thehoweranchregistration.com/'
UA = 'Mozilla/5.0 (X11; Linux x86_64) HoweRanchChangeCheck/1.0'
# Wix's own pieces the Astro site replaces on purpose (contact form message, old footer line)
JUNK_TEXT = {'Thanks for submitting!', '951-249-3826', '©2021 by Howe Ranch', '© 2021 by Howe Ranch'}
# Page names the import set on purpose instead of Wix's (see wix_to_md.py TITLE_FIX)
TITLE_FIX = {'/': 'Howe Ranch', '/pool-rules': 'Pool Rules', '/mini-moo-express': 'Mini Moo Express'}
PHOTO_ID = re.compile(r'-([0-9a-f]{6})\.(?:jpe?g|png|webp|gif)$', re.I)


# --- fetching ------------------------------------------------------------------------------------------
def fetch(url):
    """(status, text). Wix serves the full page content without JavaScript, so no browser is needed."""
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, ''
    except Exception as e:  # network trouble: report it rather than crash the whole run
        return 0, str(e)


def head(url):
    req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def sitemap_paths(site):
    _, index = fetch(site + '/sitemap.xml')
    paths = set()
    for sub in re.findall(r'<loc>([^<]+)</loc>', index):
        if 'booking' in sub:          # Wix Bookings service pages: the booking app replaces them
            continue
        _, xml = fetch(sub)
        for loc in re.findall(r'<loc>([^<]+)</loc>', xml):
            paths.add(to_path(loc, site))
    return {p for p in paths if p}


def to_path(url, site):
    m = re.match(r'^https?://(?:www\.)?thehoweranch\.com(/[^?#]*)?', url, re.I)
    if not m:
        return None
    p = (m.group(1) or '/').rstrip('/') or '/'
    return p


# --- the Astro side ------------------------------------------------------------------------------------
def load_redirects():
    rules = []
    for line in open(REDIRECTS, encoding='utf-8'):
        parts = line.split()
        if len(parts) >= 2 and not line.lstrip().startswith('#'):
            rules.append((parts[0], parts[1]))
    return rules


def redirected(path, rules):
    for old, new in rules:
        if fnmatch.fnmatch(path, old) or path == old.rstrip('/'):
            return new
    return None


def local_pages():
    out = {}
    for root, _, files in os.walk(PAGES_DIR):
        for f in files:
            if f.endswith('.md'):
                rel = os.path.relpath(os.path.join(root, f), PAGES_DIR)[:-3].replace(os.sep, '/')
                out['/' if rel == 'index' else '/' + rel] = os.path.join(root, f)
    return out


def photo_index():
    """6-letter Wix photo id (in every imported file name) -> file path relative to the site."""
    out = {}
    for root, _, files in os.walk(PHOTOS_DIR):
        for f in files:
            m = PHOTO_ID.search(f)
            if m:
                out[m.group(1).lower()] = os.path.relpath(os.path.join(root, f), SITE_DIR)
    return out


def fix_link(href, rules):
    """The same rewrites the import made, so on-purpose differences don't show up (see wix_to_md.py)."""
    href = (href or '').strip()
    if not href:
        return href
    nested = re.search(r'/_files/https?://[^/]+\.usrfiles\.com/(ugd/[A-Za-z0-9_]+\.\w+)', href)
    if nested:
        return '/_files/' + nested.group(1)
    if re.match(r'^https?://[^/]+\.usrfiles\.com/ugd/', href):
        return '/_files/' + href.split('.usrfiles.com/', 1)[1]
    h = re.sub(r'^https?://(www\.)?thehoweranch\.com', '', href, flags=re.I)
    if h != href:
        h = h.split('?')[0].rstrip('/') or '/'
        return redirected(h, rules) or h
    if re.match(r'^https?://(www\.)?thehoweranchpayments?\.com', href, re.I):
        return BOOKING + re.sub(r'^https?://(www\.)?thehoweranchpayments?\.com/?', '', href, flags=re.I)
    if href.startswith('http://thehoweranchregistration.com'):
        return 'https://' + href[len('http://'):]
    return href


def clean(s):
    s = s.replace('​', '').replace('﻿', '').replace('\xa0', ' ')
    return ' '.join(s.split())


def md_inline(text):
    """A Markdown line -> (plain words, link targets)."""
    links = re.findall(r'(?<!!)\[(?:[^\]\\]|\\.)*\]\(([^)\s]+)\)', text)
    text = re.sub(r'(?<!!)\[((?:[^\]\\]|\\.)*)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('\\*', '\0').replace('*', '').replace('\0', '*')
    text = re.sub(r'\\(.)', r'\1', text)
    return clean(html.unescape(text)), links


def read_md(path):
    """The Astro page -> title, words [(word, line)], buttons [(label, href, line)], photos [(file, line)], links."""
    lines = open(path, encoding='utf-8').read().split('\n')
    title, start = '', 0
    if lines and lines[0].strip() == '---':
        end = lines.index('---', 1)
        for ln in lines[1:end]:
            m = re.match(r'title:\s*"?(.*?)"?\s*$', ln)
            if m:
                title = m.group(1)
        start = end + 1
    words, buttons, photos, links = [], [], [], []
    for n, line in enumerate(lines[start:], start + 1):
        s = line.strip()
        for href, label in re.findall(r'<a class="button[^"]*" href="([^"]*)"[^>]*>(.*?)</a>', s):
            buttons.append((clean(html.unescape(label)), href, n))
        for f in re.findall(r'!\[[^\]]*\]\(([^)]+)\)', s):
            photos.append((f, n))
        if not s or s == '---' or '<a class="button' in s or s.startswith('!['):
            continue
        if s.startswith('[!['):     # a photo that's also a link
            links += re.findall(r'\]\((https?://[^)]+|/[^)]*)\)$', s)
            continue
        s = re.sub(r'^#{1,6}\s+', '', s)
        s = re.sub(r'^(?:[-*]|\d+\.)\s+', '', s)
        text, ls = md_inline(s)
        links += ls
        words += [(w, n) for w in text.split()]
    return title, words, buttons, photos, links


# --- the Wix side --------------------------------------------------------------------------------------
class RichText(HTMLParser):
    """Wix rich-text markup -> paragraphs [(kind, text)] and the links inside it."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.paras, self.links, self.cur = [], [], None
        self.link = None       # [href, text] of the link being read

    def flush(self):
        if self.cur:
            text = clean(''.join(self.cur[1]))
            if text and text not in JUNK_TEXT:
                self.paras.append((self.cur[0], text))
        self.cur = None

    def handle_starttag(self, tag, attrs):
        if tag in ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'):
            if not (self.cur and self.cur[0] == 'li' and tag == 'p'):
                self.flush()
                self.cur = [tag, []]
        elif tag == 'br' and self.cur:
            self.cur[1].append(' ')
        elif tag == 'a':
            self.link = [dict(attrs).get('href', ''), '']

    def handle_endtag(self, tag):
        if tag in ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'):
            self.flush()
        elif tag == 'a' and self.link:
            if clean(self.link[1]):      # Wix leaves invisible empty links behind; visitors can't see or click them
                self.links.append(self.link[0])
            self.link = None

    def handle_data(self, d):
        if self.link:
            self.link[1] += d
        if self.cur is None:
            self.cur = ['p', []]
        self.cur[1].append(d)

    def close(self):
        super().close()
        self.flush()


KIND = {'p': 'paragraph', 'li': 'list item', 'h1': 'heading', 'h2': 'heading', 'h3': 'heading',
        'h4': 'heading', 'h5': 'heading', 'h6': 'heading'}


def read_wix(raw, rules):
    p = Extract()
    p.feed(raw)
    title = clean(html.unescape((re.search(r'<title>([^<]*)', raw) or [None, ''])[1]))
    title = re.sub(r'\s*\|\s*Howe Ranch\s*$', '', title)
    words, buttons, photos, links, videos = [], [], [], [], []
    para_no = 0
    for i, b in enumerate(p.blocks, 1):
        if b['t'] == 'rich':
            r = RichText()
            r.feed(b['html'])
            r.close()
            links += [fix_link(h, rules) for h in r.links]
            for kind, text in r.paras:
                para_no += 1
                where = f'text box {i}, {KIND.get(kind, kind)} {para_no}'
                words += [(w, where, text) for w in text.split()]
        elif b['t'] == 'text' and clean(b['text']) not in JUNK_TEXT:
            para_no += 1
            text = clean(b['text'])
            words += [(w, f'text {i}', text) for w in text.split()]
        elif b['t'] == 'button':
            buttons.append((clean(b['label']), fix_link(b['href'], rules), f'button {i}'))
        elif b['t'] == 'img':
            photos.append((b['id'], b.get('alt', ''), f'photo {i}'))
            if b.get('href'):
                links.append(fix_link(b['href'], rules))
        elif b['t'] == 'gallery':
            photos += [(it['id'], it.get('alt', ''), f'gallery {i}, photo {k}') for k, it in enumerate(b['items'], 1)]
        elif b['t'] == 'video':
            videos.append(b['src'])
    site_links = set(re.findall(r'href="(https?://(?:www\.)?thehoweranch\.com/[^"#?]*)', raw))
    return dict(title=title, words=words, buttons=buttons, photos=photos, links=links, videos=videos,
                site_links=site_links, blocks=p.blocks)


# --- comparing -----------------------------------------------------------------------------------------
def snippet(words, i, j, ctx=6):
    before = ' '.join(words[max(0, i - ctx):i])
    after = ' '.join(words[j:j + ctx])
    return before, after


def diff_words(wix, md):
    """Word-level differences, merged into readable chunks with a few words of context."""
    a, b = [w for w, *_ in wix], [w for w, _ in md]
    ops = [o for o in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if o[0] != 'equal']
    chunks = []
    for op in ops:   # merge changes separated by 3 words or fewer
        if chunks and op[1] - chunks[-1][2] <= 3 and op[3] - chunks[-1][4] <= 3:
            c = chunks[-1]
            chunks[-1] = ('replace', c[1], op[2], c[3], op[4])
        else:
            chunks.append(op)
    out = []
    for tag, i1, i2, j1, j2 in chunks:
        before, after = snippet(a, i1, i2)
        wix_loc = wix[min(i1, len(wix) - 1)][1] if wix else ''
        wix_para = wix[min(i1, len(wix) - 1)][2] if wix else ''
        md_line = md[min(j1, len(md) - 1)][1] if md else None
        out.append(dict(kind={'insert': 'only-astro', 'delete': 'new-on-wix'}.get(tag, 'changed'),
                        wix=' '.join(a[i1:i2]), astro=' '.join(b[j1:j2]), before=before, after=after,
                        wix_where=wix_loc, wix_paragraph=wix_para, line=md_line))
    return out


def compare_page(path, url, wix, md_file, photos_by_id):
    items = []
    rel = os.path.relpath(md_file, SITE_DIR)

    def add(kind, summary, wix_where='', line=None, **extra):
        items.append(dict(page=path, kind=kind, summary=summary, wix_url=url, wix_where=wix_where,
                          astro_file=rel + (f':{line}' if line else ''), **extra))

    title, md_words, md_buttons, md_photos, md_links = read_md(md_file)
    want_title = TITLE_FIX.get(path, wix['title'])
    if wix['title'] and title != want_title:
        add('title', f'Page name: Wix says "{wix["title"]}", Astro says "{title}"', 'the page\'s <title>', 2,
            wix_text=wix['title'], astro_text=title)

    for d in diff_words(wix['words'], md_words):
        if d['kind'] == 'changed' and d['wix'].replace(' ', '') == d['astro'].replace(' ', ''):
            add('spacing', f'Missing or extra space on Astro: Wix "{d["wix"]}" / Astro "{d["astro"]}" (usually a '
                f'space lost next to bold or red text)', d['wix_where'], d['line'], wix_text=d['wix'],
                astro_text=d['astro'], context=f'...{d["before"]} [ ] {d["after"]}...')
            continue
        if d['kind'] == 'new-on-wix':
            s = f'Wix has new words: "{d["wix"]}"'
        elif d['kind'] == 'only-astro':
            s = f'Astro has words Wix no longer has: "{d["astro"]}"'
        else:
            s = f'Wording changed: Wix "{d["wix"]}" / Astro "{d["astro"]}"'
        add('wording', s, d['wix_where'], d['line'], wix_text=d['wix'], astro_text=d['astro'],
            context=f'...{d["before"]} [ ] {d["after"]}...', wix_paragraph=d['wix_paragraph'])

    # buttons: match by label first, then by link
    left = list(md_buttons)
    for label, href, where in wix['buttons']:
        hit = next((m for m in left if m[0] == label and m[1] == href), None) or \
            next((m for m in left if m[0] == label), None) or next((m for m in left if m[1] == href), None)
        if hit:
            left.remove(hit)
            if hit[1] != href:
                add('button', f'Button "{label}" now links to {href} (Astro: {hit[1]})', where, hit[2],
                    wix_text=href, astro_text=hit[1])
            elif hit[0] != label:
                add('button', f'Button to {href} renamed "{label}" (Astro: "{hit[0]}")', where, hit[2],
                    wix_text=label, astro_text=hit[0])
        else:
            add('button', f'New button on Wix: "{label}" -> {href}', where, wix_text=f'{label} -> {href}')
    for label, href, line in left:
        add('button', f'Button only on Astro: "{label}" -> {href} (deleted on Wix, or added on purpose)', '', line,
            astro_text=f'{label} -> {href}')

    # links inside the text
    md_set = set(md_links)
    for h in sorted(set(wix['links']) - md_set):
        if h:
            add('link', f'Link on Wix not on the Astro page: {h}', 'a link in the text', wix_text=h)

    # photos: imported files keep 6 letters of the Wix photo id in their name
    on_page = {}
    for f, line in md_photos:
        m = PHOTO_ID.search(f)
        if m:
            on_page[m.group(1).lower()] = (f, line)
    wix_ids = set()
    for mid, alt, where in wix['photos']:
        short = mid[7:13].lower()
        wix_ids.add(short)
        if short in on_page:
            continue
        name = alt or mid
        if short in photos_by_id:
            add('photo', f'Wix shows photo "{name}" here; it\'s already in the repo ({photos_by_id[short]}) but not on '
                f'this page', where, wix_text=name, file=photos_by_id[short])
        else:
            url_ = f'https://static.wixstatic.com/media/{mid}'
            status = head(url_)
            dead = '' if status == 200 else f' (Wix refuses to serve it: {status or "no answer"}; it can\'t be copied)'
            add('photo', f'New photo on Wix: "{name}"{dead}', where, wix_text=name, download=url_)
    for short, (f, line) in on_page.items():
        if short not in wix_ids:
            add('photo', f'Photo on Astro that Wix no longer shows: {os.path.basename(f)}', '', line,
                astro_text=os.path.basename(f))

    # documents (PDF, Word...) Wix links to that aren't downloaded yet
    for h in sorted({h for h in wix['links'] + [b[1] for b in wix['buttons']] if h.startswith('/_files/')}):
        if not os.path.exists(os.path.join(FILES_DIR, h[len('/_files/'):])):
            add('document', f'New document on Wix: {h}', 'a link or button', wix_text=h,
                download='https://www.thehoweranch.com' + h)
    for v in wix['videos']:
        if v not in open(md_file, encoding='utf-8').read():
            add('video', f'Video on Wix not on Astro: {v}', 'a video', wix_text=v)
    return items


def wix_menu(raw, rules):
    """The Wix header menu -> [(label, address)], skipping items that now redirect elsewhere (like Site Map)."""
    head = raw[raw.find('id="SITE_HEADER"'):raw.find('id="PAGES_CONTAINER"')]
    out = []
    for href, inner in re.findall(r'<a [^>]*href="([^"]*)"[^>]*>(.*?)</a>', head, re.S):
        label = clean(html.unescape(re.sub(r'<[^>]+>', '', inner)))
        path = to_path(href, '')
        if label and path and not redirected(path, rules) and (label, path) not in out:
            out.append((label, path))
    return out


def compare_menu(raw, rules, url):
    site_ts = os.path.join(SITE_DIR, 'src/data/site.ts')
    text = open(site_ts, encoding='utf-8').read()
    ours = re.findall(r"label: '((?:[^'\\]|\\.)*)', href: '([^']*)'", text)
    items = []
    for label, path in wix_menu(raw, rules):
        if (label, path) in ours:
            continue
        same = [l for l, h in ours if h == path]
        summary = (f'Menu item for {path} is called "{label}" on Wix, "{same[0]}" on Astro' if same else
                   f'New menu item on Wix: "{label}" -> {path}')
        items.append(dict(page='(menu)', kind='menu', summary=summary, wix_url=url, wix_where='the header menu',
                          astro_file='src/data/site.ts', wix_text=f'{label} -> {path}'))
    wix_paths = {p for _, p in wix_menu(raw, rules)}
    for label, path in ours:
        if path.startswith('/') and path not in wix_paths:
            items.append(dict(page='(menu)', kind='menu', summary=f'Menu item only on Astro: "{label}" -> {path}',
                              wix_url=url, wix_where='the header menu', astro_file='src/data/site.ts',
                              astro_text=f'{label} -> {path}'))
    return items


def load_known():
    """scripts/wix-sync/known-differences.txt: ids of differences that are fine as they are (one per line, # reason)."""
    path = os.path.join(HERE, 'known-differences.txt')
    known = {}
    if os.path.exists(path):
        for line in open(path, encoding='utf-8'):
            m = re.match(r'\s*([0-9a-f]{12})\b\s*(?:#\s*(.*))?', line)
            if m:
                known[m.group(1)] = (m.group(2) or '').strip()
    return known


def item_id(it):
    key = '|'.join(str(it.get(k, '')) for k in ('page', 'kind', 'wix_text', 'astro_text', 'summary'))
    return hashlib.sha1(key.encode()).hexdigest()[:12]


# --- report --------------------------------------------------------------------------------------------
AI_NOTES = """## AI notes: how to use this report

- **Where things came from.** Every item says which live Wix page and which part of it (`text box 3, paragraph 12`
  counts the page's text boxes, photos and buttons from the top) and where it goes in this site (`file:line`).
  Wix's full page content is saved in `{out}/wix/<page>.json` if more context is needed.
- **"New on Wix"** = Wix has it, Astro doesn't. **"Only on Astro"** = Astro has it, Wix doesn't: either it was
  deleted on Wix, or it was added to Astro on purpose (check `git log -p <file>` before removing anything).
- **Copy Wix's wording exactly** (CLAUDE.md: keep her wording). Bold/italic and how paragraphs are split are not
  compared, only the words.
- **Spacing** items are Astro mistakes from the import (a space lost next to bold or red text): add the space in
  the Astro file. Nothing changed on Wix.
- **Photos:** download the link given into `src/assets/photos/<page>/`, run `npm run photos`, then add it to the
  page with a real description. A photo marked "already in the repo" just needs adding to the page.
- **Documents:** download into `public/_files/ugd/` with the same file name; link as `/_files/ugd/<name>`.
- **Links** were already rewritten the way the import did it (Wix pages -> `/page`, old payment sites -> the
  booking site, dropped pages -> their redirect), so a link listed here is a real difference.
- **New pages:** create `src/content/pages/<address>.md` (title + description + content) and add it to the menu in
  `src/data/site.ts` if Wix's menu has it. Pages gone from Wix: hide or delete them, and add a redirect.
- Expected differences (not mistakes): the footer phone, the contact form, page descriptions, and anything listed
  in README.md "What changed from the Wix site".
"""


def write_report(out, items, new_ids, pages, notes, started, accepted):
    fresh = [it for it in items if it['id'] in new_ids]
    old = [it for it in items if it['id'] not in new_ids]
    L = [f'# Wix -> Astro changes, {started:%Y-%m-%d %H:%M}', '',
         f'Compared {len(pages)} pages of the live Wix site (https://www.thehoweranch.com) with this Astro site.', '',
         f'- **New since the last run:** {len(fresh)}', f'- **Still different (reported before):** {len(old)}',
         f'- **Known and accepted** (scripts/wix-sync/known-differences.txt): {len(accepted)}', '']
    if not items:
        L += ['**Everything matches.** The Astro site has every change made on Wix.', '']
    by_page = {}
    for it in items:
        by_page.setdefault(it['page'], []).append(it)
    L += ['| Page | New | Total | What |', '|---|---|---|---|']
    for p in sorted(by_page):
        its = by_page[p]
        kinds = sorted({i['kind'] for i in its})
        L.append(f'| `{p}` | {sum(i["id"] in new_ids for i in its)} | {len(its)} | {", ".join(kinds)} |')
    if notes:
        L += ['', '## Notes', ''] + [f'- {n}' for n in notes]
    shown = os.path.relpath(out, SITE_DIR) if out.startswith(SITE_DIR + os.sep) else out
    L += ['', AI_NOTES.format(out=shown)]
    for heading, group in (('New since the last run', fresh), ('Still different (reported before)', old)):
        L += [f'## {heading} ({len(group)})', '']
        if not group:
            L += ['Nothing.', '']
        page = None
        for it in sorted(group, key=lambda i: (i['page'], ['page', 'menu', 'title', 'wording', 'spacing', 'button', 'link', 'photo',
                                                           'document', 'video'].index(i['kind']))):
            if it['page'] != page:
                page = it['page']
                L += [f'### `{page}`', '']
            L.append(f'- **{it["kind"]}** `{it["id"]}`: {it["summary"]}')
            if it.get('context'):
                L.append(f'  - In context: {it["context"]}')
            src = f'{it["wix_url"]}' + (f' ({it["wix_where"]})' if it.get('wix_where') else '')
            L.append(f'  - From Wix: {src}')
            if it.get('wix_paragraph') and it['kind'] == 'wording':
                L.append(f'  - Wix paragraph now reads: "{it["wix_paragraph"]}"')
            if it.get('astro_file'):
                L.append(f'  - Astro: `{it["astro_file"]}`')
            if it.get('download'):
                L.append(f'  - Download: {it["download"]}')
        L.append('')
    if accepted:
        L += [f'## Known and accepted ({len(accepted)})', '']
        L += [f'- `{it["page"]}` `{it["id"]}`: {it["summary"]}. **Why it\'s fine:** {it["reason"]}' for it in accepted]
        L.append('')
    path = os.path.join(out, 'report.md')
    open(path, 'w', encoding='utf-8').write('\n'.join(L))
    json.dump(dict(run=started.isoformat(timespec='seconds'), items=items, accepted=accepted), open(os.path.join(out, 'report.json'), 'w'),
              indent=1, ensure_ascii=False)
    return path, len(fresh), len(old)


# --- main ----------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--site', default='https://www.thehoweranch.com', help='the live Wix site')
    ap.add_argument('--out', default=os.path.join(SITE_DIR, 'wix-changes'), help='where the report goes')
    ap.add_argument('--page', action='append', help='only check this page, e.g. --page weddings (repeatable)')
    args = ap.parse_args()
    site, out = args.site.rstrip('/'), os.path.abspath(args.out)
    os.makedirs(os.path.join(out, 'wix'), exist_ok=True)
    started = datetime.now()

    rules = load_redirects()
    local = local_pages()
    photos_by_id = photo_index()
    notes, items = [], []

    if args.page:
        wanted = {'/' + p.strip('/') if p.strip('/') else '/' for p in args.page}
        in_sitemap = set()
    else:
        print('Reading the Wix sitemap...')
        in_sitemap = sitemap_paths(site)
        wanted = in_sitemap | set(local)

    fetched, seen = {}, set()
    while wanted - seen:   # keep going while pages link to pages we haven't looked at
        batch = sorted(wanted - seen)
        seen |= set(batch)
        print(f'Fetching {len(batch)} page(s) from Wix...')
        with cf.ThreadPoolExecutor(6) as ex:
            for path, (status, raw) in zip(batch, ex.map(lambda p: fetch(site + (p if p != '/' else '/')), batch)):
                fetched[path] = (status, raw)
                if status == 200 and not args.page:
                    for link in re.findall(r'href="(https?://(?:www\.)?thehoweranch\.com/[^"#?]*)', raw):
                        p = to_path(html.unescape(link), site)
                        if p and not p.startswith('/_') and not re.search(r'\.\w{2,4}$', p):
                            wanted.add(p)

    for path in sorted(fetched):
        status, raw = fetched[path]
        url = site + (path if path != '/' else '/')
        target = redirected(path, rules)
        if status != 200:
            if path in local:
                if status in (404, 410):
                    items.append(dict(page=path, kind='page', summary=f'Page is gone from Wix ({status}) but still on '
                                      f'Astro', wix_url=url, wix_where='', astro_file=os.path.relpath(local[path], SITE_DIR)))
                else:
                    notes.append(f'Could not load {url} ({status or raw}); skipped it. Run again later.')
            continue
        if path not in local:
            if target:
                continue      # dropped on purpose; public/_redirects sends it elsewhere
            wix = read_wix(raw, rules)
            name = path.strip('/').replace('/', '__')
            json.dump(wix['blocks'], open(os.path.join(out, 'wix', name + '.json'), 'w'), indent=1, ensure_ascii=False)
            if not wix['words'] and not wix['photos']:
                continue     # an empty Wix system page
            where = 'in the sitemap' if path in in_sitemap else 'linked from another page, not in the sitemap'
            items.append(dict(page=path, kind='page', summary=f'New page on Wix ({where}): "{wix["title"]}", '
                              f'{len(wix["words"])} words, {len(wix["photos"])} photos, {len(wix["buttons"])} buttons',
                              wix_url=url, wix_where='whole page', astro_file=f'src/content/pages{path}.md (to create)',
                              wix_text=wix['title']))
            continue
        wix = read_wix(raw, rules)
        name = 'index' if path == '/' else path.strip('/').replace('/', '__')
        json.dump(wix['blocks'], open(os.path.join(out, 'wix', name + '.json'), 'w'), indent=1, ensure_ascii=False)
        if not wix['blocks']:
            notes.append(f'{url} loaded but had no page content (Wix changed its layout?). Check it by hand.')
            continue
        items += compare_page(path, url, wix, local[path], photos_by_id)
        if path == '/':
            items += compare_menu(raw, rules, url)

    for it in items:
        it['id'] = item_id(it)
    known = load_known()
    accepted = [dict(it, reason=known[it['id']]) for it in items if it['id'] in known]
    items = [it for it in items if it['id'] not in known]
    state_file = os.path.join(out, 'state.json')
    state = json.load(open(state_file)) if os.path.exists(state_file) else {'seen': {}}
    new_ids = {it['id'] for it in items if it['id'] not in state['seen']}
    for it in items:
        state['seen'].setdefault(it['id'], started.isoformat(timespec='seconds'))
    json.dump(state, open(state_file, 'w'), indent=1)

    path, n_new, n_old = write_report(out, items, new_ids, fetched, notes, started, accepted)
    if not items:
        print(f'\nEverything matches ({len(fetched)} pages checked, {len(accepted)} known difference(s) accepted).')
    else:
        print(f'\n{n_new} new difference(s), {n_old} reported before, {len(accepted)} known and accepted.')
    print(f'Report: {os.path.relpath(path, os.getcwd())}')
    for n in notes:
        print('Note:', n)


if __name__ == '__main__':
    main()
