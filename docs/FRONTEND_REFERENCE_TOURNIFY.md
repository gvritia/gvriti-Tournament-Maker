# Frontend Reference: Retired Tournify Direction

## Decision

The previous Tournify-inspired direction is retired.

Do not copy the old Tournify-style frontend. Do not rebuild the app as a public
tournament page. Do not use the previous purple/fuchsia sports-promo visual
language as the base.

The new frontend is an organizer workspace for authenticated backend workflows.

## What To Avoid

- Public landing-page composition.
- Hero sections.
- Public tournament presentation blocks.
- News/articles.
- Social links.
- Cookie banners.
- Ads.
- Public share/favorite controls.
- Marketing copy.
- Decorative gradients as the main visual identity.
- Oversized cards where tables/forms would be clearer.

## What The New UI Should Use Instead

- Dense dashboard.
- Tables.
- Filters.
- Forms.
- Action panels.
- Confirm dialogs.
- Status chips.
- Compact match summaries.
- Team detail pages.
- Championship standings.
- Cup bracket as an operational tool.
- Human-readable backend errors.

## Replacement Design Direction

The new visual reference is not a specific external website. It should feel like
a calm dark admin console for football competition operations:

- reliable;
- compact;
- readable;
- action-oriented;
- responsive;
- dark-only;
- restrained.

Use real backend scenarios to shape the UI:

- JWT auth;
- user-scoped data;
- team/player/stadium/referee setup;
- match scheduling;
- ticket price editing;
- lineups;
- protocol generation;
- standings/statistics;
- cup bracket.

## Public Preview Rule

Unauthenticated users may see how the app looks and navigate preview tabs, but
they cannot perform actions. Public preview is read-only and uses static/sample
content.

Real data and all mutations require login.
