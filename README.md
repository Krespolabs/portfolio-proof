# Portfolio Proof — Samson Onuh

An evidence-first static portfolio for Krespo Labs. This review draft adds an Astro website and a clearly fictional garden-care business demo. It does not claim client results or production readiness.

## Local development

Requires Node.js 22.12+ (or a supported newer LTS version) and npm.

```sh
npm ci
npm run dev
```

The dev server listens on localhost only. Routes:

- `/` — portfolio, approach, and source-linked project context.
- `/work/fern-and-field/` — fictional demo case study and limitations.
- `/demos/fern-and-field/` — fictional garden-care service demo.

```sh
npm run check
npm run build
npm test
npm run preview
```

The build generates static files in `dist/`. No backend, database, integrations, analytics, cookies, payments, or contact collection are implemented. No environment variables are required. All CSS and SVG artwork is original to this draft; system fonts avoid remote font requests. The demo enquiry control is deliberately disabled, and there is no enquiry form or submission endpoint.

## Publication gate

**The owner has approved publishing the reviewed feature branch and opening a public pull request only.** Existing repository history must be preserved. Merging, deploying, connecting a branch or project to hosting, and activating a preview are not authorized. Vercel may create a public preview automatically when a pull request is opened or a branch is connected; no hosting project or preview is to be created or activated as part of this review.

Crawler exclusion (`robots.txt` and `noindex, nofollow`) is defence in depth, not access control or permission to publish. No hosting configuration or deployment workflow is included.

## Evidence and limitations

Fern & Field is an invented brand for a self-directed design exercise, not a real business or client. Its service copy is fictional sample content. No real address, contact information, prices, testimonials, completed jobs, certifications, or performance claims are included.

- [Lovinex Web source](https://github.com/Krespolabs/Lovinex) — dating-web interface in development; deployment and current status unverified.
- [KrespoAI Hub source](https://github.com/Krespolabs/Krespoai-hub) — prototype interface; working integrations unverified.

These are source links supplied by the existing repository, not verification of the linked products. The website does not connect to either product. No Supabase dependency or integration is used.

Use the existing [case-study template](templates/case-study.md) when adding future evidence. Identify what was actually implemented, link reproducible evidence, and describe limitations. Do not imply that sample or prototype content is production functionality.

## Before any future publication

Never include credentials, private/customer data, confidential work, account email or phone numbers, private clips, or assets without reuse rights. Inspect both the full intended change and reachable repository history. Run the local checks above and review the owner-approved publishing scope first.
