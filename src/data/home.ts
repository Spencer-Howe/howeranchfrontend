// What the home page's interactive parts show: the season calendar, the experiences, the guest reviews.
// Wording comes from the site's own pages (Winter Wonderland, Media press release, Reviews).
// Dates are 'YYYY-MM-DD'. Update them each season; the page works out "happening now" and countdowns itself.
import { BOOKING_SITE } from './site';

export type Season = {
  id: string;
  name: string;
  when: string;          // shown as-is
  blurb: string;
  start: string;         // first day (for the calendar bar and "happening now")
  end: string;           // last day
  dates?: string[];      // exact event days, if known: used for "next date" countdowns
  href: string;
};

export const seasons: Season[] = [
  {
    id: 'spooky',
    name: 'Spooky Moo',
    when: 'October',
    blurb: 'Howe Ranch becomes Halloween Town: tiny Highland cows, trick-or-treating and a Spooky Moo Scavenger Hunt.',
    start: '2026-10-01',
    end: '2026-10-31',
    dates: ['2026-10-11', '2026-10-18', '2026-10-25', '2026-10-31'],
    href: `${BOOKING_SITE}/spooky-moo`,
  },
  {
    id: 'minimoo',
    name: 'Mini Moo Magic',
    when: 'November',
    blurb: 'Intimate holiday photo afternoons with the baby moos, goats, lambs and other ranch residents.',
    start: '2026-11-01',
    end: '2026-11-30',
    href: `${BOOKING_SITE}/mini-moo-magic`,
  },
  {
    id: 'wonderland',
    name: 'Winter Wonderland',
    when: 'Late November – January',
    blurb: 'The 17th annual Winter Wonderland: a cozy, storybook Christmas world with tiny Highland cows, Mrs. Claus and Santa.',
    start: '2026-11-23',   // the press release only says "late November": set the real opening day
    end: '2027-01-31',
    href: `${BOOKING_SITE}/winter-wonderland`,
  },
  {
    id: 'love',
    name: 'Season of Love',
    when: 'After Winter Wonderland',
    blurb: 'About six weeks of romantic, whimsical winter photo experiences surrounding Valentine’s season.',
    start: '2027-02-01',
    end: '2027-03-14',
    href: BOOKING_SITE,
  },
];

export type Tag = 'moos' | 'holiday' | 'groups' | 'stay' | 'weddings';
export const tags: { id: Tag | 'all'; label: string }[] = [
  { id: 'all', label: 'Everything' },
  { id: 'moos', label: 'Cuddle the Mini Moos' },
  { id: 'holiday', label: 'Holiday season' },
  { id: 'groups', label: 'Groups & parties' },
  { id: 'stay', label: 'Stay overnight' },
  { id: 'weddings', label: 'Weddings' },
];

// `photo` is a key into the photos the home page passes in (src/pages/index.astro)
export type Experience = { id: string; title: string; blurb: string; href: string; photo: string; tags: Tag[]; badge?: string };

export const experiences: Experience[] = [
  {
    id: 'mini-moo-magic',
    title: 'Mini Moo Magic with Photos',
    blurb: 'An intimate, small-group holiday experience with baby Highland cows, enchanting backdrops, crafts and treats. A professional photographer captures the moments.',
    href: `${BOOKING_SITE}/mini-moo-magic`,
    photo: 'calves',
    tags: ['moos', 'holiday'],
  },
  {
    id: 'winter-wonderland',
    title: 'Winter Wonderland Event',
    blurb: 'A limited-capacity Open Farm Day: enchanted holiday scenes, cookies with Mrs. Claus, Santa photos and micro mini-Highland calves.',
    href: `${BOOKING_SITE}/winter-wonderland`,
    photo: 'wonderland',
    tags: ['holiday', 'moos'],
    badge: '17th annual',
  },
  {
    id: 'private-mini-moo',
    title: 'Private Mini Moo Visit',
    blurb: 'Bottle feeding and cuddles with Pippi, Sugarplum, Finnegan, Theodore and Tarnickel, plus Dolly the emu, mini goats and bunnies. 1 – 15 guests.',
    href: `${BOOKING_SITE}/private-mini-moo`,
    photo: 'pippi',
    tags: ['moos', 'groups'],
  },
  {
    id: 'christmas-inn',
    title: 'Christmas Inn Stay',
    blurb: 'A magical farm stay, November 1 through January 31, during our most magical season of the year.',
    href: `${BOOKING_SITE}/christmas-inn`,
    photo: 'inn',
    tags: ['stay', 'holiday'],
    badge: 'Limited stays',
  },
  {
    id: 'private-wonderland',
    title: 'Private Wonderland Celebration',
    blurb: 'Your own private Christmas village for company parties, families and groups up to 120 guests. December 1 – January 31.',
    href: '/bookwinterwonderlandcelebration',
    photo: 'banquet',
    tags: ['groups', 'holiday'],
  },
  {
    id: 'spooky-moo',
    title: 'Spooky Moo Halloweentown',
    blurb: 'Throughout October, Howe Ranch becomes Halloween Town: friendly ghosts, pumpkins, potions and hands-on animal encounters.',
    href: `${BOOKING_SITE}/spooky-moo`,
    photo: 'spooky',
    tags: ['moos'],
  },
  {
    id: 'weddings',
    title: 'Storybook Weddings',
    blurb: 'Storybook Montana destination weddings, framed by valley and mountain views.',
    href: '/weddings',
    photo: 'wedding',
    tags: ['weddings', 'groups'],
  },
];

// From the Reviews page, word for word (Chris R. and Abi J. are shortened to their best lines)
export const reviews = [
  { name: 'Daniel S.', text: 'My girlfriend surprised me with a date here, easily one of the best dates I’ve ever been on. So much fun with so many cute animals and an amazingly friendly staff. All around amazing experience and would highly recommend' },
  { name: 'Christian', text: 'Wonderful place! Stumbled upon this place when searching for local events, and couldn\'t be happier! Everyone was so helpful and kind and the animals are adorable! 10/10, will be back for sure.' },
  { name: 'Alex M.', text: 'This is such a cool experience, our kids had a blast and the animals are all so sweet. We had a great time and hope to be back soon!' },
  { name: 'Chris R.', text: 'I came across this ranch online, immediately peaked my interest, and made my reservation same day. Come the day of the reservation and it was so much more than we had expected and hoped for. The animals were absolutely precious, hospitality was wonderful, atmosphere welcoming, and extra amenities alongside the animals were a treat.' },
  { name: 'Abi J.', text: 'You can tell that they care about the animals as well as the people that choose to come! Thank you Howe ranch for a great experience!' },
];
