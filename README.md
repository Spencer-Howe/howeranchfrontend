# thehoweranch.com (Astro)

The Howe Ranch marketing site, moved off Wix in October 2026. Every page keeps its Wix wording, photos and
**web address**, so Google rankings and old links carry over. Bookings stay on the separate booking app
(thehoweranchregistration.com).

- **Editing:** see `CLAUDE.md` (the rules Claude follows for non-developer edits). Pages are Markdown files in
  `src/content/pages/`; the menu and contact details are in `src/data/site.ts`.
- **Stack:** Astro 7 (static), self-hosted Jost + Poppins fonts (Wix used Futura + Poppins), sitemap, no
  JavaScript framework. Photos in `src/assets/photos/` are resized to WebP at several widths on build.

## Run it locally
Needs **Node 24 LTS** (Astro 7 needs 22.23+; `.nvmrc` says 24).
```
npm install
npm run dev            # http://localhost:4321, live reload (add -- --background to keep it running)
npm run check          # full build + checks every internal link, photo and document
npm run photos         # after adding photos: shrink big ones, web-safe names, flag iPhone HEIC files
npm run check-links -- --external   # also check links to other websites
```
On Spencer's Linux machine Node 24 lives in `~/.local/node/node-v24.22.1-linux-x64/bin` (system Node is 22.22).

## Publish on Cloudflare Pages (one-time setup)
1. Push this folder to a GitHub repo (public is fine: it's a public website; on a free GitHub plan only public
   repos get branch protection).
2. Cloudflare dashboard > Workers & Pages > Create > Pages > Connect to Git > pick the repo.
   - Project name: **howeranch-site** (the booking app's contact-form permission expects previews on
     `*.howeranch-site.pages.dev`)
   - Framework preset: Astro · Build command: `npm run build` · Output directory: `dist`
   - Environment variable: `NODE_VERSION` = `24`
3. Every push to `main` goes live; other branches get their own preview link.
4. First build takes about a minute (it makes ~1,400 photo sizes).

## The contact forms
Home and Our Animals have the same forms as on Wix. They post to the booking app
(`/api/website-message` in eventsales), which saves a **"Website message"** lead in Admin > Leads and emails
howeranchservices@gmail.com (reply goes straight to the sender). **That endpoint must be deployed on the booking
app before the forms work live.** To test against a local booking app:
`PUBLIC_CONTACT_ENDPOINT=http://localhost:5000/api/website-message npm run dev`.

## Switching the domain from Wix
1. Check where thehoweranch.com is registered. DNS is currently on Wix (ns12/ns13.wixdns.net), so it may have
   been bought through Wix; if so, start the transfer out early (it can take up to a week).
2. Add `www.thehoweranch.com` and `thehoweranch.com` as custom domains on the Cloudflare Pages project, and send
   the bare domain to www (the site's canonical address is https://www.thehoweranch.com).
3. Check every page on the real domain; then cancel Wix.
4. Google Search Console: add the site, submit `https://www.thehoweranch.com/sitemap-index.xml`.

## What changed from the Wix site
- **Same addresses** for every real page (yes, including `/about-5` and `/general-clean`; renaming would cost
  Google history). Dropped pages redirect (`public/_redirects`): `/about-3` (a duplicate of Weddings) ->
  /weddings; `/blank-page-1` and `/sitemap` -> home; `/book-online`, `/service-page/*`, `/booking-calendar/*`
  (empty Wix Bookings pages) -> the booking site.
- `/mini-moo-express` was a hidden page on Wix (live, not in Google); it's kept the same way (`hidden: true`).
- **Business details for Google** now say 215 Browns Gulch Rd, Kalispell, MT (Wix's settings still say
  22053 Highland Street, Wildomar, CA).
- **Footer phone:** (424) 219-4212 (the booking site's number). The Wix footer showed 951-249-3826.
- **Google descriptions** added to every page (Wix had almost none). They're drafts written from each page's own
  wording, marked "draft: review" in each file.
- **Menu** keeps every Wix menu item, grouped into dropdowns (About, Weddings, Winter Wonderland, Animals,
  Photos), plus a gold **Book Now** button to the booking site. "Site Map" is gone (the sitemap is automatic).
- Links to the old payment domains (thehoweranchpayment.com, and the dead thehoweranchpayments.com) now go
  straight to thehoweranchregistration.com.
- **Private Winter Wonderland** page: added a "Request Your Date Online" button to the booking site's new
  request page, next to the existing email BOOK button.
- Wix PDFs and documents (30) are hosted at their original `/_files/ugd/...` addresses.

## Content to review (wording kept exactly as on Wix)
- **Pages describing the former Wildomar, California property as current:** `what-s-happening` (Visitor
  Guide: Temecula wineries etc.), `booking-checklist`, `faq` (the older Events FAQ; the menu uses `faqs`),
  `events`, `general-clean-1` (Valley View Patio), `festival-and-ceromony`, `sand-pit-photos`,
  `dance-and-dining-areas`, `pool-rules`. Probably from the same era (no place names, worth a look):
  `stay-a-while`, `mother-s-day-retreat`, `farm-animal-camp`. Update, hide (`hidden: true`) or delete them
  (add a redirect when deleting).
- **Dead or blocked outside links:** the Swimply pool listing (`faq`) is gone (404). Peerspace listings
  (`booking-checklist`, `events`, `faq`, `petting-zoo-party`) refuse automated checks; check them by hand.
- **Three Mother's Day Retreat gallery photos** no longer exist on Wix (it refuses to serve them), so they're
  not in the gallery.
- "Baby Time!" at the very top of the home page is a text line from the Wix page; keep or delete.

## Folder map
```
src/content/pages/      one .md per page (path = web address)
src/assets/photos/      photos by page; shared/ = used on several pages
src/data/site.ts        menu, contact details, social links, booking/contact URLs
src/layouts/Base.astro  page shell: head tags, Google business details, header, footer, gallery lightbox
src/components/         Header, Footer, ContactForm
src/styles/global.css   colors, fonts, page styles
public/_files/ugd/      Wix documents at their original addresses
public/_redirects       old address -> new address
scripts/                check-links, prepare-photos, wix-import (one-time import, reference only)
```
