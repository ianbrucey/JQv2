# 5) Repository Strategy and Migration Plan

Question: Clone OpenHands into this repo, or create a new repo?

Recommendation
- Create a new repo for the OpenHands fork (e.g., justicequest/openhands-legal).
- Keep this Laravel repo intact as historical reference and for any management tooling you may still want.

Why a new repo
- Clear separation of concerns: the fork has a different runtime, deps, and release cadence
- Cleaner CI/CD and packaging (Docker image build) without Laravel constraints
- Easier for contributors to reason about the “app we ship” vs. “legacy integration”

Migration steps
1) New repo bootstrapping
   - Initialize justicequest/openhands-legal
   - Import upstream OpenHands (MIT) and set remote for upstream tracking
   - Add a minimal OH‑CP module (login, cases, orchestrator skeleton)
   - Add docker-compose.dev.yml with Traefik (Docker provider) and a sample runtime

2) Feature parity checkpoint
   - Implement login (OIDC) and a trivial case list
   - Implement session creation → spin/assign a runtime with labels and mount a local folder
   - Redirect to workspace subdomain and validate runtime auth

3) Decommission Laravel on the hot path
   - Freeze changes in this repo; keep for ops/dashboards if desired
   - Update DNS to point customer subdomains to the new OH‑CP stack

4) Packaging for single‑tenant deployments
   - Provide a single docker-compose.yml with Traefik, OH‑CP, and runtime warm pool
   - One-line bootstrap script for a new VM (install Docker, bring up stack, set admin creds)

5) Upstream sync strategy
   - Periodically pull upstream OpenHands changes into your fork
   - Keep your modifications modular (auth middleware, CP module) to reduce merge pain

Roll-back plan
- You can point DNS back to the Laravel+Traefik integration if needed; both architectures can coexist during transition.

