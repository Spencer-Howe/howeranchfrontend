// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import { readFileSync, readdirSync } from 'node:fs';

// Pages with `hidden: true` stay out of the sitemap (they're live, just not for Google)
const pagesDir = new URL('./src/content/pages/', import.meta.url);
const hidden = readdirSync(pagesDir, { recursive: true })
  .filter((f) => String(f).endsWith('.md'))
  .filter((f) => /^hidden:\s*true/m.test(readFileSync(new URL(String(f), pagesDir), 'utf8').split('\n---')[0]))
  .map((f) => '/' + String(f).replace(/\.md$/, '').replace(/^index$/, ''));

// https://astro.build/config
export default defineConfig({
  site: 'https://www.thehoweranch.com',
  // Same addresses as the Wix site (/weddings, not /weddings/): Cloudflare Pages serves
  // weddings.html at /weddings, so Google's existing links keep working.
  trailingSlash: 'never',
  build: { format: 'file' },
  integrations: [sitemap({ filter: (page) => !hidden.some((h) => new URL(page).pathname === h) })],
  image: {
    // Every photo gets sized versions so phones download small files
    layout: 'constrained',
    responsiveStyles: true,
  },
});
