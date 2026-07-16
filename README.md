<div align="center">

# <img src="icon.png" width="40" style="vertical-align:middle"/> **Sanskrit-Mesh**

<img src="logo.png" width="420" alt="Sanskrit-Mesh Logo"/>

<br/><br/>

<p>
<img src="https://img.shields.io/badge/version-2.0.0-8A2BE2?style=for-the-badge&logo=python" alt="v2.0.0"/>
<img src="https://img.shields.io/badge/lossless-verified-00C853?style=for-the-badge" alt="lossless"/>
<img src="https://img.shields.io/badge/token_savings-55--80%25-FF6D00?style=for-the-badge" alt="savings"/>
<img src="https://img.shields.io/badge/dependencies-zero-00BCD4?style=for-the-badge" alt="zero deps"/>
<img src="https://img.shields.io/badge/license-MIT-9C27B0?style=for-the-badge" alt="MIT"/>
</p>

<h3>Stop paying for tokens your agents waste being polite to each other.</h3>

<pre>pip install sanskrit-mesh</pre>

<p>
<a href="#-benchmarks">Benchmarks</a> •
<a href="#-quickstart">Quickstart</a> •
<a href="#-installation">Installation</a> •
<a href="#-v2-features">V2 Features</a> •
<a href="#-roadmap">Roadmap</a>
</p>

<img src="https://img.shields.io/badge/AutoGen-OK-007BFF?style=flat-square"/> 
<img src="https://img.shields.io/badge/LangChain-OK-007BFF?style=flat-square"/> 
<img src="https://img.shields.io/badge/CrewAI-soon-FF6D00?style=flat-square"/> 
<img src="https://img.shields.io/badge/OpenAI-API-OK-007BFF?style=flat-square"/>
<img src="https://img.shields.io/badge/Ollama-OK-007BFF?style=flat-square"/>

</div>

---

## What is Sanskrit-Mesh?

An **AI-native bytecode compiler** for multi-agent LLM pipelines. It intercepts structured payloads — agent messages, memory objects, tool calls, system prompts — and compresses them into a dense Intermediate Representation (IR) inspired by Panini's Sanskrit grammar. On the other side, it decompiles back to perfect English with **zero data loss**.

| What | Before | After | Saving |
|---|---|---|---|
| System prompt | 118 chars | 30 chars | **74.6%** |
| Agent handoff | 232 chars | 88 chars | **62.1%** |
| LangChain memory | 323 chars | 136 chars | **57.9%** |
| Freeform text | 108 chars | 108 chars | *0%* |

---

## Who Benefits

<table>
<tr>
<td width="50%">

<b>Running agent pipelines against paid APIs?</b>

- AutoGen, CrewAI, LangChain — **any framework**
- 55-80% fewer tokens = **real cost savings**
- System prompts compressed on every call
- `pip install` and done

</td>
<td width="50%">

<b>Running local LLMs with tight context windows?</b>

- Ollama, llama.cpp, LM Studio
- 4K-8K context models get **more turns**
- Agent structures compressed = **room for real content**
- No quantization or model changes needed

</td>
</tr>
</table>

---

## Highlights

- **One compiler** — `SanskritMeshCompiler(level="v1"|"hyper")` — V1 is default, V2 adds layers
- **Auto-learning** — monitors your traffic, promotes frequent phrases to dictionary entries
- **Lossless verified** — `python -m unittest discover -v tests/` proves it on your machine
- **Zero dependencies** — pure Python, works anywhere
- **Multilingual** — English, Spanish, French, German, Italian, Portuguese, Hindi, Japanese, Arabic stopword maps

---

## Quickstart

### Raw Compiler

```python
from sanskrit_mesh import SanskritMeshCompiler

compiler = SanskritMeshCompiler()

payload = {
    "intent": "Request Clarification",
    "message": "I encountered an error: IndexError: list index out of range."
}

compressed = compiler.compile_payload(payload)
# {'i': '|Prashna|', 'm': '|E:| |KramaBhanga|. |?|'}

restored = compiler.decompile_payload(compressed)
assert restored == payload  # 100% lossless
```

