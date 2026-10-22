# One-time import from Wix (October 2026) — kept for reference

These Python scripts copied thehoweranch.com off Wix. **Don't re-run them on this site:** `wix_to_md.py`
rewrites every page in `src/content/pages/` and would erase edits made since.

1. `wix_inventory.py PAGES_DIR OUT.json` — title, word count, photos and forms per downloaded Wix page.
2. `wix_extract.py RENDERED_DIR BLOCKS_DIR` — each page (saved from Chrome after JavaScript ran:
   `google-chrome --headless=new --virtual-time-budget=20000 --dump-dom URL`) -> ordered blocks: text with its
   alignment/size/color, photos, galleries, buttons.
3. `wix_photos.py BLOCKS_DIR src/assets/photos MANIFEST.json` — downloads each photo (up to 2000px) into a
   folder per page (`shared/` when used on several pages).
4. `wix_normalize.py MANIFEST.json src/assets/photos` — one web-ready file per photo (1600px max, JPEG, or
   WebP for real cut-outs). Safe to re-run; never re-compresses a finished photo.
5. `wix_to_md.py BLOCKS_DIR MANIFEST.json INVENTORY.json .` — one Markdown page per Wix page, same address;
   Wix links rewritten (own pages -> `/page`, old payment domains -> the booking site, dropped pages -> their
   redirect), Wix documents linked at their original `/_files/ugd/...` addresses.

Documents were downloaded separately into `public/_files/ugd/` at the same paths Wix used.
