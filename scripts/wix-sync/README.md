# What changed on Wix? (`wix_changes.py`)

While the Wix site is still live, people keep editing it. This script reads every page of the live Wix site and
lists everything that's different from this Astro site, with where each difference came from. **It never edits
the site**; it writes a report you (or Claude) use to copy the changes over.

## Run it
From the site folder (needs Python 3, nothing to install):
```
python3 scripts/wix-sync/wix_changes.py
```
Takes about 15 seconds. Open `wix-changes/report.md`.

Only some pages: `python3 scripts/wix-sync/wix_changes.py --page weddings --page /` (`/` is the home page).

Then, to have Claude apply them: *"Read wix-changes/report.md and copy the new Wix changes into the site."*

When everything has been copied over it says **"Everything matches"**.

## Keeping the backup up to date
1. Run it. 2. Ask Claude: *"Apply wix-changes/report.md."* 3. Run it again until it says "Everything matches".
4. `npm run check`, then save and publish.

Something that's fine as it is (e.g. a photo that's broken on Wix itself): add its 12-letter id from the report
to `known-differences.txt` with the reason. It's then listed under "Known and accepted" and doesn't count.

## What it checks
| | |
|---|---|
| **pages** | new pages on Wix (its sitemap plus every link to the site it finds, so hidden pages count), pages deleted on Wix |
| **wording** | word by word. Bold/italic and how paragraphs are split are ignored, so only real wording changes show |
| **spacing** | words run together on Astro ("scheduledat"): a space the import lost next to bold or red text |
| **buttons** | new, removed, renamed or re-linked buttons |
| **links** | links inside the text that differ |
| **photos** | new Wix photos (with a download link; it says if Wix refuses to serve one), photos Wix removed |
| **documents** | PDFs/Word files Wix links to that aren't in `public/_files/ugd/` yet |
| **title** | the page name in the browser tab |
| **menu** | the header menu, against `src/data/site.ts` |

Links are rewritten the same way the import did (`https://www.thehoweranch.com/weddings` → `/weddings`, old
payment sites → the booking site, dropped pages → their redirect from `public/_redirects`), so on-purpose
differences don't show up.

## The report
- **Where each item came from:** the Wix page address plus the spot on it (`text box 3, paragraph 12`,
  `gallery 50, photo 4`, `button 11`, counted from the top), and the Astro file and line it belongs in.
- **New since the last run** vs **still different**: each run remembers what it already reported
  (`wix-changes/state.json`), so new Wix edits stand out. Delete `state.json` to start fresh.
- `wix-changes/report.json`: the same list for scripts. `wix-changes/wix/<page>.json`: Wix's full page content.
- The report has an **AI notes** section telling Claude how to apply each kind of change (keep the wording
  exactly, where photos and documents go, check `git log` before removing something that's "only on Astro").

Not compared (on purpose): bold/italic/colors, photo descriptions and order, the footer, the contact forms, and
typography (the site shows ’ for ' and – for --).

`wix-changes/` isn't saved with the site (it's in `.gitignore`).

## How it works
Wix sends the whole page content in its HTML, so a plain download works (no browser needed). Each page goes
through the same parser the original import used (`scripts/wix-import/wix_extract.py`). Imported photo file
names end in 6 characters of the Wix photo id (`barn-sunset-4fa7d8.jpg`), which is how photos are matched.
Photos added later by hand don't have that, so they're never reported as removed.
