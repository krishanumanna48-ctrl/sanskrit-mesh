# Privacy and Rollout Policy

## Privacy
- Adaptive dictionary features must be opt-in
- Raw payload contents must never be stored without explicit consent
- Telemetry should be aggregated and ideally hashed or redacted
- PII and sensitive text should be excluded from learning pipelines by default

## Rollout
- New linguistic or compression rules should ship behind a staged rollout
- Canary deployments should be used before general release
- The validator and regression suite must pass before promotion
- Rollback should be immediate if round-trip failures or regressions appear
