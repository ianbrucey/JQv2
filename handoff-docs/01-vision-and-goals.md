# 1) Vision and Goals

Ultimate goal: build a Cursor‑like, AI‑powered legal drafting environment focused on written documents, not code. Users work inside an isolated, agentic workspace with their case files; the AI can read, refactor, and generate documents safely.

Key principles
- Full OpenHands UX: file tree, editor, chat/agent, terminals as needed
- Isolation: each customer (or case) has a sandboxed workspace
- Simplicity first: reduce network plumbing; invest engineering effort in legal workflows
- Security: TLS, auth, per‑tenant isolation, least privilege
- Portability: minimize cloud lock‑in; run on a single VM for pilots, scale later

What “success” looks like
- A legal professional logs in, picks a case, and drafts/edit documents with AI guidance
- Their files are isolated from other customers
- System is easy to deploy/operate per customer (single compose stack)
- Later, migrate to multi‑tenant with minimal re‑architecture

Non‑goals (for MVP)
- Building a custom chat UI that replaces OpenHands
- Complex multi‑tenant routing/ForwardAuth in the MVP
- Heavy realtime collaboration features

