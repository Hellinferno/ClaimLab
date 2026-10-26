# Cost, Resource, and Performance Controls

## Planning budget

Suggested initial development allocation: **US$30 for model calls and US$10 for hosting/execution**, with a separate optional reserve chosen by Ravi. These are planning envelopes, not current provider price quotes or authorization to spend.

The supplied guide describes US$150 in Meta credits for accepted participants; actual approval and availability must be verified. Partner credits are conditional. Keep the product usable within its own configured budget even if no partner grant arrives.

## Cost calculation

Estimate each model request using:

`estimated USD = input tokens × input USD per million / 1,000,000 + output tokens × output USD per million / 1,000,000`

Load verified rates and a price-version timestamp through configuration. Do not bake a stale rate into the code or pitch. Use actual reported usage for settlement, with conservative reservations before requests. If required price configuration is missing, do not silently make unmetered paid calls.

Include request context, tool schemas/results, repeated prefixes, and retries in the estimate. Discounts/caching are optimizations only after actual availability is confirmed. A billing notification is an alert, not an application-enforced hard stop.

## Enforcement

- Enforce an app-wide AI budget and per-owner request quotas on the server.
- Atomically reserve the worst permitted request cost before calling the provider; reconcile actual usage afterward.
- Use a verified token counter if available. Otherwise use a documented conservative estimate and narrow context; do not claim exact preflight token counts.
- Bound output tokens, input context, request attempts, tool calls, and run count.
- Keep a reservation when a network failure leaves usage uncertain; reconcile before releasing it.
- Stop new requests when remaining budget is insufficient; preserve the student's session and explain the limit.

Application controls bound authorized requests but cannot guarantee a third-party invoice amount. Track and compare actual billing during development. Hosting costs are metered separately from model usage.

## Resource controls

Use limits in the technical spec for uploads, queue depth, parsing, board size, run output, and execution. Rate-limit expensive operations per owner and globally. A single durable worker intentionally limits concurrency in the first deployment.

## Performance targets

These are proposed targets to measure, not achieved benchmarks:

| Operation | Target under the documented single-user test environment |
| --- | --- |
| Local UI action | Feedback within 100 ms where computation is local |
| API acceptance | p95 below 500 ms excluding upload transfer |
| Small supported PDF parsing | p95 below 10 seconds |
| First meaningful tutor update | p95 below 20 seconds on the verified model/account |
| Typical reviewed recipe | p95 below 3 seconds excluding queue wait/image cold start |
| Local runner cancellation | Termination within 5 seconds after the worker observes cancellation |
| Session reload | Correct committed state within 2 seconds in the test environment |

Track queue wait, model latency, tool execution, rendering, and end-to-end latency separately. Record cold/warm runs and sample count. Remote model cancellation is best effort and may incur usage even if its late output is discarded.

## Optimization order

Reduce irrelevant context, reuse validated source extraction, send compact board/evidence summaries, limit output verbosity, and avoid unnecessary model calls. Preserve numerical correctness and observation semantics. Add complexity only when measured results justify it.

## Demo load

Test a small concurrent set of independent guests and verify queue feedback and isolation. Do not advertise an unsupported user-capacity figure. Provide a clear busy state rather than accepting an unbounded queue.
