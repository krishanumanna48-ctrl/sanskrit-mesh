# Additional Lossless Compression Techniques

## 1. Symbol-level compaction
- replace repeated symbol clusters with compact tokens
- keep a reversible mapping table for decode

## 2. Phrase-level compaction
- compress repetitive multi-word phrases into compact reversible tokens
- use exact-match rules so the original phrasing is restored precisely

## 3. Structural compaction
- shrink schema and key patterns using canonical forms and registry-backed mappings
- maintain a stable reverse map for decode

## 4. Canonical normalization
- normalize whitespace, ordering, and common formatting differences before compression
- preserve exact values while reducing redundancy

## 5. Tokenizer-aware selection
- prefer transformations that are meaningful under actual tokenization metrics
- use these rules to optimize for token bills rather than raw character count alone
