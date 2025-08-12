# Risks and Mitigations

## Risks
- Runtime mount misconfiguration leads to empty or read-only workspaces
- S3 sync conflicts or partial sync cause data loss
- Hidden Git assumptions still trigger code paths and errors
- Performance regression for large S3 cases due to sync cost
- Security: leaking S3 credentials into nested runtime

## Mitigations
- Strong validation for case paths; explicit error messages
- For S3: last-write-wins MVP, add checksums and conflict logs; provide manual override
- Feature flag guardrails and QA scenarios to ensure Git paths are bypassed
- Async size calculation and lazy folder listing for large cases
- Keep S3 credentials in app container for sync approach; do not pass into nested runtime

## Open Questions
- Do we need case-level access controls per user? (Single-tenant may defer)
- How to handle concurrent edits across multiple conversations on same case? (MVP: discourage; longer-term: locks)
- Should we implement file templates or starter kits?

