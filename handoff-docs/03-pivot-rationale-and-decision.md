# 3) Pivot Rationale and Decision

Why pivot now
- Product direction: we will modify OpenHands to deliver a Cursor‑like legal editor and agent workflows over folders/files. Owning OpenHands aligns the codebase with the product.
- Simplicity: removing the Laravel bridge and ForwardAuth reduces edge complexity and places auth/workflow logic in one place (the OpenHands fork).
- Maintainability: avoiding a perpetual integration layer reduces drift and speeds up development.

Decision summary
- Move to a single‑tenant deployment model per customer for MVP/pilot
- Fork OpenHands (MIT) and build an OpenHands Control Plane (OH‑CP) inside it
- Keep Traefik only for TLS and subdomain routing (Docker provider, labels)
- Drop ForwardAuth and dynamic YAML; enforce auth inside the OpenHands runtime

Constraints and assumptions
- Isolation remains via per‑tenant (or per‑case) containers
- Persistence via mounted host folders (optional S3 backups)
- OIDC login (or simple auth) built into OH‑CP

Risks
- Owning auth/multi‑tenancy code in the fork; mitigated by starting single‑tenant
- Upgrade path: track upstream OpenHands releases; keep patches well‑scoped

Exit criteria for pivot success
- New user: login → select case → working editor in <3s (warm pool)
- Instance can be deployed on a small VM with one script
- Clear path to add multi‑tenant later without re‑architecture

