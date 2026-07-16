# <img src="icon.png" width="40" style="vertical-align:middle"/> Sanskrit-Mesh

<div align="center">

<img src="logo.png" width="400" alt="Sanskrit-Mesh Logo"/>

<br/><br/>

<img src="https://img.shields.io/badge/sanskrit--mesh-v2.0.0-cyan?style=for-the-badge" alt="version"/>
<img src="https://img.shields.io/badge/pip_install-sanskrit--mesh-blue?style=for-the-badge&logo=python" alt="pip"/>
<img src="https://img.shields.io/badge/token_savings-55--80%25-green?style=for-the-badge" alt="savings"/>
<img src="https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge" alt="license"/>
<img src="https://img.shields.io/badge/dependencies-zero-brightgreen?style=for-the-badge" alt="deps"/>

<br/><br/>

<h3>Stop paying for tokens your agents waste being polite to each other.</h3>

<p>
Sanskrit-Mesh V2 compresses LLM agent payloads 55-80% using a Paninian Intermediate Representation.<br/>
Lossless. Drop-in. Single compiler. Auto-learning improves with your traffic.
</p>

<pre>pip install sanskrit-mesh</pre>

<p>
<a href="#live-benchmark">Benchmarks</a> |
<a href="#quickstart">Quickstart</a> |
<a href="#roadmap">Roadmap</a> |
<a href="CONTRIBUTING.md">Contributing</a>
</p>

</div>

---

`Sanskrit-Mesh` is an AI-native bytecode compiler for **multi-agent LLM pipelines**. It intercepts structured payloads that frameworks like AutoGen, LangChain, and CrewAI generate automatically — agent messages, memory objects, tool calls, system prompts — and compresses them into an ultra-dense Intermediate Representation (IR) inspired by Panini's Sanskrit grammar. On the other side, it decompiles back to perfect English with zero data loss.

**Result: 55-80% token reduction on agent-generated payloads. Zero logic changes to your pipeline.**

| Payload Type | Before | After | Saving |
|---|---|---|---|
| System prompt | 118 chars | 30 chars | **74.6%** |
| Agent message | 232 chars | 88 chars | **62.1%** |
| LangChain memory | 323 chars | 136 chars | **57.9%** |
| Freeform text | 108 chars | 108 chars | *0% (no agent structure)* |

*Run `python tests/benchmark.py` to verify on your machine.*

---

## What It Does and Doesn't Do

**Delivers:**
- Compresses JSON keys, framework boilerplate, error messages, status fields, and system prompts
- Works with AutoGen, LangChain, or any OpenAI-format API
- 100% lossless — `python -m unittest discover -v tests/` proves it
- System prompt compression saves tokens on every single API call
- Extends effective context window for local LLM users running agent pipelines
- V2 adds auto-learning dictionary, numeric compression, and opt-in entropy/huffman layers

**Does not deliver:**
- Compression of freeform human text — a user typing "deploy my app" saves nothing
- Inference speed improvements — model loading and generation speed are unchanged
- Meaningful savings for simple chatbot use cases with no agent structure

**Who gets real value:**
- Developers running AutoGen, CrewAI, or LangChain agent pipelines against paid APIs
- Developers with large repetitive system prompts sent on every call
- Local LLM users running agent pipelines on hardware with tight context windows (4K-8K)

---

## Quickstart

### Universal — Works With Any OpenAI-Format API

```python
from sanskrit_mesh import SanskritMeshCompiler

compiler = SanskritMeshCompiler()

messages = [
    {"role": "system",    "content": "You are a helpful, harmless, and honest assistant. Think step by step before answering. Always respond in JSON format."},
    {"role": "assistant", "content": "I will execute the tool to deploy. The deployment failed. Running again..."},
    {"role": "tool",      "content": "I encountered the following error: ConnectionError: failed to establish connection. Please advise on how to proceed."},
]

compressed = [compiler.compile_payload(m) for m in messages]

response = openai_client.chat.completions.create(
    model="gpt-4o",
    messages=compressed,
)

original = [compiler.decompile_payload(m) for m in compressed]
```

### System Prompt Compression

```python
from sanskrit_mesh import SanskritMeshCompiler

compiler = SanskritMeshCompiler()

system_prompt = (
    "You are a helpful, harmless, and honest assistant. "
    "You are operating in a multi-agent environment. "
    "Think step by step before answering. "
    "Always respond in valid JSON. "
    "Your goal is to complete the assigned task efficiently."
)

compressed = compiler.compile_text(system_prompt)
# 315 chars to 74 chars. 76.5% smaller.
```

### LangChain Integration

