// The "happening now" badge in the hero. A React island: Astro renders it to HTML at build time, then the
// browser takes it over (hydrates) and fills in today's date. Until then it shows the build-time fallback,
// so the server HTML and the first browser render match (no hydration mismatch from Date.now()).
import { useEffect, useState } from 'react';
import type { Season } from '../../data/home';
import { day, daysBetween, inWords, nice, today, whatsOn } from './dates';

export default function SeasonNow({ seasons }: { seasons: Season[] }) {
  const [now, setNow] = useState<Date | null>(null);
  useEffect(() => setNow(today()), []);

  if (!now) return <a className="season-now" href="#seasons"><span className="dot" />Fall &amp; holiday seasons at Howe Ranch</a>;

  const { current, nextDate, upcoming } = whatsOn(seasons, now);
  let text: string;
  let href = '#seasons';
  if (current && nextDate) {
    text = `${current.name} is on! Next date ${nice(nextDate)}`;
    href = current.href;
  } else if (current) {
    text = `It’s ${current.name} season`;
    href = current.href;
  } else if (upcoming) {
    text = `${upcoming.name} starts ${inWords(daysBetween(now, day(upcoming.start)))}`;
  } else {
    text = 'See what’s coming up at the ranch';
  }
  return (
    <a className="season-now live" href={href}>
      <span className="dot" />
      {text}
    </a>
  );
}
