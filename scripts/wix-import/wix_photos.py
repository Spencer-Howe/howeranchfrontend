"""Download the photos the kept Wix pages use into <site>/src/assets/photos/<page>/ and write a
manifest (media id -> path relative to src/assets/photos)."""
import collections
import concurrent.futures as cf
import json
import os
import re
import sys
import urllib.request

BLOCKS, DEST, MANIFEST = sys.argv[1], sys.argv[2], sys.argv[3]
KEEP = ['home', 'about-5', 'animals', 'animals__availableminimoos', 'booking-checklist',
        'bookwinterwonderlandcelebration', 'dance-and-dining-areas', 'events', 'faq', 'faqs', 'farm-animal-camp',
        'festival-and-ceromony', 'general-4', 'general-clean', 'general-clean-1', 'media', 'microwedding',
        'mother-s-day-retreat', 'opportunities', 'petting-zoo-party', 'photos', 'pool-rules', 'reviews',
        'sand-pit-photos', 'stay-a-while', 'weddings', 'what-s-happening', 'winterwonderland', 'mini-moo-express']
GENERIC = re.compile(r'^(img|image|dsc|pxl|photo|untitled|screenshot|copy|file|unnamed|\d|[a-z]{1,3}$)', re.I)

uses = collections.defaultdict(list)   # id -> [(page, alt)]
for page in KEEP:
    for b in json.load(open(os.path.join(BLOCKS, page + '.json'))):
        items = b['items'] if b['t'] == 'gallery' else [b] if b['t'] == 'img' else []
        for it in items:
            uses[it['id']].append((page, it.get('alt', '')))


def slug(text):
    text = re.sub(r'\.(jpe?g|png|webp|gif|heic)$', '', text, flags=re.I)
    text = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return text[:48].strip('-')


def folder(page):
    return page.replace('__', '-')


plan = {}
counters = collections.Counter()
for mid, where in uses.items():
    pages = sorted({p for p, _ in where})
    home = 'shared' if len(pages) > 1 else folder(pages[0])
    alt = next((a for _, a in where if a), '')
    base = slug(alt)
    if not base or GENERIC.match(base):
        counters[home] += 1
        base = f'{home}-{counters[home]}'
    ext = mid.rsplit('.', 1)[1].lower().replace('jpeg', 'jpg')
    plan[mid] = f'{home}/{base}-{mid[7:13]}.{ext}'


def fetch(item):
    mid, rel = item
    path = os.path.join(DEST, rel)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return mid, 'cached', os.path.getsize(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ext = rel.rsplit('.', 1)[1]
    data, last = None, None
    for url in (f'https://static.wixstatic.com/media/{mid}/v1/fit/w_2000,h_2000,q_88/photo.{ext}',
                f'https://static.wixstatic.com/media/{mid}'):  # resized, else the original
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            break
        except Exception as e:
            last = e
    if data is None:
        return mid, f'FAILED {last}', 0
    if not (data[:3] == b'\xff\xd8\xff' or data[:8] == b'\x89PNG\r\n\x1a\n' or data[:4] == b'RIFF' or data[:4] == b'GIF8'):
        return mid, 'NOT AN IMAGE', len(data)
    with open(path, 'wb') as f:
        f.write(data)
    return mid, 'ok', len(data)


bad = []
total = 0
with cf.ThreadPoolExecutor(8) as ex:
    for mid, status, size in ex.map(fetch, plan.items()):
        total += size
        if status not in ('ok', 'cached'):
            bad.append((mid, status))
json.dump({'photos': plan, 'pages': {mid: sorted({p for p, _ in w}) for mid, w in uses.items()}},
          open(MANIFEST, 'w'), indent=1)
print(f'{len(plan)} photos, {total / 1e6:.1f} MB, problems: {bad}')
print(collections.Counter(p.split('/')[0] for p in plan.values()).most_common())
