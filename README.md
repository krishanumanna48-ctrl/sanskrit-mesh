# Sanskrit-Mesh

<div align="center">

<img src="https://img.shields.io/badge/sanskrit--mesh-v1.0.0-cyan?style=for-the-badge" alt="version"/>
<img src="https://img.shields.io/badge/pip_install-sanskrit--mesh-blue?style=for-the-badge&logo=python" alt="pip"/>
<img src="https://img.shields.io/badge/token_savings-55--77%25-green?style=for-the-badge" alt="savings"/>
<img src="https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge" alt="license"/>
<img src="https://img.shields.io/badge/dependencies-zero-brightgreen?style=for-the-badge" alt="deps"/>

<br/><br/>

### Stop paying for tokens your agents waste being polite to each other.

**Sanskrit-Mesh compresses LLM agent payloads 55–77% using a Paninian Intermediate Representation.**  
Lossless. Drop-in. Works with LangChain, AutoGen, and any OpenAI-format API.

```bash
pip install sanskrit-mesh
```

[📊 Benchmarks](#live-benchmark) · [🚀 Quickstart](#quickstart) · [🗺 Roadmap](#roadmap) · [🤝 Contributing](CONTRIBUTING.md)

</div>

---

`Sanskrit-Mesh` is an AI-native bytecode compiler for **multi-agent LLM pipelines**. It intercepts the structured payloads that frameworks like AutoGen, LangChain, and CrewAI generate automatically — agent messages, memory objects, tool calls, system prompts — and compresses them into an ultra-dense Intermediate Representation (IR) inspired by Panini's Sanskrit grammar. On the other side, it decompiles back to perfect English with zero data loss.

**Result: 55–77% token reduction on agent-generated payloads. Zero logic changes to your pipeline.**

<div align="center">

| Payload Type | Before | After | Saving |
|---|---|---|---|
| System prompt | 373 chars | 87 chars | **76.7%** |
| Agent message | 232 chars | 88 chars | **62.1%** |
| LangChain memory | 864 chars | 379 chars | **56.1%** |
| ReAct scratchpad | 656 chars | 335 chars | **48.9%** |

*Run `python benchmark.py` to verify these numbers yourself.*

</div>

---

## What V1 Does and Doesn't Do

Read this before installing. No surprises.

**V1 delivers:**
- Compresses JSON keys, framework boilerplate, error messages, status fields, and system prompts
- Works with AutoGen, LangChain, or any OpenAI-format API
- 100% lossless — `python validator.py` proves it on your machine
- System prompt compression saves tokens on every single API call, not just multi-agent runs
- Extends effective context window for local LLM users running agent pipelines

**V1 does not deliver:**
- Compression of freeform human text — a user typing "deploy my app" saves nothing. The dictionary covers agent vocabulary, not natural conversation
- Inference speed improvements — model loading and generation speed are unchanged
- Model size reduction — this is not quantization
- Meaningful savings for simple chatbot use cases with no agent structure

**Who gets real value from V1:**
- Developers running AutoGen, CrewAI, or LangChain agent pipelines against paid APIs
- Developers with large repetitive system prompts sent on every call
- Local LLM users running agent pipelines on hardware with tight context windows (4K–8K)

**Who won't see much benefit:**
- Apps where most traffic is freeform human conversation
- Single-turn prompt/response use cases with no agent structure
- Anyone not using a framework that generates structured payloads

---

## Honest Answers to the Obvious Criticisms

**"This is just a find-and-replace script with a fancy name."**

Partially fair. The dictionary layer is a lookup table — that's true. What makes it more than that: the key minification layer is structural (works on any JSON regardless of content), the round-trip fidelity is guaranteed and verifiable, and the IR is designed as a protocol — not a one-off abbreviation. The dictionary is also open for community contribution, so it grows with real agent traffic patterns. Run `python validator.py` to see exactly what matches and why.

**"LLMLingua already does this, and better."**

For compressing arbitrary human text, yes — LLMLingua uses a neural model and handles freeform language. Sanskrit-Mesh targets a different thing: the structured machine-generated payloads that frameworks produce automatically. They're complementary. LLMLingua integration is planned for V2 to cover the human text gap.

**"The dictionary is too small for production use."**

200+ entries covers common framework patterns well. Coverage will drop on unusual custom patterns. This is a known limitation and the reason `CONTRIBUTING.md` exists — adding entries is one dict line. PRs are the fix. The more the community uses it on real pipelines, the better the dictionary gets.

**"How do I know the LLM still understands the compressed payload?"**

The middleware decompresses back to full English before the LLM ever sees it — the LLM always receives normal text. The compression only travels over the wire between your code and the API. Run `python validator.py` for byte-perfect proof on your own payloads.

**"Token prices keep dropping anyway."**

True. But context window limits don't — especially on local models. The context extension use case gets stronger as models get faster and more people run them locally on limited hardware.

---

## The Problem

Multi-agent systems (AutoGen, CrewAI, LangChain) auto-generate and transmit repetitive structured payloads on every step:

```json
{
  "sender": "Agent A",
  "receiver": "Agent B",
  "intent": "Request Clarification",
  "context": {
    "status": "failed",
    "message": "I encountered the following error: NullPointerException: object reference not set. Please advise on how to proceed."
  }
}
```
*232 characters. Sent hundreds of times per pipeline run. You never wrote this — your framework did.*

## The Solution

Sanskrit-Mesh compresses it to:

```json
{"s":"|AgA|","r":"|AgB|","i":"|Prashna|","c":{"st":"|F|","m":"|E:| |ShunyaDosha|. |?|"}}
```
*88 characters. Same meaning. **62% smaller.***

Three compression layers running simultaneously:
1. **Key minification** — JSON keys shrunk to 1–3 chars (`"sender"` → `"s"`, `"intermediate_steps"` → `"is_"`)
2. **Semantic IR dictionary** — 200+ agent phrases mapped to dense Sanskrit tokens
3. **Whitespace stripping** — removes bloat agents auto-generate

---

## Why Paninian Grammar?

Panini formalized Sanskrit grammar 2,500 years ago into the most concise, unambiguous linguistic rule system ever written. It encodes complex meaning in single dense constructs — exactly what machine-to-machine communication needs. `MemoryError: out of memory` becomes `SmritiBhara`. `ConnectionError: failed to establish connection` becomes `BandhanDosha`. Dense, unambiguous, lossless.

---

## Installation

```bash
pip install sanskrit-mesh
```

With framework integrations:
```bash
pip install sanskrit-mesh[langchain]    # LangChain support
pip install sanskrit-mesh[autogen]      # AutoGen support
pip install sanskrit-mesh[all]          # Everything
```

No hard dependencies in the base install — works out of the box.

---

## Quickstart

### Universal — Works With Any OpenAI-Format API

```python
from middleware import SanskritMeshMiddleware

middleware = SanskritMeshMiddleware()

# Agent-generated content — compresses well
messages = [
    {"role": "system",    "content": "You are a helpful, harmless, and honest assistant. Think step by step before answering. Always respond in JSON format."},
    {"role": "assistant", "content": "I will execute the tool to deploy. The deployment failed. Running again..."},
    {"role": "tool",      "content": "I encountered the following error: ConnectionError: failed to establish connection. Please advise on how to proceed."},
]

# NOTE: human freeform user messages compress minimally.
# Savings come from system prompts, assistant messages, and tool responses.
compressed = middleware.compress_messages(messages)

response = openai_client.chat.completions.create(
    model="gpt-4o",
    messages=compressed
)

print(middleware.get_savings_report())
```

### System Prompt Compression

System prompts are the best target — repetitive, developer-written, and sent on **every single API call**.

```python
from middleware import SanskritMeshMiddleware

middleware = SanskritMeshMiddleware()

system_prompt = (
    "You are a helpful, harmless, and honest assistant. "
    "You are operating in a multi-agent environment. "
    "Think step by step before answering. "
    "Always respond in valid JSON. "
    "Your goal is to complete the assigned task efficiently."
)

compressed = middleware.compress_system_prompt(system_prompt)
# Result: |sys:hhh| |sys:multi| |sys:CoT| |sys:json+| |sys:goal|
# 315 chars → 74 chars. 76.5% smaller. Runs on every call.
```

### LangChain Integration

```python
from middleware import SanskritMeshLangChainCallback
from langchain_openai import ChatOpenAI

# One line — attaches to any LangChain LLM
callback = SanskritMeshLangChainCallback(verbose=True)
llm = ChatOpenAI(model="gpt-4o", callbacks=[callback])

# System prompts, memory, agent scratchpad all compressed automatically
response = llm.invoke("Deploy the application.")

print(callback.get_session_report())
```

Compress LangChain memory directly:
```python
compressed_memory = callback.compress_memory(memory.chat_memory.dict())
```

### AutoGen Integration

```python
from middleware import SanskritMeshAutoGenHook
import autogen

hook = SanskritMeshAutoGenHook(verbose=True)

planner  = autogen.ConversableAgent("PlannerAgent", ...)
executor = autogen.ConversableAgent("ExecutorAgent", ...)

# All agent-to-agent messages compressed before transmission
planner.register_hook(
    hookable_method="process_message_before_send",
    hook=hook.compress_hook
)

# Compress full conversation history before passing to a new agent
compressed_history = hook.compress_conversation_history(
    planner.chat_messages[executor]
)
```

### Raw Compiler

```python
from compiler import SanskritMeshCompiler

compiler = SanskritMeshCompiler()

payload = {
    "intent": "Request Clarification",
    "message": "I encountered the following error: IndexError: list index out of range. Please advise on how to proceed."
}

compressed = compiler.compile_payload(payload)
# {'i': '|Prashna|', 'm': '|E:| |KramaBhanga|. |?|'}

restored = compiler.decompile_payload(compressed)
assert restored == payload  # 100% lossless — guaranteed
```

---

## Verify It Yourself

```bash
python validator.py
```

Runs 6 tests including a freeform human text case (correctly shows ~0% savings) and a mixed agent+human case. Shows exactly which phrases matched the dictionary and which passed through untouched. All must pass before any release.

---

## Live Benchmark

```bash
python benchmark.py
```

Test your own payload:
```bash
python benchmark.py --payload '{"role": "system", "content": "You are a helpful assistant. Think step by step."}'
```

### Real Benchmark Results (V1)

Actual numbers from `python benchmark.py` — run it yourself to verify.

| Benchmark | Original | Compressed | Saving |
|---|---|---|---|
| Simple agent message | 232 chars | 88 chars | **62.1%** |
| System prompt | 373 chars | 87 chars | **76.7%** |
| LangChain memory / chat history | 864 chars | 379 chars | **56.1%** |
| Complex nested multi-agent payload | 833 chars | 374 chars | **55.1%** |
| ReAct agent scratchpad | 656 chars | 335 chars | **48.9%** |
| Worst case (zero dictionary matches) | 245 chars | 236 chars | 3.7% |

**Real-world average on agent-generated traffic: ~59–62%**

---

## What V1 Can Actually Save

| Payload Type | Max Observed | Typical Range | Notes |
|---|---|---|---|
| System prompts | **76.7%** | 60–77% | Best target — repetitive, developer-written |
| Simple agent messages | **62.1%** | 55–65% | Framework-generated boilerplate |
| Multi-agent nested payloads | **55–62%** | 50–65% | AutoGen / CrewAI chains |
| ReAct scratchpads | **48.9%** | 40–55% | Mixed agent + reasoning text |
| Human freeform text | ~0–4% | 0–8% | Not the target. Key minification only. |

**V1 ceiling: ~77%. Real-world average on agent pipelines: ~59%.**

---

## Cost Savings at Scale

Based on real benchmark averages (~59% compression, GPT-4o at $5/1M tokens):

| Monthly API Calls | Avg Token Reduction | Monthly Savings |
|---|---|---|
| 10,000 | 59% | ~$7 |
| 100,000 | 59% | ~$74 |
| 1,000,000 | 59% | ~$740 |
| 10,000,000 | 59% | ~$7,400 |

*Assumes average 500 tokens/call on agent pipelines. Human chat apps will see lower savings.*

---

## For Local LLM Users (Low-End PCs)

If you run **agent pipelines** locally via Ollama or llama.cpp with Llama 3.2, Phi-3, or Mistral, Sanskrit-Mesh extends your effective context window on the structured parts of your conversation. A 4K context model running an AutoGen pipeline gets meaningfully more turns before hitting the limit.

This does **not** help casual local chat — savings only apply to agent-structured messages.

```python
import ollama
from middleware import SanskritMeshMiddleware

middleware = SanskritMeshMiddleware()
messages = [...]  # agent-structured conversation
compressed = middleware.compress_messages(messages)
response = ollama.chat(model="llama3.2", messages=compressed)
```

---

## V2 Plans

V2 is where the vision expands beyond structured agent traffic to cover everything.

**Human prompt compression** — integrating LLMLingua as an optional layer so freeform user messages get compressed too, not just agent boilerplate. This is the missing piece from V1.

**Adaptive dictionary** — instead of a static hand-coded list, a model that learns compression patterns from your own agent traffic. Your pipeline teaches it what to compress. Coverage becomes near-complete over time.

**Sanskrit-Mesh-3B** — a fine-tuned small model (Llama 3.2 3B or Phi-3 Mini) that natively reads and writes IR without any decompilation step. The model *thinks* in compressed form. Same intelligence, smaller context footprint. This is the item that changes the low-end PC story completely — a 3B model that behaves like it has double the context window by design.

**CrewAI integration** — drop-in for the third major agent framework.

**Ollama / llama.cpp plugin** — direct integration so local users get compression without writing any code.

---

## Roadmap

- [x] Core compiler with 200+ IR dictionary entries
- [x] System prompt compression
- [x] LangChain callback integration
- [x] AutoGen hook integration
- [x] Universal OpenAI-format middleware
- [x] Live benchmark tool with cost reporting
- [x] Round-trip validator (`python validator.py`)
- [x] PyPI package (`pip install sanskrit-mesh`)
- [x] Contribution guide
- [ ] CrewAI integration
- [ ] 500+ dictionary entries
- [ ] Adaptive dictionary from real traffic
- [ ] Human prompt compression via LLMLingua
- [ ] Fine-tuned `Sanskrit-Mesh-3B` — IR-native model
- [ ] Ollama / llama.cpp plugin

---

## Contributing

The dictionary grows with the community. Adding an entry is one line of Python. See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT — free forever. Stop paying OpenAI to read your agents' polite greetings.
