import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const date = z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Use YYYY-MM-DD dates.');

const industryNews = defineCollection({
  loader: glob({ base: './src/content/news', pattern: '**/*.md' }),
  schema: z.object({
    title: z.string().min(1),
    description: z.string().min(1).max(200),
    publishedAt: date,
    announcementDate: date,
    authorName: z.string().min(1),
    status: z.enum(['draft', 'published']).default('draft'),
    sourceUrl: z.string().url(),
    tags: z.array(z.string()).default([]),
  }),
});

export const collections = { industryNews };
