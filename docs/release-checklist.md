# V2 Release Checklist

## Release readiness
- [ ] Validator passes for core, linguistic, multilingual, and unicode payloads
- [ ] IR versioning and canonical serialization are documented and used by the runtime
- [ ] New linguistic rules have round-trip regression tests
- [ ] New compression techniques have regression tests and benchmarks
- [ ] Examples and integrations are documented
- [ ] Packaging metadata and extras are consistent
- [ ] Privacy and rollout policy are documented

## Validation gate
- [ ] Run validator suite on representative payloads
- [ ] Run regression suite for linguistic and multilingual features
- [ ] Run benchmark suite and record baseline numbers
- [ ] Confirm no lossless regressions

## Rollout plan
- [ ] Use staged rollout: canary -> general availability
- [ ] Maintain rollback path for validator failures or regressions
- [ ] Track round-trip success rate and benchmark deltas
