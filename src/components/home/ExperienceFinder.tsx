// "Find your experience": filter chips + photo cards. Filtering animates with the browser's View Transitions
// API (each card has its own view-transition-name, so cards glide to their new spots); browsers without it just
// switch instantly. Cards tilt toward the pointer and follow it with a soft glare (CSS variables set here).
import { useState, type PointerEvent } from 'react';
import { flushSync } from 'react-dom';
import type { Experience, Tag } from '../../data/home';

export type Photo = { src: string; srcSet: string; width: number; height: number; alt: string };
type Props = { experiences: Experience[]; tags: { id: Tag | 'all'; label: string }[]; photos: Record<string, Photo> };

function tilt(e: PointerEvent<HTMLAnchorElement>) {
  if (e.pointerType !== 'mouse') return;
  const el = e.currentTarget;
  const r = el.getBoundingClientRect();
  const x = (e.clientX - r.left) / r.width;
  const y = (e.clientY - r.top) / r.height;
  el.style.setProperty('--rx', `${(0.5 - y) * 8}deg`);
  el.style.setProperty('--ry', `${(x - 0.5) * 10}deg`);
  el.style.setProperty('--gx', `${x * 100}%`);
  el.style.setProperty('--gy', `${y * 100}%`);
}
function untilt(e: PointerEvent<HTMLAnchorElement>) {
  ['--rx', '--ry'].forEach((p) => e.currentTarget.style.setProperty(p, '0deg'));
}

export default function ExperienceFinder({ experiences, tags, photos }: Props) {
  const [tag, setTag] = useState<Tag | 'all'>('all');
  const shown = tag === 'all' ? experiences : experiences.filter((x) => x.tags.includes(tag));

  const pick = (t: Tag | 'all') => {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!document.startViewTransition || reduce) return setTag(t);
    // flushSync makes React update the DOM inside the transition callback, so the browser can animate it
    document.startViewTransition(() => flushSync(() => setTag(t)));
  };

  return (
    <div className="finder">
      <div className="chips" role="group" aria-label="Show experiences for">
        {tags.map((t) => (
          <button key={t.id} type="button" aria-pressed={tag === t.id} onClick={() => pick(t.id)}>
            {t.label}
          </button>
        ))}
      </div>
      <p className="sr-only" aria-live="polite">{shown.length} experiences shown</p>
      <ul className="cards">
        {shown.map((x) => {
          const p = photos[x.photo];
          return (
            <li key={x.id} style={{ viewTransitionName: `xp-${x.id}` }}>
              <a className="card" href={x.href} onPointerMove={tilt} onPointerLeave={untilt}>
                <img src={p.src} srcSet={p.srcSet} sizes="(max-width: 700px) 92vw, 380px" width={p.width} height={p.height}
                  alt={p.alt} loading="lazy" decoding="async" />
                {x.badge && <span className="badge">{x.badge}</span>}
                <span className="body">
                  <span className="title">{x.title}</span>
                  <span className="blurb">{x.blurb}</span>
                  <span className="go">Explore →</span>
                </span>
              </a>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
