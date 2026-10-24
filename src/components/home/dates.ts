// Date helpers for the season islands. Dates are local days ('YYYY-MM-DD'), compared at midnight.
import type { Season } from '../../data/home';

export const day = (iso: string) => {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(y, m - 1, d);
};

export const today = () => {
  const n = new Date();
  return new Date(n.getFullYear(), n.getMonth(), n.getDate());
};

export const daysBetween = (a: Date, b: Date) => Math.round((b.getTime() - a.getTime()) / 86_400_000);

export const nice = (d: Date) => d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });

export const inWords = (n: number) => (n === 0 ? 'today' : n === 1 ? 'tomorrow' : `in ${n} days`);

/** What's on now, and the next thing to look forward to. */
export function whatsOn(seasons: Season[], now = today()) {
  const current = seasons.find((s) => day(s.start) <= now && now <= day(s.end));
  const nextDate = current?.dates?.map(day).find((d) => d >= now);
  const upcoming = seasons.filter((s) => day(s.start) > now).sort((a, b) => +day(a.start) - +day(b.start))[0];
  return { current, nextDate, upcoming };
}
