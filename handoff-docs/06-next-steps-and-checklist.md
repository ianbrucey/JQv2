# 6) Next Steps and Checklist

Immediate actions (week 1)
- [ ] Create new repo: justicequest/openhands-legal (MIT fork)
- [ ] Stand up Traefik with Docker provider in dev
- [ ] Add OH‑CP module to the fork:
  - [ ] OIDC login (Auth0/Clerk/Keycloak) and session cookie
  - [ ] Minimal DB (users, cases)
  - [ ] Orchestrator skeleton (Docker SDK) with warm pool
- [ ] Runtime auth middleware (validate session/JWT on HTTP + WS)
- [ ] Happy path demo: login → select case → open workspace subdomain

Short‑term hardening
- [ ] Per‑customer compose stack template (Traefik + OH‑CP + runtime)
- [ ] Resource limits; seccomp/apparmor; read‑only rootfs
- [ ] Restic/S3 backups for /workspaces
- [ ] Uptime checks and log capture

Defer/maybe later
- [ ] Multi‑tenant cluster (K8s/Nomad) and autoscaling
- [ ] Centralized logs/metrics (Loki/Promtail/Grafana)
- [ ] Advanced RBAC and audit trails
- [ ] Git integration for versioned workspaces

References
- See ../architecture-comparison.md for context
- See ../technical-implementation-plan.md (updated) for our journey

