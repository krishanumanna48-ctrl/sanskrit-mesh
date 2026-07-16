# IR Serialization and Versioning

## 1. Purpose

This document defines how Sanskrit-Mesh serializes its compressed IR and how version changes are handled.

The goal is to make the IR:
- deterministic
- backward-compatible where possible
- explicit about version changes
- safe to validate and test

## 2. Canonical serialization rules

All IR payloads should be serialized in a canonical form before comparison or validation.

### Required rules
- object keys must be emitted in a deterministic order
- whitespace must not affect semantics
- strings must preserve their exact content
- arrays must preserve element order
- nested objects must be recursively canonicalized

### Recommended form
- use JSON with sorted keys
- use compact formatting for deterministic byte-level comparisons
- avoid non-semantic runtime ordering

## 3. IR envelope structure

A compressed payload should carry enough metadata to decode it safely.

Suggested envelope fields:
- `version`: IR version number
- `format`: serialization format, such as `json`
- `layers`: active layers used in the transformation
- `payload`: the actual compressed body

This makes the IR self-describing and easier to evolve.

## 4. Versioning policy

Use semantic versioning for the IR:
- MAJOR: breaking changes to the encoding contract
- MINOR: additive, backward-compatible changes
- PATCH: bug fixes and compatibility fixes

### Rules
- a decoder must be able to reject unsupported versions explicitly
- a new version should come with validator coverage
- changes to the canonical form or decode contract require a version bump

## 5. Compatibility rules

When introducing a new rule or layer:
- preserve decode compatibility for older versions where possible
- do not silently reinterpret old payloads
- require explicit migration logic for incompatible changes

## 6. Validation expectations

Every version change should be validated with:
- round-trip tests
- deterministic serialization tests
- compatibility tests for prior versions where applicable

## 7. Release policy

A release should not be considered ready unless:
- the current IR version is documented
- the canonical form is stable
- the validator passes for the supported payload types
- compatibility notes are available for downstream integrators
