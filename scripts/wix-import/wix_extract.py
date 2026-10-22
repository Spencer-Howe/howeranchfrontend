"""Turn a rendered Wix page into ordered content blocks (JSON).

Blocks: {"t": "section"} | {"t": "rich", "html": ...} | {"t": "img", "id", "alt", "href"}
        {"t": "gallery", "items": [{"id","alt"}]} | {"t": "button", "label", "href"} | {"t": "text", "text"}
        {"t": "video", "src"}
Only the page body (PAGES_CONTAINER) is read; the header menu and footer are handled separately.
"""
import html
import json
import os
import re
import sys
from html.parser import HTMLParser

MEDIA = re.compile(r'static\.wixstatic\.com/media/([0-9a-f]{6}_[0-9a-f]{32}~mv2\.(?:jpe?g|png|webp|gif))', re.I)
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}
KEEP_INLINE = {'a', 'strong', 'b', 'em', 'i', 'u', 'br', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li'}


class Extract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []          # (tag, attrs)
        self.in_main = 0         # depth marker: index in stack where PAGES_CONTAINER opened
        self.skip_depth = None   # inside script/style/svg
        self.rich_depth = None   # inside a richTextElement: collect markup
        self.rich = []
        self.gallery_depth = None
        self.gallery = []
        self.button = None       # (depth, href, label parts)
        self.expand_depth = None
        self.expand = []
        self.blocks = []

    # helpers -------------------------------------------------------------
    def depth(self):
        return len(self.stack)

    def inside_main(self):
        return self.in_main and self.depth() >= self.in_main

    def link_href(self):
        for tag, a in reversed(self.stack):
            if tag == 'a' and a.get('href'):
                return a['href']
        return None

    def emit(self, block):
        if block['t'] == 'img':
            prev = self.blocks[-1] if self.blocks else None
            if prev and prev['t'] == 'img' and prev['id'] == block['id']:
                return
        self.blocks.append(block)

    # parser --------------------------------------------------------------
    def handle_starttag(self, tag, attrs):
        a = {k: (v or '') for k, v in attrs}
        if self.skip_depth is not None:
            if tag not in VOID:
                self.stack.append((tag, a))
            return
        if tag in ('script', 'style', 'svg', 'noscript', 'template'):
            self.skip_depth = self.depth()
            self.stack.append((tag, a))
            return
        if a.get('id') == 'PAGES_CONTAINER' and not self.in_main:
            self.in_main = self.depth() + 1
        main = self.inside_main() or a.get('id') == 'PAGES_CONTAINER'

        if main and self.rich_depth is not None:
            style = a.get('style', '')
            if tag in KEEP_INLINE:
                if tag == 'a':
                    self.rich.append(f'<a href="{html.escape(a.get("href", ""), quote=True)}">')
                elif tag == 'br':
                    self.rich.append('<br>')
                elif tag == 'span':
                    # keep text colour (Wix uses red for the important notices)
                    color = re.search(r'(?<![-\w])color:\s*(#[0-9a-fA-F]{6})', style)
                    if color:
                        self.rich.append(f'<span data-color="{color.group(1)}">')
                        a['_emitted'] = '1'
                else:
                    align = re.search(r'text-align:\s*(\w+)', style)
                    size = re.search(r'font-size:\s*(\d+)px', style)
                    extra = (f' data-align="{align.group(1)}"' if align else '') + (f' data-size="{size.group(1)}"' if size else '')
                    self.rich.append(f'<{tag}{extra}>')
            if tag not in VOID:
                self.stack.append((tag, a))
            return

        if main:
            testid = a.get('data-testid', '')
            cls = a.get('class', '')
            if tag == 'section':
                self.emit({'t': 'section'})
            if testid == 'richTextElement':
                self.rich_depth = self.depth()
                self.rich = []
            elif testid == 'ellipsis_text_viewer_root' and self.expand_depth is None:
                self.expand_depth = self.depth()
                self.expand = []
            elif (a.get('data-hook') in ('gallery-widget', 'pro-gallery-container') or 'pro-gallery' == a.get('id', '')[:11]
                  or (a.get('data-hook') == 'gallery-root')) and self.gallery_depth is None:
                self.gallery_depth = self.depth()
                self.gallery = []
            elif tag == 'a' and testid == 'linkElement' and self.button is None:
                self.button = [self.depth(), a.get('href', ''), [], False]
            elif tag == 'img':
                m = MEDIA.search(a.get('src', '') + ' ' + a.get('srcset', '') + ' ' + a.get('data-src', ''))
                w = a.get('width') or ''
                small = w.isdigit() and int(w) < 40
                if m and not small:
                    item = {'id': m.group(1), 'alt': html.unescape(a.get('alt', '')).strip()}
                    if self.gallery_depth is not None:
                        if not self.gallery or self.gallery[-1]['id'] != item['id']:
                            if item['id'] not in {g['id'] for g in self.gallery}:
                                self.gallery.append(item)
                    else:
                        if self.button is not None:
                            self.button[3] = True
                        href = self.link_href()
                        self.emit({'t': 'img', **item, 'href': href})
            elif tag == 'iframe':
                src = a.get('src') or a.get('data-src') or ''
                if 'youtube' in src or 'vimeo' in src:
                    self.emit({'t': 'video', 'src': src})
            elif tag == 'video':
                src = a.get('src', '')
                if src:
                    self.emit({'t': 'video', 'src': src})
        if tag not in VOID:
            self.stack.append((tag, a))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        # pop to matching tag
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                break
        else:
            return
        while len(self.stack) > i:
            t, a = self.stack.pop()
            d = len(self.stack)
            if self.skip_depth is not None and d == self.skip_depth:
                self.skip_depth = None
                continue
            if self.skip_depth is not None:
                continue
            if self.rich_depth is not None:
                if d == self.rich_depth:
                    markup = ''.join(self.rich).strip()
                    if re.sub(r'<[^>]+>|\s|​', '', markup):
                        self.emit({'t': 'rich', 'html': markup})
                    self.rich_depth = None
                elif t == 'span' and a.get('_emitted'):
                    self.rich.append('</span>')
                elif t in KEEP_INLINE and t not in ('span', 'br'):
                    self.rich.append(f'</{t}>')
                continue
            if self.expand_depth is not None and d == self.expand_depth:
                txt = ' '.join(''.join(self.expand).split())
                if txt:
                    self.emit({'t': 'text', 'text': txt})
                self.expand_depth = None
            if self.gallery_depth is not None and d == self.gallery_depth:
                if self.gallery:
                    self.emit({'t': 'gallery', 'items': self.gallery})
                self.gallery_depth = None
            if self.button is not None and d == self.button[0]:
                label = ' '.join(''.join(self.button[2]).split())
                if label and not self.button[3]:
                    self.emit({'t': 'button', 'label': label, 'href': self.button[1]})
                self.button = None
            if self.in_main and d + 1 == self.in_main and t == 'div' and a.get('id') == 'PAGES_CONTAINER':
                self.in_main = 0

    def handle_data(self, data):
        if self.skip_depth is not None or not self.inside_main():
            return
        if self.rich_depth is not None:
            self.rich.append(html.escape(data, quote=False))
            return
        if self.expand_depth is not None:
            self.expand.append(data)
        if self.button is not None:
            self.button[2].append(data)


def main(src_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    summary = {}
    for f in sorted(os.listdir(src_dir)):
        p = Extract()
        p.feed(open(os.path.join(src_dir, f), encoding='utf-8', errors='replace').read())
        blocks = p.blocks
        # drop a leading/trailing run of section markers and collapse repeats
        cleaned = []
        for b in blocks:
            if b['t'] == 'section' and (not cleaned or cleaned[-1]['t'] == 'section'):
                continue
            cleaned.append(b)
        while cleaned and cleaned[-1]['t'] == 'section':
            cleaned.pop()
        name = f[:-5]
        json.dump(cleaned, open(os.path.join(out_dir, name + '.json'), 'w'), indent=1, ensure_ascii=False)
        kinds = {}
        for b in cleaned:
            kinds[b['t']] = kinds.get(b['t'], 0) + 1
        imgs = sum(1 for b in cleaned if b['t'] == 'img') + sum(len(b['items']) for b in cleaned if b['t'] == 'gallery')
        summary[name] = (kinds, imgs)
    for k, (kinds, imgs) in summary.items():
        print(f'{k:<34} photos={imgs:<4} {kinds}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
