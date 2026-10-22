"""Write one Markdown file per kept Wix page into <site>/src/content/pages/, from the extracted
blocks and the photo manifest. Usage: wix_to_md.py BLOCKS_DIR MANIFEST INVENTORY SITE_DIR"""
import html
import json
import os
import re
import sys
from html.parser import HTMLParser

BLOCKS, MANIFEST, INVENTORY, SITE = sys.argv[1:5]
PAGES_DIR = os.path.join(SITE, 'src/content/pages')
PHOTOS = os.path.join(SITE, 'src/assets/photos')
man = json.load(open(MANIFEST))['photos']
titles = {r['page']: r['title'] for r in json.load(open(INVENTORY))}

# Wix page name -> content file (the file path is the page's address)
KEEP = {
    'home': 'index', 'about-5': 'about-5', 'animals': 'animals', 'animals__availableminimoos': 'animals/availableminimoos',
    'booking-checklist': 'booking-checklist', 'bookwinterwonderlandcelebration': 'bookwinterwonderlandcelebration',
    'dance-and-dining-areas': 'dance-and-dining-areas', 'events': 'events', 'faq': 'faq', 'faqs': 'faqs',
    'farm-animal-camp': 'farm-animal-camp', 'festival-and-ceromony': 'festival-and-ceromony', 'general-4': 'general-4',
    'general-clean': 'general-clean', 'general-clean-1': 'general-clean-1', 'media': 'media',
    'microwedding': 'microwedding', 'mother-s-day-retreat': 'mother-s-day-retreat', 'opportunities': 'opportunities',
    'petting-zoo-party': 'petting-zoo-party', 'photos': 'photos', 'pool-rules': 'pool-rules', 'reviews': 'reviews',
    'sand-pit-photos': 'sand-pit-photos', 'stay-a-while': 'stay-a-while', 'weddings': 'weddings',
    'what-s-happening': 'what-s-happening', 'winterwonderland': 'winterwonderland',
    'mini-moo-express': 'mini-moo-express',
}
TITLE_FIX = {'pool-rules': 'Pool Rules', 'home': 'Howe Ranch', 'mini-moo-express': 'Mini Moo Express'}
HIDDEN = {'mini-moo-express'}  # live but kept out of Google, as on Wix
FORMS = {'home': 'contact', 'animals': 'animals'}
DROPPED = {'/about-3': '/weddings', '/blank-page-1': '/', '/sitemap': '/',
           '/booking-calendar/service-name': 'https://thehoweranchregistration.com/',
           '/booking-calendar/service-name-1': 'https://thehoweranchregistration.com/',
           '/booking-calendar/service-name-2': 'https://thehoweranchregistration.com/',
           '/book-online': 'https://thehoweranchregistration.com/'}
BOOKING = 'https://thehoweranchregistration.com/'
# Wix's own pieces we replace (the contact form, the old footer line)
JUNK_TEXT = {'Thanks for submitting!', '951-249-3826', '©2021 by Howe Ranch', '© 2021 by Howe Ranch'}


def fix_link(href):
    href = (href or '').strip()
    if not href:
        return href
    # Wix sometimes nests a file-storage address inside its own: keep just the file
    nested = re.search(r'/_files/https?://[^/]+\.usrfiles\.com/(ugd/[A-Za-z0-9_]+\.\w+)', href)
    if nested:
        return '/_files/' + nested.group(1)
    if re.match(r'^https?://[^/]+\.usrfiles\.com/ugd/', href):
        return '/_files/' + href.split('.usrfiles.com/', 1)[1]
    h = re.sub(r'^https?://(www\.)?thehoweranch\.com', '', href, flags=re.I)
    if h != href:
        h = h or '/'
        h = h.split('?')[0].rstrip('/') or '/'
        return DROPPED.get(h, h)
    if re.match(r'^https?://(www\.)?thehoweranchpayments?\.com', href, re.I):
        rest = re.sub(r'^https?://(www\.)?thehoweranchpayments?\.com/?', '', href, flags=re.I)
        return BOOKING + rest
    if href.startswith('http://thehoweranchregistration.com'):
        return 'https://' + href[len('http://'):]
    return href


def clean_text(s):
    s = s.replace('​', '').replace('﻿', '').replace('\xa0', ' ')
    return re.sub(r'[ \t]+', ' ', s)


def esc(s):
    s = s.replace('\\', '\\\\').replace('*', '\\*').replace('`', '\\`').replace('<', '&lt;')
    s = re.sub(r'(?<!\w)_|_(?!\w)', r'\\_', s)
    s = s.replace('[', '\\[').replace(']', '\\]')
    return s


def is_red(hex_color):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return r >= 110 and g <= 80 and b <= 110 and r > g + 60


