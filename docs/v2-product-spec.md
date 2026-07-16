# Sanskrit-Mesh V2 Product Spec and IR Contract

## 1. Goal

Make Sanskrit-Mesh a production-grade, lossless compression layer for structured LLM payloads.

The core promise is simple:
- compress agent-style payloads into a compact IR
- preserve meaning exactly
- recover the original payload exactly on decode
- keep the system deterministic, testable, and versioned

## 2. What V2 includes

V2 is a layered, reversible pipeline:
1. Entropy layer for redundancy reduction
2. Structural layer for schema/key compression
3. Paninian layer for linguistic transforms
4. Huffman layer for compact symbol encoding

The layers are applied in a fixed order for encode and reversed for decode.

## 3. Core contract

Every supported transform must satisfy the following contract:
- Encode then decode must return the original payload exactly
- The output must be deterministic for the same input and configuration
- The IR format must be stable and versioned
- Any new rule or dictionary entry must be testable with a round-trip case

This is the differentiator. Lossless behavior is not optional; it is the product boundary.

## 4. Non-goals

V2 does not aim to:
- compress arbitrary human chat lossily without verification
- replace model inference or model size reduction
- rely on ambiguous heuristics in the critical path
- silently change meaning during compression

## 5. IR rules

The IR must be:
- canonical
- reversible
- unambiguous
- versioned
- safe for downstream frameworks

### Required properties
- stable serialization format
- explicit version marker
- deterministic key ordering
- no hidden state required for decode
- clear handling of unknown or unsupported content

## 6. Canonicalization rules

Before compression, the payload should be normalized in a consistent way:
- normalize object key ordering
- preserve semantic structure while removing non-semantic formatting differences
- avoid relying on incidental whitespace or runtime ordering

The canonical form is the reference form for validation and regression tests.

## 7. Versioning policy

Each IR change must be versioned.

Rules:
- breaking changes require a new major version
- additive reversible changes may use a minor version
- bug fixes and compatibility patches use patch version

A new version must include:
- a summary of the change
- compatibility notes
- regression tests
- validator evidence

## 8. Validation gate

V2 release readiness requires a strict validation gate:
- round-trip tests for structured payloads
- round-trip tests for system prompts and freeform text
- regression cases for nested payloads
- fuzz tests for edge cases and Unicode

The validator is the acceptance test for production readiness.

## 9. Linguistics policy

Linguistic rules must be:
- reversible
- testable
- narrowly scoped at first
- documented with examples

Rules that are too ambiguous or not fully reversible must stay behind a feature flag or be excluded from the default path.

## 10. Release criteria

V2 is considered ready when:
- the validator passes for representative payloads
- round-trip equality is preserved across layers
- the IR versioning policy is in place
- benchmarks and docs are available
- examples and integrations are documented
- privacy and rollout safety rules are defined
