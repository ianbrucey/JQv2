# Feature Flags and GitHub Bypass

## Goals
- Disable GitHub-centric features without invasive code removal
- Default instances to "case mode"

## Flags
- `FEATURE_GIT=false` — hides repo/PR UI; backend skips repo-dependent logic
- `FEATURE_S3` — enables S3 CaseStore and related UI

## Frontend
- Wrap components and routes that require Git in feature checks
- Replace repo-focused panels with Files panel bound to case

## Backend
- In `agent_session` and microagent bootstrap, if `git_enabled=false`, skip repo operations
- Avoid provider token prompts

## Cleanup Targets (Examples)
- Microagent PR review flows (guarded or hidden)
- Repo-based microagent discovery
- Git provider auth banners

## Migration Strategy
- Phase 1: Flag-driven disablement
- Phase 2: Move Git logic into optional plugins