class RichToMd(HTMLParser):
    """Wix rich-text markup (p, h1-6, ul/ol/li, a, strong/em, br, coloured spans) -> Markdown blocks
    of (kind, text, align, size)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.cur = None        # [kind, parts, align, size]
        self.lists = []
        self.link = []
        self.spans = []
        self.block_attrs = (None, None)

    def start_block(self, kind, align=None, size=None):
        self.flush()
        self.cur = [kind, [], align, size]

    def flush(self):
        if self.cur:
            kind, parts, align, size = self.cur
            text = clean_text(''.join(parts)).strip()
            text = re.sub(r'\*\*\s*\*\*', '', text)
            text = re.sub(r'<span class="alert">\s*</span>', '', text)
            if re.sub(r'[\s*_]|<[^>]+>', '', text):
                self.out.append((kind, text, align, size))
            self.cur = None

    def add(self, s):
        if self.cur is None:
            self.cur = ['p', [], None, None]
        self.cur[1].append(s)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            size = int(a['data-size']) if (a.get('data-size') or '').isdigit() else None
            if self.cur and self.cur[0].startswith('li'):
                return
            self.start_block(tag, a.get('data-align'), size)
        elif tag in ('ul', 'ol'):
            self.flush()
            self.lists.append(tag)
        elif tag == 'li':
            kind = 'li-ol' if self.lists and self.lists[-1] == 'ol' else 'li-ul'
            self.start_block(kind)
        elif tag == 'br':
            self.add('  \n')
        elif tag == 'a':
            self.link.append(fix_link(a.get('href', '')))
            self.add('[')
        elif tag in ('strong', 'b'):
            self.add('**')
        elif tag in ('em', 'i'):
            self.add('*')
        elif tag == 'span':
            red = bool(a.get('data-color')) and is_red(a['data-color'])
            self.spans.append(red)
            if red:
                self.add('<span class="alert">')

    def handle_endtag(self, tag):
        if tag in ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'):
            if self.cur and (self.cur[0] == tag or (tag == 'li' and self.cur[0].startswith('li'))):
                self.flush()
        elif tag in ('ul', 'ol'):
            self.flush()
            if self.lists:
                self.lists.pop()
        elif tag == 'a':
            href = self.link.pop() if self.link else ''
            self.add(f']({href})' if href else ']')
        elif tag in ('strong', 'b'):
            self.add('**')
        elif tag in ('em', 'i'):
            self.add('*')
        elif tag == 'span':
            if self.spans and self.spans.pop():
                self.add('</span>')

    def handle_data(self, data):
        self.add(esc(data))

    def close(self):
        super().close()
        self.flush()
        return self.out


def tidy_inline(text):
    text = re.sub(r'\[\s*\]\([^)]*\)', '', text)
    text = re.sub(r'\[([^\]]+)\]\(\)', r'\1', text)
    return text.strip()


def heading_level(kind, size):
    """Wix often marks small lines as headings and shrinks them: go by the size actually shown."""
    level = int(kind[1])
    if size is None:
        return level
    if size <= 18:
        return None            # body-size text: a paragraph
    if size <= 24:
        return max(level, 3)
    return level


def convert_rich(markup, state):
    p = RichToMd()
    p.feed(markup)
    lines = []                 # (markdown, centered)
    for kind, text, align, size in p.close():
        text = tidy_inline(text)
        plain = re.sub(r'<[^>]+>|[*\\\[\]]|\(http[^)]*\)|\(/[^)]*\)', '', text).strip()
        if not plain or plain in JUNK_TEXT:
            continue
        center = align == 'center'
        if kind.startswith('h'):
            level = heading_level(kind, size)
            if level is None or len(plain) > 140:
                lines.append((text, center))
                continue
            if not state['h1']:
                level, state['h1'] = 1, True
            elif level == 1:
                level = 2
            lines.append(('#' * level + ' ' + text.replace('**', ''), center))
        elif kind == 'li-ul':
            lines.append(('- ' + text, False))
        elif kind == 'li-ol':
            lines.append(('1. ' + text, False))
        else:
            text = re.sub(r'^(\d+)\. ', r'\1\\. ', text)
            text = re.sub(r'^([#>+-]) ', r'\\\1 ', text)
            lines.append((text, center))
    # Centered runs go in a <div class="center">; lists stay tight
    md, i = [], 0
    while i < len(lines):
        line, center = lines[i]
        if center:
            run = []
            while i < len(lines) and lines[i][1]:
                run.append(lines[i][0])
                i += 1
            md.append('<div class="center">\n\n' + '\n\n'.join(run) + '\n\n</div>')
            continue
        if md and line.startswith(('- ', '1. ')) and md[-1].split('\n')[-1].startswith(('- ', '1. ')):
            md[-1] += '\n' + line
        else:
            md.append(line)
        i += 1
    return '\n\n'.join(md)


GENERIC_ALT = re.compile(r'^(img|image|dsc|pxl|photo|untitled|screenshot|copy|file|unnamed|\d|[a-z]{1,3}$|.{0,3}$)', re.I)


def alt_text(alt, page_title):
    a = clean_text(re.sub(r'\.(jpe?g|png|webp|gif|heic)$', '', alt or '', flags=re.I)).strip()
    a = re.sub(r'[_]+', ' ', a)
    if not a or GENERIC_ALT.match(a):
        return f'{page_title} at Howe Ranch'
    return a.replace('[', '').replace(']', '')


def img_md(item, rel_to, page_title, href=None):
    rel = man.get(item['id'])
    if not rel:
        return None
    path = os.path.relpath(os.path.join(PHOTOS, rel), rel_to)
    md = f'![{alt_text(item.get("alt"), page_title)}]({path})'
    if href:
        return f'[{md}]({fix_link(href)})'
    return md


def convert(page, target):
    blocks = json.load(open(os.path.join(BLOCKS, page + '.json')))
    title = TITLE_FIX.get(page) or re.sub(r'\s*\|\s*Howe Ranch\s*$', '', titles.get(page, page)).strip()
    md_path = os.path.join(PAGES_DIR, target + '.md')
    rel_to = os.path.dirname(md_path)
    state = {'h1': False}
    parts = []
    i = 0
    missing = 0
    while i < len(blocks):
        b = blocks[i]
        t = b['t']
        if t == 'section':
            if parts and parts[-1] != '---':
                parts.append('---')
        elif t == 'rich':
            md = convert_rich(b['html'], state)
            if md:
                parts.append(md)
        elif t == 'text':
            # Wix's expandable text box: the full text shows, so drop its "Read more" label
            txt = re.sub(r'\s*Read (more|less)\s*$', '', clean_text(b['text']), flags=re.I)
            parts.append(esc(txt))
        elif t == 'img':
            run = []
            while i < len(blocks) and blocks[i]['t'] == 'img':
                m = img_md(blocks[i], rel_to, title, blocks[i].get('href'))
                if m:
                    run.append(m)
                else:
                    missing += 1
                i += 1
            i -= 1
            if len(run) == 1:
                parts.append(run[0])
            elif run:
                parts.append('<div class="photo-row">\n\n' + '\n'.join(run) + '\n\n</div>')
        elif t == 'gallery':
            imgs = []
            for it in b['items']:
                m = img_md(it, rel_to, title)
                if m:
                    imgs.append(m)
                else:
                    missing += 1
            if imgs:
                parts.append('<div class="gallery">\n\n' + '\n'.join(imgs) + '\n\n</div>')
        elif t == 'button':
            run = []
            while i < len(blocks) and blocks[i]['t'] == 'button':
                bb = blocks[i]
                label = html.escape(clean_text(bb['label']).strip())
                run.append(f'<a class="button" href="{html.escape(fix_link(bb["href"]), quote=True)}">{label}</a>')
                i += 1
            i -= 1
            parts.append('<div class="buttons">\n' + '\n'.join(run) + '\n</div>')
        elif t == 'video':
            parts.append(f'<div class="video"><iframe src="{html.escape(b["src"], quote=True)}" loading="lazy" '
                         f'allowfullscreen title="Video"></iframe></div>')
        i += 1
    while parts and parts[-1] == '---':
        parts.pop()
    while parts and parts[0] == '---':
        parts.pop(0)
    front = ['---', f'title: {json.dumps(title, ensure_ascii=False)}',
             'description: ""  # what Google shows under the page name (see README)']
    if page in HIDDEN:
        front.append('hidden: true  # live, but kept out of Google and the sitemap')
    if page in FORMS:
        front.append(f'form: {FORMS[page]}  # adds the contact form at the bottom')
    front.append('---')
    os.makedirs(rel_to, exist_ok=True)
    body = '\n\n'.join(parts).strip() + '\n'
    body = re.sub(r'\n{3,}', '\n\n', body)
    open(md_path, 'w').write('\n'.join(front) + '\n\n' + body)
    words = len(re.sub(r'!\[[^\]]*\]\([^)]*\)|<[^>]+>|[#*\\]', ' ', body).split())
    imgs = body.count('![')
    return words, imgs, missing


if __name__ == '__main__':
    os.makedirs(PAGES_DIR, exist_ok=True)
    for page, target in KEEP.items():
        w, n, miss = convert(page, target)
        print(f'{target + ".md":<40} words={w:<5} photos={n:<3}{"  MISSING " + str(miss) if miss else ""}')
