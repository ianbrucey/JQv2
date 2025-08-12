# 4) Target Architecture — Single‑Tenant OpenHands Fork

Components
- Traefik (edge)
  - Wildcard TLS via ACME
  - Docker provider: routes by container labels; no dynamic files
- OpenHands Control Plane (OH‑CP) inside the fork
  - Login: OIDC (Google/Microsoft/Auth0/Keycloak) → session cookie on .justicequest.com
  - Case selection UI and simple DB (users, cases, collaborators)
  - Orchestrator (Docker SDK): warm pool, spawn/assign, cleanup, logs
  - API for listing cases and creating sessions
- OpenHands Runtime Containers
  - One per active workspace (user+case or just per customer)
  - Mount /workspaces/<case-id> read/write; read‑only rootfs where possible
  - Small auth middleware validates session/JWT on HTTP + WebSocket

Request flow (happy path)
1. Browser → justicequest.com → OH‑CP (login if needed)
2. User selects case → OH‑CP assigns container from warm pool or spawns
3. OH‑CP labels the container:
   - traefik.http.routers.workspace-<session>.rule=Host(`workspace-<session>.justicequest.com`)
   - traefik.http.services.workspace-<session>.loadbalancer.server.port=3000
4. OH‑CP redirects user to https://workspace-<session>.justicequest.com
5. Traefik routes by Host header → runtime container
6. Runtime checks session/JWT; if valid, serves full OpenHands UI

Security
- TLS at edge; HSTS
- Session/JWT signed by OH‑CP; runtime validates (public key)
- Resource limits (CPU/mem/pids); read‑only rootfs + writable volumes; seccomp/apparmor
- Per‑case folder mounts; no cross‑case paths

Operations
- One compose stack per customer (Traefik + OH‑CP + runtime warm pool)
- Restic/S3 backups for /workspaces
- Uptime probe; log aggregation later

Migration to multi‑tenant later
- Keep Traefik + Docker provider
- Keep OH‑CP; change assignment policy from per‑customer VM to shared cluster
- Add orgs/tenancy in DB; same edge and runtime auth model

