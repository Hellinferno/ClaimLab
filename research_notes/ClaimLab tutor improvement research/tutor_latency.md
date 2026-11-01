# Reducing real and perceived latency of ClaimLab's tool-calling live tutor turn

Scope: one ClaimLab tutor turn is up to 7 sequential `POST https://api.meta.ai/v1/chat/completions` calls to `muse-spark-1.3` (function tools, `tool_choice: "auto"`, `max_tokens: 8192`). The browser request blocks synchronously, with no streaming. Baseline figures come from the brief: single observations on 31 Oct 2026. Whole turns took 17-46 s, each model round trip 4-23 s, the final `present_lesson` reply 12-23 s, experiment code-writing about 8-10 s, and a separate `assess_answer` reply about 22 s.

Local code facts were checked in this research (31 Oct 2026, files under `D:/Meta hackathon/backend`):
- The provider payload in `backend/src/claimlab/services/agent_orchestrator.py` (about lines 776-784) sends `model`, `messages`, `tools`, `tool_choice: "auto"` and `max_tokens: 8192`. It sets no `reasoning_effort`, `stream`, `response_format` or `prompt_cache_key`.
- The `tools` list is rebuilt on every iteration by `live_tools(web=..., assess=..., final=..., excerpts=..., experiments=...)`, so the tool set can change between rounds of one turn.
- The code already handles several `tool_calls` in one reply. It sorts `present_lesson` last, but the calls run one after another.
- An SSE endpoint `GET /api/v1/jobs/{job_id}/events` already exists in `backend/src/claimlab/api.py` (about lines 1118-1152). It polls the `JobEvent` table every 0.5 s through a `db` session that comes from `Depends(get_db)`.
- `get_db` in `backend/src/claimlab/database.py` is a `yield` dependency that calls `db.close()` in `finally`. SQLite WAL is already on.
- Installed versions: FastAPI 0.115.4, Starlette 0.41.3, Pydantic 2.9.2. `pyproject.toml` pins `fastapi>=0.115.0` and `pydantic>=2.9.0`.
- A server-only job event holds the tutor-written check's answer key, which is "never streamed" (comment at `agent_orchestrator.py` line 54).

---

## Q1. What does Meta's developer API (Meta Model API / muse-spark-1.3) document for streaming, tool-call streaming, parallel tools, reasoning controls, caching, structured outputs, faster tiers and latency?

### Takeaway
Meta's current developer platform is the "Meta Model API" at dev.meta.ai, base URL `https://api.meta.ai/v1`. It documents most of the levers this architecture needs:
- SSE streaming on Chat Completions
- incremental tool-call arguments
- `parallel_tool_calls` (on by default)
- `reasoning_effort` from `minimal` to `xhigh`/`max`
- automatic prefix prompt caching with an optional `prompt_cache_key`
- `response_format` JSON-schema structured output with constrained decoding

Two constraints matter. `tool_choice` only accepts `"auto"`, so the final `present_lesson` call cannot be forced. On Chat Completions the model does not carry its reasoning across turns: every round of the 7-call loop reasons from scratch. Meta publishes no latency, time-to-first-token or throughput figures, and no smaller or faster hosted tier.

