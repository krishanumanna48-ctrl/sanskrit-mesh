# Contributing to Sanskrit-Mesh

The dictionary is the heart of Sanskrit-Mesh. The more phrases it covers, the higher the real-world compression. Every contribution directly reduces token costs for everyone using it.

---

## Easiest Way to Contribute — Add Dictionary Entries

Open `compiler.py` and find the `self.dictionary` dict. Add your phrase:

```python
# Pattern: "full English phrase": "ShortToken"
"Your phrase here": "YourToken",
```

**Rules for good entries:**
1. The phrase must appear verbatim in real agent traffic (LangChain, AutoGen, CrewAI, OpenAI function calls, etc.)
2. The token must be unique — check existing entries first
3. Longer phrases = more savings. Prioritize sentences over single words.
4. Sanskrit-inspired tokens preferred for agent intents and errors. Short ASCII tokens fine for status/structural phrases.
5. Add it to the right section (errors, intents, system prompts, filler phrases, etc.)

**Example PR — adding LangChain ReAct patterns:**
```python
# In self.dictionary:
"I need to use the following tool:": "tool_use>",
"The tool returned the following result:": "tool_ret:",
"Based on the observation, I will now:": "obs_act>",
```

---

## How to Add a New Key Mapping

Open `compiler.py` and find `self.key_map`. Add your key:

```python
"your_json_key": "yk",   # keep it 1-3 chars, must be unique
```

Common targets: any JSON key that appears frequently in your framework's output.

---

## How to Test Your Addition

Run the validator to confirm 100% lossless round-trip:

```bash
python validator.py
```

Run the benchmark to see your savings improvement:

```bash
python benchmark.py
```

Both must pass before submitting a PR.

---

## PR Checklist

- [ ] `python validator.py` — all tests pass
- [ ] `python benchmark.py` — savings % didn't decrease
- [ ] Entries added to the correct section with a comment
- [ ] Token is unique (no duplicates in `self.dictionary`)
- [ ] Phrase sourced from real agent framework output (mention which framework in PR description)

---

## Other Ways to Contribute

- **Bug reports** — open an issue with the payload that caused the problem
- **Framework integrations** — CrewAI, LlamaIndex, Haystack, DSPy integrations welcome
- **Benchmarks** — run `benchmark.py` on your real production payloads and share the numbers in an issue
- **Documentation** — usage examples, tutorials, blog posts

---

## What We're Prioritizing for V1.1

- [ ] CrewAI drop-in integration
- [ ] 500+ dictionary entries (currently 200+)
- [ ] LlamaIndex memory compressor
- [ ] Payload auto-detection (skip compression when savings < 5%)

If you want to work on any of these, open an issue first so we can coordinate.
