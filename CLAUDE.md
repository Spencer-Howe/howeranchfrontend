# Howe Ranch website (thehoweranch.com)

## Who you're helping
The person editing this site runs Howe Ranch's marketing and is **not a developer**. She'll ask for changes in
plain English ("change the price on Weddings", "add these photos to Animals"). Work like a helpful web person:

- Explain in plain words. No jargon (say "save and publish", not "commit and push"). Keep replies short.
- **Keep her wording.** Only change text she asked you to change. Don't rewrite, "improve" or fix grammar unless asked.
- After every change, make sure the preview is running and give her the link to look at.
- **Never publish until she says so** ("publish", "make it live", "push it", "looks good, go").
- If something is confusing or risky, ask one short question instead of guessing.

## Where things are
| What | Where |
|---|---|
| Each page's words and photos | `src/content/pages/<page>.md`. The file's path is the page's web address: `weddings.md` is /weddings, `animals/availableminimoos.md` is /animals/availableminimoos, `index.md` is the home page. |
| Photos | `src/assets/photos/<page>/` (photos used on several pages are in `shared/`) |
| Menu, phone, email, address, social links | `src/data/site.ts` |
| Colors and fonts | `src/styles/global.css` |
| PDFs and documents | `public/_files/ugd/` (same addresses the old Wix site used, so old links keep working) |
| Old addresses that now point elsewhere | `public/_redirects` |

The booking site (thehoweranchregistration.com: checkout, bookings, admin) is a **different project**. Don't try
to change it from here; tell her it's in the booking app.

## The preview
Start it (it keeps running in the background):
```
npm run dev -- --background
```
Then give her **http://localhost:4321** plus the page, e.g. http://localhost:4321/weddings. Changes show within a
second or two. `npx astro dev status` / `npx astro dev stop` / `npx astro dev logs` manage it.

## How pages are written (Markdown)
Each page starts with settings between `---` lines:
```
---
title: "Weddings"               # browser tab and Google title
description: "..."              # the line Google shows under the title (under 160 characters)
form: contact                   # optional: adds the contact form at the bottom (contact or animals)
hidden: true                    # optional: page works but stays out of Google
---
```
Then the content:
- Headings: `# Big` (one per page, the first heading), `## Section`, `### Smaller`
- **Bold** `**text**`, *italic* `*text*`, links `[words](https://...)` or `[words](/weddings)`
- A photo: `![what the photo shows](../../assets/photos/weddings/barn-sunset.jpg)` (path is relative to the page
  file; pages inside `animals/` need one more `../`). Always write a real description in the `[...]`; it's what
  blind visitors and Google "see".
- A photo that's also a link: `[![description](../../assets/photos/...)](https://link)`
- A gallery (square thumbnails, tap to enlarge) or a row of photos side by side:
  ```
  <div class="gallery">

  ![...](../../assets/photos/...)
  ![...](../../assets/photos/...)

  </div>
  ```
  (use `class="photo-row"` for photos shown whole, side by side). Keep the blank lines.
- Buttons: `<div class="buttons">` with `<a class="button" href="...">Label</a>` inside (`class="button gold"`
  for the gold one).
- Centered text: wrap in `<div class="center">` ... `</div>` with blank lines inside, like the gallery.
- Red text: `<span class="alert">words</span>`
- `---` on its own line between paragraphs: a section break (small gold line).

## Adding photos
1. She puts the photos in the page's folder in `src/assets/photos/` (File Explorer is fine).
2. Run `npm run photos`. It shrinks big photos and makes the file names web-safe (it prints any renames).
3. If it lists **HEIC** files (iPhone): those can't be used. Tell her: open the photo in the Windows Photos app >
   "..." > Save as > JPG, then delete the HEIC. To stop it happening: iPhone Settings > Camera > Formats > Most
   Compatible.
4. Add them to the page, with a description of what each shows.

## Publishing (only when she says so)
1. `npm run check`: builds the whole site and checks every link, photo and document. **If it fails, stop**, fix
   it, and tell her what was wrong in plain words. Never publish a failing site.
2. Save it with a short plain description of what changed:
   `git add -A && git commit -m "Weddings: new price and barn photo"`
3. `git pull --rebase` (picks up anything Spencer changed), then `git push`.
4. Tell her it will be live at https://www.thehoweranch.com in about a minute.

If `git pull` reports a conflict (they both edited the same lines), sort it out, keeping both people's changes
where you can, and explain to her what happened in a sentence.

**Undo a published change:** find it with `git log --oneline`, then `git revert <id>` and push. Explain in plain
words what was undone. Never use `git push --force` or `git reset --hard`.

## Keeping it in step with Wix
Wix is still the main site; this one is kept as an up-to-date copy. To copy over what changed on Wix:
`python3 scripts/wix-sync/wix_changes.py`, then apply `wix-changes/report.md` (it says where each change came
from and where it goes), and run it again until it says "Everything matches". Details: `scripts/wix-sync/README.md`.

## Rules that protect the site
- Don't rename or delete a page file without adding a line to `public/_redirects` from the old address to the
  new one (old address  new address  301). Google and people's bookmarks use those addresses.
- Don't delete anything in `public/_files/`: emails and old posts link to those documents.
- Every page needs a `title`; keep `description` under 160 characters.
- Photos go in `src/assets/photos/`, not `public/` (only `src/assets` photos get resized for phones).
- Ask before adding new tools, packages or big structural changes; explain why in plain words.