### Cited Findings
**Platform and status**
- The Meta Model API launched in public preview on 8 Jul 2026, for US developers, with self-serve sign-up. It is OpenAI-SDK-compatible with base URL `https://api.meta.ai/v1` and offers three protocols:
  - Chat Completions: stateless, you manage the message list.
  - Responses: server-held state via `previous_response_id`.
  - Messages: Anthropic-format.
  — [Meta dev blog, "Build with Muse Spark"](https://dev.meta.ai/resources/blog/build-with-muse-spark/)
- Pay-as-you-go pricing "starts at $1.25 input / $4.25 output per million tokens". Reasoning tokens are billed as output. — [Meta dev blog](https://dev.meta.ai/resources/blog/build-with-muse-spark/); [Meta docs: Reasoning](https://dev.meta.ai/docs/reasoning)
- The old `developer.meta.com/ai/...` URLs now 301-redirect to `dev.meta.ai`. Searches turned up no current "Llama API" (llama.developer.meta.com) documentation. Treat Llama-API-era (2025) guidance as possibly outdated and superseded. — observed redirect from [developer.meta.com blog URL](https://developer.meta.com/ai/resources/blog/build-with-muse-spark/)
- A third party describes Muse Spark API documentation as sparse, with no detailed model card (written for Spark 1.1). — [DataCamp](https://www.datacamp.com/blog/muse-spark-1-1)

**Streaming (verified in official docs)**
- Chat Completions supports `stream=True`, which returns "server-sent events: a sequence of chunks you consume as they arrive". Text is in `chunk.choices[0].delta.content` and can be `None`. The final chunk sets `finish_reason`. Keep-alive chunks occur. — [Meta cookbook: Streaming responses](https://dev.meta.ai/docs/cookbook/streaming-responses)
- Usage is omitted from streams unless you pass `stream_options={"include_usage": True}`. The last chunk then carries `usage`, and its `choices` may be empty. — [Meta cookbook: Streaming responses](https://dev.meta.ai/docs/cookbook/streaming-responses)
- "Tool-call arguments arrive as deltas too."
  - Chat Completions: "accumulate `tool_calls` deltas across chunks by `index`". Meta does not list the exact delta field names.
  - Responses API: consume `response.function_call_arguments.delta` events and finalize on `response.function_call_arguments.done`.
  — [Meta cookbook: Streaming](https://dev.meta.ai/docs/cookbook/streaming-responses); [Meta docs: Tool calling](https://dev.meta.ai/docs/tool-calling)
- Muse Spark "reasons internally, so a reasoning-heavy prompt can pause before content streams". "The deltas carry the answer text, not the reasoning." Total generation time stays "the same", but the user "sees the first words sooner". A retry "restarts the stream from the beginning", so keep partial text. — [Meta cookbook: Streaming](https://dev.meta.ai/docs/cookbook/streaming-responses)

**Tool calling constraints (verified)**
- `tool_choice` only supports `"auto"`. `"none"`, `"required"` and named-function choices return HTTP 400, so apps "must handle both a tool call and a plain text response". — [Meta docs: Tool calling](https://dev.meta.ai/docs/tool-calling); [Meta cookbook: Tool/function calling](https://dev.meta.ai/docs/cookbook/tool-function-calling)
- `parallel_tool_calls` defaults to `true`, so one assistant message can contain several `tool_calls`. You return one `tool` message per `tool_call_id`. It works on both Chat Completions and Responses. — [Meta docs: Tool calling](https://dev.meta.ai/docs/tool-calling)
- `strict` defaults to `false`. With `strict: true` the server validates the schema subset (`additionalProperties: false`, all properties `required`). The docs say generated arguments are still "not guaranteed to match the schema". — [Meta docs: Tool calling](https://dev.meta.ai/docs/tool-calling)
- Meta's own docs "recommend Responses for tool calling and multi-turn agents because it preserves reasoning across tool turns". — [Meta docs: Tool calling](https://dev.meta.ai/docs/tool-calling); [Meta docs: Chat Completions protocol](https://dev.meta.ai/docs/protocols/chat-completions)

**Reasoning controls (verified)**
- Parameter placement: top-level `reasoning_effort` on Chat Completions, `reasoning.effort` on Responses.
  - Values: `minimal`, `low`, `medium`, `high`, `xhigh`. `max` works only on `muse-wonder-1.0` and `muse-spark-1.3`, not the contributor model. `none` returns HTTP 400 because "Muse Spark always reasons".
  - If you omit it, "the model still reasons at a model-determined level".
  — [Meta docs: Reasoning](https://dev.meta.ai/docs/reasoning); [Meta docs: Chat Completions protocol](https://dev.meta.ai/docs/protocols/chat-completions)
- "Higher effort means more reasoning — and more reasoning tokens, latency, and cost." For direct-answer tasks, use `"low"` "for faster responses at lower cost", and "use the lowest level that gives you acceptable results". No numbers are given. — [Meta docs: Reasoning](https://dev.meta.ai/docs/reasoning)
- Reasoning tokens count toward `max_tokens` (Chat Completions) or `max_output_tokens` (Responses). They are reported as `usage.completion_tokens_details.reasoning_tokens`. — [Meta docs: Reasoning](https://dev.meta.ai/docs/reasoning)
- On Chat Completions, "reasoning cannot carry across turns for external keys": `reasoning_content` is "redacted to empty", so "each turn reasons from scratch". The Responses API keeps reasoning through `previous_response_id`, or statelessly through `include: ["reasoning.encrypted_content"]`, and this works across tool-loop turns. — [Meta docs: Reasoning](https://dev.meta.ai/docs/reasoning)
- Conflicting third-party evidence: a harn-vm capability config from a Sept 2026 probe reported that `low` and `high` spent an identical 197 reasoning tokens on a trivial prompt. This is a search-result snippet that I did not fetch or verify. — [harn-vm Meta catalog (docs.rs)](https://docs.rs/crate/harn-vm/0.10.170/source/src/llm/catalog_sources/60-models/12-meta.toml)

**Prompt caching (verified, with gaps)**
- Caching is automatic: "there is no flag to turn on and no cache key to manage". The server "matches from the start of your tokenized prompt", and "the first token that differs ends the match". Guidance is to "Put stable content first" and keep the prefix "byte-for-byte identical".
  - An optional stable `prompt_cache_key` "routes same-prefix requests to the same backend and raises the hit rate". "A unique key per user or session … lowers your hit rate."
  - `prompt_cache_retention` takes `"in_memory"` (the default) or `"24h"`, and is "a hint, not a guarantee".
  - Hits show in `usage.prompt_tokens_details.cached_tokens`.
  — [Meta cookbook: Prompt caching](https://dev.meta.ai/docs/cookbook/prompt-caching); [Meta docs: Chat Completions protocol](https://dev.meta.ai/docs/protocols/chat-completions)
- Cached input is priced at $0.15 per 1M tokens for Spark 1.3 (third party; Meta's pricing page was not fetched). — [OpenClaw Meta provider docs](https://docs.openclaw.ai/providers/meta)
- Meta documents no latency benefit, minimum prefix length or TTL beyond the two retention options. — [Meta cookbook: Prompt caching](https://dev.meta.ai/docs/cookbook/prompt-caching)

**Structured output (verified)**
- Chat Completions accepts `response_format={"type": "json_schema", "json_schema": {...}}`, and `client.beta.chat.completions.parse(..., response_format=PydanticModel)` works. "Constrained decoding guarantees the output conforms."
  - Recommended: `additionalProperties: false` and `enum` for closed sets. "Recursive schemas are rejected" with HTTP 400.
  - On Responses the parameter is `text.format`; sending `response_format` there returns HTTP 400.
  - The recipe points to the streaming recipe for "streaming a structured response as it generates".
  — [Meta cookbook: Structured output](https://dev.meta.ai/docs/cookbook/structured-output)
- The docs do not say whether `response_format` and `tools` can be combined in one request. — [Meta cookbook: Structured output](https://dev.meta.ai/docs/cookbook/structured-output)

**Unsupported or deprecated parameters (verified)**
- On Chat Completions, `max_tokens` is a "deprecated alias"; use `max_completion_tokens`.
- `prediction` (predicted outputs) is unsupported on reasoning models.
- `verbosity`, `stop`, `logit_bias`, `logprobs`, `frequency_penalty`/`presence_penalty` and `n>1` are unsupported or rejected.
- `system` is merged with `developer`.
— [Meta docs: Chat Completions protocol](https://dev.meta.ai/docs/protocols/chat-completions)

**Model tiers and latency figures**
- Hosted models: `muse-wonder-1.0` (preview), `muse-spark-1.3` ("Recommended for new work"), `muse-spark-1.3-contributor`, `muse-spark-1.2`, `muse-spark-1.2-contributor` and `muse-spark-1.1`. All have a 1,048,576-token context window.
  - Meta lists no max output size and no "tokens-per-second or time-to-first-token figures" for any model.
  - Contributor mode is priced lower but not described as faster.
  - Muse Glimmer (distilled from Spark) and Muse Spark Open (816B MoE, 42B active) are open-weight and self-hosted only, not on the hosted API.
  — [Meta docs: Models](https://dev.meta.ai/docs/models)
- The cookbook has a "glimmer-api-agent" recipe: a local Muse Glimmer agent "that asks before escalating to Muse Spark". This is the only documented small-model pattern. — [Meta cookbook index](https://dev.meta.ai/docs/cookbook)
- Contributor models come with data-use terms, and users are told not to submit sensitive or personal information. — [OpenClaw Meta provider docs](https://docs.openclaw.ai/providers/meta)

### Inferences
- The "each turn reasons from scratch" rule probably compounds latency in ClaimLab's loop. Each of up to 7 rounds re-derives its plan before emitting a tool call, which likely explains part of the 4-23 s per-round cost. Moving the loop to the Responses API (`previous_response_id`, or `store:false` plus encrypted reasoning replay) is Meta's own recommendation for tool loops. The size of the gain is unmeasured.
- ClaimLab never sets `reasoning_effort`, so every call reasons at a "model-determined level". This is the cheapest lever to test: one line per call type, measured through `reasoning_tokens` and wall time. The harn-vm snippet means the effect cannot be assumed; it has to be measured on real lesson prompts.
- Because `tool_choice` cannot be `"required"` or named, the most reliable final step is a call with no tools and `response_format` set to the lesson JSON schema. Constrained decoding guarantees the shape and removes the risk of one more tool round. Whether that call streams cleanly must be probed.
- `live_tools(...)` changes the tool list between iterations of one turn. If the server serializes tool definitions ahead of the messages, as OpenAI-compatible stacks usually do, each change ends the cached prefix early. A constant tool list, with restrictions enforced by the tool handlers returning error strings, would keep the prefix byte-stable. This is unverified for Meta's serializer.
- The old `max_tokens: 8192` still works as an alias. Renaming it to `max_completion_tokens` is hygiene, not a speed change.

### Gaps
- Meta publishes no official TTFT, tokens/sec or latency percentiles for any model. A local probe is the only source.
- I did not fetch the exact Chat Completions `delta.tool_calls` field names. The OpenAI shape (`choices[0].delta.tool_calls[i].index/id/function.name/function.arguments`) is assumed and needs a probe.
- Rate and concurrency limits (`/docs/pricing-rate-limits`) were not fetched. They matter for parallel or speculative calls.
- The `/docs/prompt-caching` feature page (minimum prefix, latency claims) was not fetched.
- Undocumented: whether `response_format` combines with `tools`; whether streaming works with `response_format`; whether constrained decoding emits keys in schema order.
- Undocumented: whether `reasoning_effort` measurably changes latency on muse-spark-1.3.

---

## Q2. How do production apps stream structured tool-call output so the UI can render the first lesson step before the rest is generated?

### Takeaway
The standard pattern has four parts:
1. Stream the model response with `stream: true`.
2. Accumulate each tool call's `arguments` string by `index`.
3. Run a tolerant partial-JSON parser over the growing buffer after each delta.
4. Emit typed UI events only for fields that are complete.

For ClaimLab, Pydantic 2.9.2 is already installed, and its `pydantic_core.from_json(buf, allow_partial=True)` (available since 2.7) needs no new dependency. Parsing should happen on the server, never in the browser. The `present_lesson` arguments include the check question's answer key, which must never be streamed.

### Cited Findings
- Pydantic's jiter parser supports partial JSON through `from_json(..., allow_partial=True)`, introduced in Pydantic 2.7. The usual flow is to parse the partial string, then validate with `model_validate()`. Caveat: partial mode cannot tell complete `"b": "12"` from incomplete `"b": "12…`. — [Pydantic experimental/partial docs](https://pydantic.dev/docs/validation/dev/concepts/experimental/); [Pydantic v2.7 release](https://pydantic.dev/articles/pydantic-v2-7-release)
- Standalone `jiter` offers `partial_mode`: `False` raises on incomplete input, `True` drops an incomplete last field, and `'trailing-strings'` keeps the incomplete last string, which suits a typing effect. — [jiter-python README](https://github.com/pydantic/jiter/tree/main/crates/jiter-python); [Simon Willison on jiter](https://simonwillison.net/2024/Sep/22/jiter/) (2024, possibly outdated)
- Pure-Python, zero-dependency `partial-json-parser` (promplate) has a JS twin, `partial-json-parser-js`, for client-side parsing. `partial-json-stream` targets streamed tool calls but is new, and its maintenance status is unverified. — [partial-json-parser](https://www.github.com/promplate/partial-json-parser); [partial-json-parser-js](https://github.com/promplate/partial-json-parser-js); [partial-json-stream (PyPI)](https://pypi.org/project/partial-json-stream/)
- The Vercel AI SDK UI message stream protocol is a reference event vocabulary for streaming tool input:
  - `tool-input-start` (`toolCallId`, `toolName`, `inputEncoding` `'json'` or `'text'`)
  - `tool-input-delta` (`inputTextDelta`)
  - `tool-input-available` (`input`)
  - `tool-output-available` (`output`)
  - custom `data-*` parts
  - `reasoning-start/delta/end`
  - `start-step`/`finish-step` per LLM call, and `reset-step` to discard a retried step
  The transport is SSE `data: {json}` ending in `data: [DONE]`. Custom backends must send the header `x-vercel-ai-ui-message-stream: v1`, and a FastAPI example is linked. — [AI SDK stream protocol](https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol)
- LangGraph stream modes: `values`, `updates`, `messages` (token, metadata), `custom` (emitted from inside nodes or tools with `get_stream_writer()`), `checkpoints`, `tasks` and `debug`. This is a reference pattern for "progress from inside a tool". `get_stream_writer` does not work in async code on Python below 3.11. — [LangGraph streaming docs](https://docs.langchain.com/oss/python/langgraph/streaming)
- Meta confirms that tool-call arguments stream as deltas, accumulated by `index` on Chat Completions or through `response.function_call_arguments.delta` on Responses. — [Meta docs: Tool calling](https://dev.meta.ai/docs/tool-calling)

### Inferences
Implementation sketch for ClaimLab (my inference from the above, not a documented Meta recipe):
1. Order the `present_lesson` schema fields as `steps` (array) first, then `whiteboard_items`, then `check_question`, and put the answer key last. Ask in the prompt for steps in order. Generation order usually follows schema or prompt order, which puts step 1 on screen earliest. This is undocumented for Meta and must be verified.
2. On each delta, append to `buf[index]` and run `from_json(buf, allow_partial=True)`. Treat `steps[k]` as final only once `steps[k+1]` exists or the stream ends; this works around the incomplete-last-string caveat. Validate each finished step with the existing Pydantic step model, then emit a `lesson_step` JobEvent with `{k, title, body}`.
3. Strip the answer key and any reviewed-code-only fields on the server. Never forward raw `tool-input-delta` text to the browser: the arguments contain the answer key that ClaimLab already keeps server-only.
4. Whiteboard items can be emitted the same way, so board objects appear progressively.
5. In React, keep `steps` as an array in state keyed by step index. Wrap finished step components in `React.memo` so markdown is not re-parsed for earlier steps on every event. Show a skeleton for "step k+1 being written".
6. Streaming `run_python_experiment` arguments (`inputEncoding: 'text'` style) lets the UI show the numpy code as it is written. That turns the 8-10 s code-writing wait into visible work.
7. Retry semantics: a provider retry restarts the stream (Meta docs). Emit a `lesson_reset` event, like AI SDK's `reset-step`, so the UI drops partial steps.

### Gaps
- I found no published case study measuring time-to-first-rendered-step for streamed tool arguments. The perceived gain has to be measured locally: time to the first `lesson_step` event versus time to the full `present_lesson`.
- I did not verify whether muse-spark emits a long silent reasoning phase before the first argument delta of `present_lesson`. Meta says reasoning "can pause before content streams". If most of the 12-23 s is reasoning, streaming helps less, and effort reduction matters more.

---

## Q3. Background job plus SSE/polling versus a synchronous request for multi-step agent turns; FastAPI StreamingResponse and DB-session pitfalls

### Takeaway
Convert the tutor turn into a job:
1. `POST` creates the job and returns a `job_id` (202).
2. A worker thread runs the loop with its own DB session and writes `JobEvent` rows: phase changes, tool starts and ends, experiment results, `lesson_step`, and `tutor_turn_completed`.
3. The browser subscribes through the existing `/api/v1/jobs/{id}/events` SSE endpoint, resuming with `after` / `id`.

ClaimLab already has the Job and JobEvent tables, the SSE endpoint and WAL. The main fix is session lifetime. On the installed FastAPI 0.115.4, `yield`-dependency cleanup runs before a streaming body is sent, so the existing SSE generator's `Depends(get_db)` session is closed when the generator runs.

### Cited Findings
- Before FastAPI 0.118.0, a `yield` dependency's exit code ran "after the path operation function returned but right before sending the response". A `StreamingResponse` body therefore ran after the session was closed. 0.118.0 changed this so the exit code runs after the response is sent. — [FastAPI advanced dependencies docs](https://fastapi.tiangolo.com/advanced/advanced-dependencies); [FastAPI 0.118.0 release](https://newreleases.io/project/pypi/fastapi/release/0.118.0)
- FastAPI 0.121.0 added `Depends(scope="function")`, which deliberately restores early cleanup and is meant for dependencies used only during auth or validation. Do not use it for a session that a stream reads. — [FastAPI advanced dependencies docs](https://fastapi.tiangolo.com/advanced/advanced-dependencies)
- Workaround from the FastAPI issue tracker: "initiate your resources within the background task (or generator function in the case of streaming)". — [FastAPI issue #11143](https://github.com/tiangolo/fastapi/issues/11143)
- FastAPI 0.135.0 added built-in SSE: `from fastapi.sse import EventSourceResponse` with `response_class=EventSourceResponse` and `yield`. Yielded items are JSON-encoded into `data:`. `ServerSentEvent` objects set `event`, `id` and `retry`. Plain `def` generators are supported. Older tutorials use the third-party `sse-starlette`. — [FastAPI SSE tutorial](https://fastapi.tiangolo.com/tutorial/server-sent-events/)
- LangGraph's `updates` and `custom` modes show the same idea at framework level: stream state deltas and tool-emitted progress rather than block for a final value. — [LangGraph streaming docs](https://docs.langchain.com/oss/python/langgraph/streaming)

### Inferences
**Concrete risk in the current code.** `stream_job_events` captures `db` from `Depends(get_db)` and calls `db.query(...)` and `db.refresh(job)` inside the generator. With FastAPI 0.115.4, `get_db`'s `finally: db.close()` has already run by then. After `close()`, SQLAlchemy expunges `job`, so `db.refresh(job)` will likely raise on the first loop. Verify this with a test; it matches the issue the team already hit. Fix options:
- Open `with SessionLocal() as s:` inside each poll iteration of the generator, re-query the job by id each time, and do not hold ORM objects across yields.
- Or upgrade to FastAPI ≥0.118, where cleanup runs after the response. Even then, per-poll short sessions are safer with SQLite.

**Event-loop blocking.** The SSE generator is `async def` but runs synchronous SQLAlchemy queries, which block the event loop for every connected client. Either make it a plain `def` generator (Starlette iterates sync iterators in a threadpool) or wrap queries in `run_in_threadpool`.

**Worker.** For a hackathon, a `threading.Thread` or `BackgroundTasks` with its own `SessionLocal()`, plus the existing `httpx` client, is enough. Notes:
- Mark jobs `TIMED_OUT` on startup if they were left `RUNNING`, since in-process work dies on restart.
- Use `JobEvent.sequence` plus the SSE `id:` so a reloaded tab resumes. The `after` parameter already supports this.
- This also fits ClaimLab's "pause and return" principle: the turn survives a disconnect.

**Auth.** The browser `EventSource` API cannot send custom headers. If guest auth is header-based, use a cookie or a `fetch()` + `ReadableStream` SSE reader. Check how `get_current_guest` resolves the guest.

**Latency of the transport itself.** A 0.5 s DB poll adds up to 0.5 s per event, which is acceptable for phase events. For token-level `lesson_step` events, either tolerate it or push events through an in-process `queue.Queue`/`asyncio.Queue` keyed by `job_id`, with DB persistence kept for replay.

**Simpler alternative.** Return a `StreamingResponse` directly from the turn POST and read it with `fetch` streaming. This is fewer moving parts, but it ties the turn to one connection, and a dropped connection mid-turn loses the progress view. The job pattern reuses what already exists and is preferable.

**Streaming timeouts.** The current `httpx.Client(timeout=60.0)` applies per read operation. With `client.stream(...)`, a reasoning pause before the first chunk counts against the read timeout, so set an explicit `httpx.Timeout(connect=10, read=60, ...)` and catch timeout errors while keeping partial steps, as Meta's recipe advises.

### Gaps
- I did not verify the exact FastAPI version that first moved cleanup before the response. The commonly cited version is 0.106.0, but only "before 0.118.0" is confirmed by the sources fetched here.
- I did not check whether `get_current_guest` uses cookies or headers, which decides whether native `EventSource` works.

---

## Q4. Speculative and parallel strategies: concurrent tools, split generations, prefetching, per-source caching, fewer output tokens

### Takeaway
The highest-yield moves remove whole sequential model round trips and reduce reasoning and output tokens. Fine-tuning prompts or inputs matters much less. Output generation dominates LLM latency: halving output roughly halves latency, while halving the prompt gains only 1-5%. Every extra sequential call adds a full reasoning-plus-generation round, which is 4-23 s here. Ranked concretely:
1. Fold `assess_answer` into the lesson call, or grade deterministically.
2. Set `reasoning_effort` per call.
3. Execute independent tool calls concurrently.
4. Replace free-form experiment code with parameterized templates.
5. Keep a byte-stable prompt prefix with a per-source cache key.

Speculative prefetching of the next turn is the most costly option and the least certain.

### Cited Findings
- OpenAI's latency guide gives seven principles: "Process tokens faster", "Generate fewer tokens", "Use fewer input tokens", "Make fewer requests", "Parallelize", "Make your users wait less" and "Don't default to an LLM". — [OpenAI latency optimization guide](https://developers.openai.com/api/docs/guides/latency-optimization)
- "Generating tokens is almost always the highest latency step"; "cutting 50% of your output tokens may cut ~50% of your latency", whereas "cutting 50% of your prompt may only result in a 1–5% latency improvement". — [OpenAI latency optimization guide](https://developers.openai.com/api/docs/guides/latency-optimization)
- In the guide's worked example:
  - merging two sequential prompts into one removed a round trip
  - a step that no longer depended on retrieval ran in parallel with it
  - shortening JSON field names and moving explanations out of the output saved 19 output tokens, worth "up to about a second on GPT-4"
  - speculative execution means starting the likely next step early and cancelling it if a check fails
  - the guide warns that splitting or shortening must be validated against quality
  — [OpenAI latency optimization guide](https://developers.openai.com/api/docs/guides/latency-optimization)
- "Don't default to an LLM": hard-code constrained outputs, pre-compute responses for constrained inputs, and use classical caching. — [OpenAI latency optimization guide](https://developers.openai.com/api/docs/guides/latency-optimization)
- Meta: `parallel_tool_calls` is on by default, so the model may return several `tool_calls` in one message, each answered by `tool_call_id` before the next request. — [Meta docs: Tool calling](https://dev.meta.ai/docs/tool-calling)
- Meta prompt caching is prefix-based and automatic. A stable per-prefix `prompt_cache_key` raises hit rate, while a per-session key lowers it. `"24h"` retention keeps the cache warm across idle gaps. — [Meta cookbook: Prompt caching](https://dev.meta.ai/docs/cookbook/prompt-caching)
- Meta: `"low"` effort for direct-answer tasks gives "faster responses at lower cost". — [Meta docs: Reasoning](https://dev.meta.ai/docs/reasoning)
- Meta: predicted outputs (`prediction`) are unsupported on reasoning models, so that output-reuse trick is unavailable. — [Meta docs: Chat Completions protocol](https://dev.meta.ai/docs/protocols/chat-completions)

### Inferences
These are ClaimLab-specific applications.

**1. Remove the separate `assess_answer` round (saves about 22 s on answer turns, based on the brief's single observation).**
- Add an `assessment` object (verdict enum, short rationale, misconception tag) as the first field of the `present_lesson` schema on feedback turns. The model then grades and teaches in one reply.
- For multiple-choice or numeric checks, grade in reviewed code and pass the verdict into the prompt, with no LLM call ("don't default to an LLM").
- This follows the "make fewer requests" pattern from the OpenAI guide.

**2. Per-call `reasoning_effort` (one-line change; must be measured).**
- Suggested starting points: `low` for writing experiment code and composing the lesson, `minimal` for grading, `medium` only for the first planning round if quality drops.
- Log `usage.completion_tokens_details.reasoning_tokens`, `completion_tokens` and wall time for each round to get the first real latency breakdown. This shows whether reasoning or visible output dominates the 12-23 s lesson reply.

**3. Concurrent tool execution.** When one reply contains several non-lesson `tool_calls` (for example `web_search` plus `run_python_experiment`), run them with `concurrent.futures.ThreadPoolExecutor` (the code is sync `httpx`) and append the `tool` messages in the original order. Then add a prompt line asking the model to "issue independent tools in the same reply". The saving is the sum of tool times minus the maximum; web fetches are the big win, while the 1 s sandbox is minor.

**4. Collapse "write code → see result → write lesson" where possible.**
- Offer a small catalogue of reviewed, parameterized experiments (for example `simulate_sampling(n, p, trials)`). The model emits a tiny argument object instead of 8-10 s of numpy code: fewer output tokens and "don't default to an LLM".
- Keep free-form `run_python_experiment` as the fallback.
- Cache experiment code and results per (source, claim, parameters) so repeated demos skip the round entirely.

**5. Stable prefix and per-source cache key.**
- Order every request as: static system and developer instructions, a constant tool list, the source excerpt or passage, then session history, with the per-turn learner input last.
- Use `prompt_cache_key=f"claimlab:{source_id}"` (per source, not per session) and `prompt_cache_retention="24h"` for the demo period. Verify with `usage.prompt_tokens_details.cached_tokens`.
- Expected latency gain is modest, given the 1-5% input effect in the OpenAI guide. Cost savings are larger: about $0.15 versus $1.25 per 1M input tokens, using third-party pricing.

**6. Split generation ("answer first").**
- With streaming (Q2), a separate fast "step 1" call is mostly unnecessary.
- If streaming is not available, two parallel final calls (A: steps 1-N prose; B: whiteboard items plus check question, given the same context) would cut wall time to the larger of the two instead of the sum. This doubles input cost and risks inconsistency between the halves. Rate limits for concurrency are not verified.
- A small local Muse Glimmer model for the plan step (Meta's "glimmer-api-agent" escalation pattern) is out of scope for a hackathon, because it is self-hosted only.

**7. Trim output.**
- Cap steps at 3-4 for feedback turns.
- Shorten JSON keys in the lesson schema, mapped to canonical names in code.
- Have reviewed code derive whiteboard items from experiment results (axes, values, run ids) instead of the model writing them.
- Avoid echoing source quotes the server already holds; reference them by anchor id.

**8. Speculative prefetch.** While the learner reads the lesson, pre-run likely follow-ups: the next experiment variant, or a prerequisite explainer for the misconception tag, cancelled if unused. This is high cost and uncertain value, and worth it only for the scripted demo path.

**9. Switch to the Responses API with reasoning carried forward** (`previous_response_id`, or `store:false` plus `include:["reasoning.encrypted_content"]`). Later rounds would not re-reason from scratch. This is Meta's recommendation for tool loops, but it means migrating the message and tool format (`function_call_output`/`call_id`). Benefit unmeasured; medium to high effort.

### Gaps
- No measured split of the 12-23 s lesson reply into reasoning time versus visible-token time; it is needed to rank #2 against #7.
- I did not verify Meta concurrency and rate limits, which bound #3, #6 and #8.
- Whether removing the `assess_answer` round degrades grading quality is untested.

---

## Q5. Perceived-latency UX: progress indicators, skeletons, intermediate steps, and tolerable wait times

### Takeaway
ClaimLab's turns of 17-46 s are far past the roughly 10 s limit for keeping attention on the dialogue. NN/g guidance for waits of 10 s or more is a percent-done style indicator, with feedback "indicating when the computer expects to be done". Animated progress feedback made users willing to wait about 3 times longer in a cited study. The best fix for perceived latency is to make the wait visibly productive with real, ordered progress: streamed experiment code, the experiment chart as soon as the run finishes, and lesson steps appearing one by one. Streaming can bring the first visible output down to about a second, apart from the model's initial reasoning pause.

### Cited Findings
- "0.1 second is about the limit for having the user feel that the system is reacting instantaneously"; "1.0 second is about the limit for the user's flow of thought to stay uninterrupted"; "10 seconds is about the limit for keeping the user's attention focused on the dialogue". Longer delays "should be given feedback indicating when the computer expects to be done". For 2-10 s operations, "a true percent-done indicator may be overkill". Source is from 1993 with a 2014 update, so older than 2025, but these perceptual limits are widely treated as stable. — [NN/g, Response Times: The 3 Important Limits](https://www.nngroup.com/articles/response-times-3-important-limits/)
- NN/g recommends "a looped indicator for delays of 2–9 seconds and a percent-done indicator for delays of 10 seconds or more". Looped animation under 1 s is distracting. When estimates are uncertain, show percent-done sooner. In a University of Nebraska-Lincoln study, users with an animated progress bar "were willing to wait on average 3 times longer" and were more satisfied. The article (2014, older than 2025) cites Nah (2004). — [NN/g, Progress Indicators Make a Slow System Less Insufferable](https://www.nngroup.com/articles/progress-indicators/)
- Jakob Nielsen restates: show a progress indicator when response time exceeds 10 s, preferably percent-done. This is from a search snippet; the post date was not verified. — [UX Tigers: Progress indicators](https://www.uxtigers.com/post/progress-indicators)
- Another source argues the 0.1/1/10 s figures synthesize Nielsen (1993), Miller (1968) and Card, Moran & Newell, rather than coming from a single experiment. — [feelsfast: canonical thresholds](https://feelsfast.vercel.app/concepts/canonical-thresholds)
- OpenAI says streaming brings the wait for the first output to about a second or less. "Showing steps" and loading states have mainly a psychological effect, while streaming and chunking also shorten the time to a useful response. — [OpenAI latency optimization guide](https://developers.openai.com/api/docs/guides/latency-optimization)
- Meta: with streaming the user "sees the first words sooner", but a reasoning-heavy prompt "can pause before content streams". — [Meta cookbook: Streaming](https://dev.meta.ai/docs/cookbook/streaming-responses)
- The AI SDK protocol has explicit `start-step`/`finish-step` and tool-input and tool-output parts, which is how agentic UIs show "what the agent is doing" between LLM calls. — [AI SDK stream protocol](https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol)

### Inferences
**Staged progress strip, driven by JobEvents** (all are real events the orchestrator already knows about):
- "Reading the source" (planning round)
- "Writing an experiment", with the code streaming in a collapsed panel
- "Running experiment (about 1 s)", then the result or chart shown immediately
- "Searching the web: <query>", only when used
- "Composing lesson: step 2 of 4", which is a true percent-done once step boundaries stream

This meets NN/g's percent-done advice for waits of 10 s or more without faking a timer.

**Skeletons.** Before step 1 arrives, show the lesson card skeleton: N step placeholders plus a whiteboard frame. I found no NN/g source on skeleton screens in this research, so this is practice, not cited evidence.

**Elapsed-time cue.** Show "usually 15-40 s" from ClaimLab's own measured range, plus a cancel button. The Job model already has a cancel endpoint.

**Commit early.** Render the experiment result card and its board object as soon as the tool returns, before the lesson. This turns the ~1 s run plus the 8-10 s code-writing into visible progress, and fits ClaimLab's explicit-objects principle: experiment runs are first-class objects.

**Pace the reveal.** Keep each step's reveal at the speed it arrives. Do not hold back finished steps to animate them, since that adds latency.

### Gaps
- I found no HCI study specific to waits for LLM or agent tutors, for example whether learners tolerate 30 s when shown intermediate reasoning. The NN/g thresholds are general-purpose and decades old.
- I found no cited research on skeleton screens versus spinners for waits over 10 s.

---

## Q6. Ranked recommendations for ClaimLab (impact vs effort for a small team)

### Takeaway
Do the low-effort items that remove real seconds first: per-call `reasoning_effort` with token logging, merging `assess_answer` into the lesson, and concurrent tools. Then build the job-plus-SSE progress path, fixing the session lifetime, and stream `present_lesson` steps through it. These give the largest perceived improvement. The Responses API migration and experiment templates are the next tier. Speculative prefetch and parallel split generation come last.

### Cited Findings
- The evidence base for this ranking: output tokens and round trips dominate latency ([OpenAI guide](https://developers.openai.com/api/docs/guides/latency-optimization)); Meta's reasoning controls and the from-scratch reasoning on Chat Completions ([Meta Reasoning](https://dev.meta.ai/docs/reasoning)); streaming of tool arguments ([Meta Tool calling](https://dev.meta.ai/docs/tool-calling)); FastAPI session lifetime ([FastAPI advanced dependencies](https://fastapi.tiangolo.com/advanced/advanced-dependencies)); NN/g thresholds of 10 s or more ([NN/g](https://www.nngroup.com/articles/response-times-3-important-limits/)).

### Inferences
Ranking (my synthesis; "saves" estimates come from the brief's single observations and are unvalidated):

| # | Change | Real or perceived | Expected impact | Effort | Notes and risks |
|---|---|---|---|---|---|
| 1 | Log `usage` (`reasoning_tokens`, `completion_tokens`, `cached_tokens`) and wall time for every round; then set `reasoning_effort` per call (`low` for code and lesson, `minimal` for grading) | Real | Unknown, possibly large; the measurement itself unblocks every other decision | Very low (a few lines) | Check lesson quality; the third-party probe saw no low/high difference on a trivial prompt |
| 2 | Fold `assess_answer` into the `present_lesson` schema; grade MCQ/numeric checks in code | Real | Removes one full round (about 22 s observed) on answer turns | Low to medium (schema, prompt, tests) | Grading quality must be re-checked |
| 3 | Run independent `tool_calls` from one reply concurrently (thread pool) and prompt the model to batch independent tools | Real | Saves the sum minus the max of tool times; large only with web fetches | Low | Keep `tool` message order and ids; Meta requires pairing |
| 4 | Async tutor turn: POST returns `job_id`; worker thread with its own `SessionLocal`; phase JobEvents; frontend subscribes to the existing SSE endpoint | Perceived (large); robustness | Wait becomes visible progress; survives reload | Medium | Fix the existing SSE generator: per-poll session, sync generator or threadpool; consider FastAPI ≥0.118 or 0.135 `EventSourceResponse`; check how auth reaches `EventSource` |
| 5 | Stream `present_lesson` (`stream:true`, `stream_options.include_usage`); accumulate arguments by index; parse with `pydantic_core.from_json(allow_partial=True)`; emit validated `lesson_step` events; never stream the answer key | Perceived (large) | First step visible before the 12-23 s reply ends, unless reasoning dominates | Medium | Needs #4; probe delta field names; handle retry with a `lesson_reset` event |
| 6 | Final round: no tools plus `response_format` json_schema for the lesson (constrained decoding) | Real (avoids stray extra rounds) and reliability | Removes "model called another tool at the deadline" rounds | Low to medium | Probe whether it streams; `tool_choice` cannot force `present_lesson` |
| 7 | Byte-stable prefix: constant tool list (enforce restrictions in handlers), static content first, `prompt_cache_key` per source, `prompt_cache_retention:"24h"` | Real (small) and cost | Modest latency gain, clear cost cut | Low | Verify with `cached_tokens` |
| 8 | Stream `run_python_experiment` code to the UI and render experiment results the moment they return | Perceived | 8-10 s of code-writing becomes visible work | Low once #4 and #5 exist | Validate the code server-side before running, as today |
| 9 | Parameterized experiment templates, with free-form code as fallback; cache results per (source, claim, params) | Real | Shrinks or removes the 8-10 s code-writing round | Medium to high | Reviewed code performs calculations, which matches ClaimLab's principle |
| 10 | Migrate the loop to the Responses API (`previous_response_id` or encrypted reasoning replay) | Real | Later rounds stop re-reasoning from scratch; size unknown | Medium to high | Meta's recommended path for tool loops; format changes |
| 11 | Trim output: 3-4 steps on feedback turns, short JSON keys, board items derived in code | Real | Roughly proportional to tokens cut | Low to medium | Quality trade-off |
| 12 | Speculative prefetch of likely next steps; two parallel final calls (prose, board plus check) | Real | Uncertain | High; doubles cost | Rate limits unverified; consistency risk |

Quick wins that fit in under a day: #1, #3, #7, and the hygiene item `max_tokens` → `max_completion_tokens`.

### Gaps
- Every "saves" number above is extrapolated from single baseline observations. The team should collect a per-round timing table (round type, reasoning tokens, completion tokens, cached tokens, wall time) over about 10 turns before and after each change.
