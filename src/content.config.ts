import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

// One Markdown file per page in src/content/pages. The file's path is the page's address:
// pages/weddings.md is /weddings, pages/animals/availableminimoos.md is /animals/availableminimoos,
// pages/index.md is the home page.
const pages = defineCollection({
  loader: glob({ base: './src/content/pages', pattern: '**/*.md' }),
  schema: z.object({
    title: z.string(),                       // browser tab and Google result title
    description: z.string().default(''),     // the line Google shows under the title
    form: z.enum(['contact', 'animals']).optional(),  // adds a contact form at the bottom
    hidden: z.boolean().default(false),      // live, but kept out of Google and the sitemap
  }),
});

export const collections = { pages };
