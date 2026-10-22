// Site-wide details: the menu, contact info, links. Change them here and every page updates.

export const BOOKING_SITE = 'https://thehoweranchregistration.com';

export const contact = {
  phone: '(424) 219-4212',
  phoneHref: 'tel:+14242194212',
  email: 'howeranchservices@gmail.com',
  street: '215 Browns Gulch Rd',
  city: 'Kalispell',
  region: 'MT',
  postalCode: '59901',
};

export const social = [
  { label: 'Instagram', href: 'https://www.instagram.com/howe_ranch/' },
  { label: 'Facebook', href: 'https://www.facebook.com/p/The-Howe-Ranch-61556938111897/' },
];

// The menu. A group with `items` shows as a dropdown (a flat list on phones).
export type MenuLink = { label: string; href: string };
export type MenuItem = MenuLink | { label: string; items: MenuLink[] };

export const menu: MenuItem[] = [
  { label: 'Home', href: '/' },
  {
    label: 'About',
    items: [
      { label: 'About', href: '/about-5' },
      { label: 'Reviews', href: '/reviews' },
      { label: 'Opportunities', href: '/opportunities' },
    ],
  },
  {
    label: 'Weddings',
    items: [
      { label: 'Weddings', href: '/weddings' },
      { label: 'MicroWedding', href: '/microwedding' },
    ],
  },
  {
    label: 'Winter Wonderland',
    items: [
      { label: 'Winter Wonderland', href: '/winterwonderland' },
      { label: 'Private Winter Wonderland', href: '/bookwinterwonderlandcelebration' },
    ],
  },
  {
    label: 'Animals',
    items: [
      { label: 'Our Animals', href: '/animals' },
      { label: 'Available Mini Moos', href: '/animals/availableminimoos' },
    ],
  },
  {
    label: 'Photos',
    items: [
      { label: 'Photos', href: '/photos' },
      { label: 'Media', href: '/media' },
    ],
  },
  { label: 'FAQs', href: '/faqs' },
];

// Where the website's contact forms send messages (the booking app adds them to Admin > Leads).
// For testing against a local booking app: PUBLIC_CONTACT_ENDPOINT=http://localhost:5000/api/website-message
export const CONTACT_ENDPOINT = import.meta.env.PUBLIC_CONTACT_ENDPOINT || `${BOOKING_SITE}/api/website-message`;