```python
from sanskrit_mesh.integrations.langchain_plugin import SanskritMeshLangChainCallback
from langchain_openai import ChatOpenAI

callback = SanskritMeshLangChainCallback(verbose=True)
llm = ChatOpenAI(model="gpt-4o", callbacks=[callback])

response = llm.invoke("Deploy the application.")
print(callback.get_session_report())
```

### AutoGen Integration

```python
from sanskrit_mesh.integrations.autogen_plugin import SanskritMeshAutoGenHook
import autogen

hook = SanskritMeshAutoGenHook(verbose=True)

planner  = autogen.ConversableAgent("PlannerAgent", ...)
executor = autogen.ConversableAgent("ExecutorAgent", ...)

planner.register_hook(
    hookable_method="process_message_before_send",
    hook=hook.compress_hook
)
```

### Raw Compiler

```python
from sanskrit_mesh import SanskritMeshCompiler

compiler = SanskritMeshCompiler()

payload = {
    "intent": "Request Clarification",
    "message": "I encountered the following error: IndexError: list index out of range. Please advise on how to proceed."
}

compressed = compiler.compile_payload(payload)
# {'i': '|Prashna|', 'm': '|E:| |KramaBhanga|. |?|'}

restored = compiler.decompile_payload(compressed)
assert restored == payload  # 100% lossless
```

### V2 Auto-Learning

```python
from sanskrit_mesh import SanskritMeshCompiler

# Enable V2 layers with auto-learning
compiler = SanskritMeshCompiler(level="paninian")

for payload in agent_traffic:
    compressed = compiler.compile_payload(payload)
    compressed = compiler.decompile_payload(compressed)
    # After 100+ payloads, call:
    promoted = compiler.learn_and_promote(top_n=10)
    print(f"Learned {len(promoted)} new phrases")
```

---

## Installation

```bash
pip install sanskrit-mesh
```

With framework integrations:

```bash
pip install sanskrit-mesh[langchain]
pip install sanskrit-mesh[autogen]
pip install sanskrit-mesh[all]
```

No hard dependencies in the base install.

---

## V2 Features

- **Auto-learning dictionary** — monitors traffic and promotes frequent phrases to dictionary entries
- **Numeric/timestamp compression** — optional lossless layer for dates, UUIDs, and large ints
- **Opt-in entropy/Huffman layers** — `level="entropy"` or `level="hyper"` for additional compression
- **Dynamic key registry** — compresses unknown keys on-the-fly with 1-2 char sentinels
- **Multilingual stopword maps** — English, Spanish, French, German, Italian, Portuguese, Hindi, Japanese, Arabic

---

## Cost Savings at Scale

Based on real benchmark averages, GPT-4o at $5/1M tokens:

| Monthly API Calls | Avg Token Reduction | Monthly Savings |
|---|---|---|
| 10,000 | 60% | ~$7 |
| 100,000 | 60% | ~$74 |
| 1,000,000 | 60% | ~$740 |
| 10,000,000 | 60% | ~$7,400 |

---

## For Local LLM Users

Running agent pipelines locally via Ollama or llama.cpp? Sanskrit-Mesh extends your effective context window on the structured parts of your conversation. A 4K context model running an AutoGen pipeline gets more turns before hitting the limit.

```python
import ollama
from sanskrit_mesh import SanskritMeshCompiler

compiler = SanskritMeshCompiler()
messages = [...]
compressed = [compiler.compile_payload(m) for m in messages]
response = ollama.chat(model="llama3.2", messages=compressed)
```

---

## Roadmap

- [x] Core compiler with 200+ IR dictionary entries
- [x] System prompt compression
- [x] LangChain callback integration
- [x] AutoGen hook integration
- [x] Universal OpenAI-format middleware
- [x] Round-trip validator
- [x] PyPI package (`pip install sanskrit-mesh`)
- [x] Adaptive dictionary from real traffic (V2)
- [x] Numeric/timestamp compression (V2)
- [ ] CrewAI integration
- [ ] 500+ dictionary entries
- [ ] Human prompt compression via LLMLingua
- [ ] Fine-tuned Sanskrit-Mesh-3B model
- [ ] Ollama / llama.cpp plugin

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, test commands, and how to add dictionary entries.

## License

MIT — free forever. Stop paying OpenAI to read your agents' polite greetings.

## Project Structure

```text
sanskrit_mesh/          # installable package
tests/                  # tests, validator, benchmark
examples/               # framework integrations
docs/                   # product/release docs
tools/                  # maintenance scripts
.github/workflows/      # CI
README.md
CONTRIBUTING.md
setup.py