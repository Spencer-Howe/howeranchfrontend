// Gets new photos ready for the website. Run after adding photos to src/assets/photos/:
//   npm run photos
// - Photos bigger than 1600px are shrunk (the site never shows them larger; phones get smaller copies).
// - File names become web-safe: "IMG 2041 (1).JPG" -> "img-2041-1.jpg". It prints every rename so
//   you can update any page that already used the old name.
// - iPhone HEIC photos can't be used: it lists them so they can be saved as JPEG first.
import { readdirSync, statSync, renameSync, existsSync } from 'node:fs';
import { join, extname, basename, dirname } from 'node:path';
import sharp from 'sharp';

const ROOT = new URL('../src/assets/photos/', import.meta.url).pathname;
const MAX = 1600;
const OK = ['.jpg', '.jpeg', '.png', '.webp', '.avif', '.gif'];

const files = [];
const walk = (dir) => readdirSync(dir).forEach((f) => {
  const p = join(dir, f);
  statSync(p).isDirectory() ? walk(p) : files.push(p);
});
walk(ROOT);

const safe = (name) => name.toLowerCase().normalize('NFKD').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || 'photo';
let resized = 0;
const renamed = [];
const heic = [];

for (const file of files) {
  const ext = extname(file).toLowerCase();
  if (ext === '.heic' || ext === '.heif') { heic.push(file.replace(ROOT, '')); continue; }
  if (!OK.includes(ext)) continue;
  let path = file;
  const wanted = join(dirname(file), safe(basename(file, extname(file))) + (ext === '.jpeg' ? '.jpg' : ext));
  if (wanted !== file && !existsSync(wanted)) {
    renameSync(file, wanted);
    renamed.push(`${file.replace(ROOT, '')}  ->  ${wanted.replace(ROOT, '')}`);
    path = wanted;
  }
  const meta = await sharp(path).metadata();
  if (Math.max(meta.width ?? 0, meta.height ?? 0) > MAX) {
    const buf = await sharp(path).rotate().resize(MAX, MAX, { fit: 'inside' })
      .toFormat(ext === '.png' ? 'png' : ext === '.webp' ? 'webp' : 'jpeg', { quality: 80, mozjpeg: true }).toBuffer();
    await sharp(buf).toFile(path);
    resized++;
  }
}

console.log(`${files.length} photos checked, ${resized} shrunk to ${MAX}px.`);
if (renamed.length) console.log(`Renamed (update any page using the old name):\n  ${renamed.join('\n  ')}`);
if (heic.length) {
  console.log(`\nThese are iPhone HEIC photos, which websites can't use:\n  ${heic.join('\n  ')}`);
  console.log('Fix: open each in the Windows Photos app > ... > Save as > JPG (then delete the HEIC), or on the');
  console.log('iPhone set Settings > Camera > Formats > Most Compatible so new photos are JPEG.');
  process.exitCode = 1;
}
