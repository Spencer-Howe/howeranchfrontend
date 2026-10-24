// The season calendar: a bar from the first season to the last with a "today" marker, and a card per season
// that says whether it's on now, coming up (with a countdown) or done for the year.
import { useEffect, useState } from 'react';
import type { Season } from '../../data/home';
import { day, daysBetween, inWords, nice, today } from './dates';

const MONTH = (d: Date) => d.toLocaleDateString('en-US', { month: 'short' });

export default function SeasonTimeline({ seasons }: { seasons: Season[] }) {
  const [now, setNow] = useState<Date | null>(null);
  useEffect(() => setNow(today()), []);

  const first = day(seasons[0].start);
  const last = day(seasons[seasons.length - 1].end);
  const span = daysBetween(first, last) + 1;
  const pct = (d: Date) => `${(Math.min(Math.max(daysBetween(first, d), 0), span) / span) * 100}%`;

  // Month ticks along the bar
  const months: Date[] = [];
  for (let d = new Date(first.getFullYear(), first.getMonth(), 1); d <= last; d = new Date(d.getFullYear(), d.getMonth() + 1, 1)) {
    if (d >= first) months.push(d);
  }
  const showToday = now && now >= first && now <= last;

  return (
    <div className="timeline">
      <div className="bar" role="img" aria-label={`Season calendar from ${MONTH(first)} to ${MONTH(last)}`}>
        {seasons.map((s) => {
          const on = now && day(s.start) <= now && now <= day(s.end);
          return (
            <span
              key={s.id}
              className={`seg seg-${s.id}${on ? ' on' : ''}`}
              style={{ left: pct(day(s.start)), width: `calc(${pct(day(s.end))} - ${pct(day(s.start))})` }}
            />
          );
        })}
        {months.map((m) => (
          <span key={+m} className="tick" style={{ left: pct(m) }}>{MONTH(m)}</span>
        ))}
        {showToday && <span className="today" style={{ left: pct(now) }}><b>Today</b></span>}
      </div>

      <ol className="season-cards">
        {seasons.map((s) => {
          const start = day(s.start);
          const end = day(s.end);
          let status = s.when;
          let state = 'later';
          if (now) {
            if (now > end) { status = 'Done for this year'; state = 'past'; }
            else if (now >= start) {
              const next = s.dates?.map(day).find((d) => d >= now);
              status = next ? `On now · next date ${nice(next)}` : `On now · ${s.when}`;
              state = 'now';
            } else {
              status = `${s.when} · starts ${inWords(daysBetween(now, start))}`;
            }
          }
          return (
            <li key={s.id} className={`season-card seg-${s.id} ${state}`}>
              <span className="status">{status}</span>
              <h3>{s.name}</h3>
              <p>{s.blurb}</p>
              <a href={s.href}>{state === 'past' ? 'See what it was like' : 'Book or learn more'} →</a>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
