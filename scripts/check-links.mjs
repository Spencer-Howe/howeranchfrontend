// Checks the built site (dist/) for broken internal links, photos and documents.
// Run after `npm run build`:  npm run check-links
// Add --external to also check links to other websites (slower).
import { readFileSync, existsSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

const DIST = new URL('../dist/', import.meta.url).pathname;
const external = process.argv.includes('--external');

const redirects = readFileSync(new URL('../public/_redirects', import.meta.url), 'utf8')
  .split('\n').filter((l) => l.trim() && !l.startsWith('#')).map((l) => l.trim().split(/\s+/)[0]);
const redirected = (path) => redirects.some((r) => (r.endsWith('/*') ? path.startsWith(r.slice(0, -1)) : path === r));

const pages = [];
const walk = (dir) => readdirSync(dir).forEach((f) => {
  const p = join(dir, f);
  if (statSync(p).isDirectory()) walk(p);
  else if (f.endsWith('.html')) pages.push(p);
});
walk(DIST);

const exists = (path) => {
  const clean = decodeURIComponent(path.split('#')[0].split('?')[0]);
  if (clean === '/' || clean === '') return existsSync(join(DIST, 'index.html'));
  const p = join(DIST, clean);
  return existsSync(p) && statSync(p).isFile() || existsSync(p + '.html') || existsSync(join(p, 'index.html'));
};

const broken = [];
const outside = new Map();
for (const page of pages) {
  const html = readFileSync(page, 'utf8');
  const from = '/' + relative(DIST, page).replace(/\.html$/, '').replace(/^index$/, '');
  for (const [, attr, url] of html.matchAll(/\s(href|src)="([^"]+)"/g)) {
    if (url.startsWith('#') || url.startsWith('mailto:') || url.startsWith('tel:') || url.startsWith('data:')) continue;
    if (/^https?:\/\//.test(url)) {
      if (!outside.has(url)) outside.set(url, new Set());
      outside.get(url).add(from);
      continue;
    }
    if (url.startsWith('/') && !exists(url) && !redirected(url.split('#')[0])) broken.push(`${from}: ${attr}="${url}"`);
  }
  for (const [, set] of html.matchAll(/\ssrcset="([^"]+)"/g)) {
    for (const part of set.split(',')) {
      const url = part.trim().split(' ')[0];
      if (url.startsWith('/') && !exists(url)) broken.push(`${from}: srcset ${url}`);
    }
  }
}

console.log(`${pages.length} pages checked.`);
if (broken.length) {
  console.log(`\n${broken.length} broken internal links:`);
  [...new Set(broken)].forEach((b) => console.log('  ' + b));
} else {
  console.log('No broken internal links, photos or documents.');
}

if (external) {
  const urls = [...outside.keys()];
  console.log(`\nChecking ${urls.length} links to other websites...`);
  const bad = [];
  const check = async (url) => {
    try {
      const r = await fetch(url, { method: 'GET', redirect: 'follow', signal: AbortSignal.timeout(20000),
        headers: { 'User-Agent': 'Mozilla/5.0 (link check)' } });
      if (r.status >= 400) bad.push(`${r.status}  ${url}  (on ${[...outside.get(url)].join(', ')})`);
    } catch (e) {
      bad.push(`ERR  ${url}  (on ${[...outside.get(url)].join(', ')}): ${e.cause?.code || e.name}`);
    }
  };
  for (let i = 0; i < urls.length; i += 8) await Promise.all(urls.slice(i, i + 8).map(check));
  console.log(bad.length ? `${bad.length} problem links:\n  ${bad.join('\n  ')}` : 'All outside links answered.');
}
process.exitCode = broken.length ? 1 : 0;