### OpenAI-Format API

```python
from sanskrit_mesh import SanskritMeshCompiler

compiler = SanskritMeshCompiler()
messages = [{"role": "system", "content": "You are a helpful assistant."}]

compressed = [compiler.compile_payload(m) for m in messages]
# response = openai.chat.completions.create(messages=compressed, ...)
# restored = [compiler.decompile_payload(m) for m in response]
```

### V2 with Auto-Learning

```python
from sanskrit_mesh import SanskritMeshCompiler

compiler = SanskritMeshCompiler(level="paninian")

for payload in agent_traffic:
    compressed = compiler.compile_payload(payload)
    decompressed = compiler.decompile_payload(compressed)
    # After 100+ payloads:
    promoted = compiler.learn_and_promote(top_n=10)
```

### Framework Integrations

```python
# LangChain
from sanskrit_mesh.integrations.langchain_plugin import SanskritMeshLangChainCallback

# AutoGen  
from sanskrit_mesh.integrations.autogen_plugin import SanskritMeshAutoGenHook
```

---

## Installation

```bash
pip install sanskrit-mesh
pip install sanskrit-mesh[langchain]   # with LangChain
pip install sanskrit-mesh[autogen]     # with AutoGen
pip install sanskrit-mesh[all]         # everything
```

---

## V2 Features

<table>
<tr>
<td><b>Auto-Learning Dictionary</b></td>
<td>Monitors real traffic, scores n-grams by token savings, auto-promotes top phrases to dictionary entries. Persists across restarts.</td>
</tr>
<tr>
<td><b>Numeric Compression</b></td>
<td>Lossless timestamps (epoch -> base-62), UUIDs, large integers with suffix notation. Opt-in.</td>
</tr>
<tr>
<td><b>Entropy / Huffman</b></td>
<td>Multilingual stopword maps + fixed/dynamic Huffman encoding. Opt-in via <code>level="entropy"|"hyper"</code>.</td>
</tr>
<tr>
<td><b>Dynamic Key Registry</b></td>
<td>Unknown JSON keys get 1-2 char sentinels automatically.<br>Key maps: 105 static (V1) + 260 extended (V2).</td>
</tr>
</table>

---

## Benchmarks

| Payload | Original | V1 | V1% | V2 (hyper) | V2% |
|---|---|---|---|---|---|
| Agent handoff | 232 | 88 | **62.1%** | 88 | **62.1%** |
| System prompt | 118 | 30 | **74.6%** | 30 | **74.6%** |
| LangChain memory | 323 | 136 | **57.9%** | 136 | **57.9%** |
| Freeform text | 108 | 108 | 0% | 123 | -13.9% |

```
$ python tests/benchmark.py
$ python -m unittest discover -v tests/
```

### Monthly Savings (GPT-4o, $5/1M tokens, avg 60% reduction)

| Calls | Saved | Calls | Saved |
|---|---|---|---|
| 10K | ~$7 | 1M | ~$740 |
| 100K | ~$74 | 10M | ~$7,400 |

---

## Roadmap

- [x] Core compiler with 200+ IR dictionary entries
- [x] System prompt compression
- [x] LangChain + AutoGen integrations
- [x] Round-trip validator
- [x] **Auto-learning dictionary (V2)**
- [x] **Numeric/timestamp compression (V2)**
- [ ] CrewAI integration
- [ ] 500+ dictionary entries
- [ ] Human prompt compression via LLMLingua
- [ ] Fine-tuned Sanskrit-Mesh-3B model
- [ ] Ollama / llama.cpp plugin

---

## Project Structure

```text
sanskrit_mesh/          # installable package
tests/                  # validator, benchmark, learning tests
examples/               # LangChain, LlamaIndex demos
docs/                   # product spec, release checklist
tools/                  # table validation
.github/workflows/      # CI
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) — one line in `tables.py` adds a dictionary entry.

---

## License

**MIT** — free forever. Stop paying OpenAI to read your agents' polite greetings.