"""Make the downloaded photos web-ready, safe to run again: every photo ends up as ONE file, at most
1600px, JPEG (or WebP when it has real transparency). The manifest is rewritten to match the
files, and anything in the photos folder that no page uses is deleted.
Usage: wix_normalize.py MANIFEST PHOTOS_DIR"""
import json
import os
import sys

from PIL import Image, ImageOps

MANIFEST, ROOT = sys.argv[1], sys.argv[2]
man = json.load(open(MANIFEST))
MAX = 1600


def stem(rel):
    return rel.rsplit('.', 1)[0]


def candidates(rel):
    s = stem(rel)
    return [s + ext for ext in ('.jpg', '.webp', '.png', '.jpeg', '.gif')]


def transparent(im):
    if im.mode not in ('RGBA', 'LA', 'P'):
        return False
    alpha = im.convert('RGBA').getchannel('A').histogram()
    return alpha[255] / sum(alpha) < 0.995      # real cut-outs, not a stray edge pixel


keep = set()
changed = 0
for mid, rel in list(man['photos'].items()):
    files = [c for c in candidates(rel) if os.path.exists(os.path.join(ROOT, c))]
    if not files:
        print('missing on disk:', rel)
        del man['photos'][mid]
        continue
    # Prefer an already-processed file; otherwise the freshly downloaded one
    done = [f for f in files if f.endswith(('.jpg', '.webp'))]
    src = done[0] if done else files[0]
    im = ImageOps.exif_transpose(Image.open(os.path.join(ROOT, src)))
    alpha = transparent(im)
    out = stem(rel) + ('.webp' if alpha else '.jpg')
    # Finished files (right format and size) are never re-compressed: each pass would lose quality
    needs = src != out or max(im.size) > MAX
    if needs:
        im.thumbnail((MAX, MAX), Image.LANCZOS)
        if alpha:
            im.save(os.path.join(ROOT, out), 'WEBP', quality=85, method=6)
        else:
            im.convert('RGB').save(os.path.join(ROOT, out), 'JPEG', quality=78, optimize=True, progressive=True)
        changed += 1
    for f in files:
        if f != out:
            os.remove(os.path.join(ROOT, f))
    man['photos'][mid] = out
    keep.add(out)

stray = 0
for d, _, fs in os.walk(ROOT):
    for f in fs:
        rel = os.path.relpath(os.path.join(d, f), ROOT)
        if rel not in keep:
            os.remove(os.path.join(d, f))
            stray += 1
for d, ds, fs in os.walk(ROOT, topdown=False):
    if not os.listdir(d):
        os.rmdir(d)
json.dump(man, open(MANIFEST, 'w'), indent=1)
size = sum(os.path.getsize(os.path.join(ROOT, k)) for k in keep)
print(f'{len(keep)} photos, {size / 1e6:.0f} MB; processed {changed}; removed {stray} stray files')
