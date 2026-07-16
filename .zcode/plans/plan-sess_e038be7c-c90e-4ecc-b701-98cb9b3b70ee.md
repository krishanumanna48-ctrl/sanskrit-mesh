# Sanskrit-Mesh v2 — Hyper-Compiler Final Implementation Plan

## Two confirmed rulings (material changes incorporated)
1. **Non-English source compression (Ruling 1b):** Natively compress non-English text. New `linguistics/` subsystem: Unicode script detection (Latin/Cyrillic/Greek/Devanagari/CJK/Arabic/Hangul) + multi-language redundancy matrices (EN, ES, FR, DE, IT, PT, HI/SA, ZH, JA, AR), cross-lingual agglutination, Hindi/Sanskrit native Sandhi/Samāsa routed into L3. Extensible one-line matrix pattern.
2. **BPE-token optimization (Ruling 2):** Optimize for actual BPE tokens, not char count. **PUA glyph scheme scrapped** (PUA fractures in BPE). Replaced with a vetted **BPE-safe single-token glyph pool** (confirmed 1-token in cl100k_base + o200k_base, drawn from low-collision ranges, excludes all supported-script codepoints) + input pre-scan escaper so collisions stay reversible. Token-based metrics primary (pure-Python estimator default, exact via optional tiktoken).

## 4-Layer Semantic Layer Cake (LIFO: encode L1→L4, decode L4→L1)
- **L1 Entropy:** reversible multilingual stopword/particle markers (BPE-safe single tokens), code/markdown/raw-string region guards. LLMLingua genuine pruning = separate opt-in LOSSY path.
- **L2 Structural:** extended static key-map (v1's ~105 preserved + ~200 new) + cross-lingual camelCase noun-chain agglutination + dynamic 1–2 char key markers via sentinel registry.
- **L3 Paninian (ground floor):** v1 dictionary + key_map UNCHANGED (byte-identical at level="v1") + Samāsa compounding + Sandhi pipe-boundary whitespace blend + Kāraka preposition→suffix.
- **L4 Huffman:** BPE-safe fixed glyph table (default, stateless) + dynamic per-payload table (opt-in, carries envelope). All glyphs verified single-token.

## Backward compatibility (100% preserved)
- `SanskritMeshCompiler` default `level="v1"` → byte-identical v1 output. All v1 methods + attributes (`key_map`,`reverse_key_map`,`dictionary`,`reverse_dictionary`,`sorted_eng_keys`) preserved. `compress_hook(sender,message,recipient,silent)` frozen. `from compiler import …` / `from middleware import …` via shims. Core `install_requires=[]`.

## New additive surface
- `HyperCompiler(level=..., huffman="fixed"|"dynamic"|"off", entropy_prune=False)`.
- `level` values: v1, entropy, structural, paninian, hyper.
- LangChain `BaseDocumentTransformer`, LlamaIndex postprocessor, `AsyncStreamingDecoder`, opt-in LLMLingua pruner under `extras_require[entropy]`.

## Packaging
- `setup.py` → v2.0.0, `install_requires=[]`, `extras_require`: entropy(llmlingua), metrics(tiktoken), langchain, llamaindex, autogen, all. Real `sanskrit_mesh/` package + flat shims `compiler.py`/`middleware.py`.

## Execution order
1. `tables.py` + `linguistics/` (scripts, matrices, glyph pool, escaper)
2. `layers/` (entropy, structural, paninian, huffman — each unit-reversible)
3. `registry.py` + `token_metrics.py`
4. `core/compiler.py` (v1-parity + HyperCompiler orchestrator)
5. shims + integrations + streaming + optional pruner
6. `setup.py`, `validator.py`, `benchmark.py`
7. Run validator (all levels + non-English payloads green) + benchmark (no v1 regression); update docs
8. No inline comments / placeholders / pseudocode / TODO stubs.

## Honesty guards
- Validator asserts BPE token delta ≥ 0 before reporting any ratio (no fake 90%).
- Finite glyph pool → graceful fallback (still lossless) if a payload exceeds it.