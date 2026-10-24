// Guest reviews carousel: moves on by itself every 7 seconds, pauses while the pointer or keyboard focus is
// on it (or when the visitor prefers less motion), swipes on phones, and has dots + arrow keys.
import { useEffect, useRef, useState } from 'react';

type Review = { name: string; text: string };

export default function Reviews({ reviews }: { reviews: Review[] }) {
  const [at, setAt] = useState(0);
  const [paused, setPaused] = useState(false);
  const x0 = useRef(0);
  const go = (i: number) => setAt((i + reviews.length) % reviews.length);

  useEffect(() => {
    if (paused || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const t = setTimeout(() => go(at + 1), 7000);
    return () => clearTimeout(t);
  }, [at, paused]);

  return (
    <div
      className="reviews"
      role="region"
      aria-roledescription="carousel"
      aria-label="Guest reviews"
      tabIndex={0}
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
      onKeyDown={(e) => { if (e.key === 'ArrowRight') go(at + 1); if (e.key === 'ArrowLeft') go(at - 1); }}
      onTouchStart={(e) => { x0.current = e.touches[0].clientX; setPaused(true); }}
      onTouchEnd={(e) => {
        const dx = e.changedTouches[0].clientX - x0.current;
        if (Math.abs(dx) > 40) go(at + (dx < 0 ? 1 : -1));
      }}
    >
      <div className="track" style={{ transform: `translateX(-${at * 100}%)` }}>
        {reviews.map((r, i) => (
          <figure key={r.name} className="review" aria-hidden={i !== at} aria-roledescription="slide" aria-label={`${i + 1} of ${reviews.length}`}>
            <blockquote>“{r.text}”</blockquote>
            <figcaption>{r.name}</figcaption>
          </figure>
        ))}
      </div>
      <div className="dots">
        {reviews.map((r, i) => (
          <button key={r.name} type="button" aria-label={`Review ${i + 1}: ${r.name}`} aria-current={i === at} onClick={() => go(i)} />
        ))}
      </div>
    </div>
  );
}
