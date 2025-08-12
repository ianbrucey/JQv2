# 2) Current State — Laravel + Traefik + OpenHands Integration

What exists today
- JusticeQuest (Laravel 11) as the control plane
  - Auth, case selection, container orchestration (warm pool)
  - Writes Traefik router files for workspace subdomains
  - Generates access tokens and redirects the user to workspace‑<uuid>.justicequest.test:8443
- Traefik reverse proxy
  - TLS (mkcert in dev), dynamic subdomain routing via file provider
  - Optional ForwardAuth calling Laravel /_proxy/auth to validate token (now session‑bound)
- OpenHands containers
  - One per session/case with mounted workspace
  - Full OpenHands application UI

What works
- End‑to‑end: user → case → OpenHands UI on workspace subdomain
- Isolation via per‑session containers and mounted folders
- Session binding at the edge (prevents cross‑user reuse of a link)

Pain points
- Edge complexity: ForwardAuth, token/session binding, dynamic YAML files
- First‑load latency: cold starts if warm pool misses
- Operational: more moving parts to deploy/operate (Laravel + Traefik + OpenHands)

Takeaway
- The integration validated core feasibility and isolation, but the architecture has extra moving parts if our long‑term plan is to modify/own OpenHands.

