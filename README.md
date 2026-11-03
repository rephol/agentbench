# agentbench

[![CI](https://github.com/rephol/agentbench/actions/workflows/ci.yml/badge.svg)](https://github.com/rephol/agentbench/actions/workflows/ci.yml)

A small benchmark harness for coding agents. It runs a fixed set of coding tasks through
an agent under different configurations ("arms") and reports **success rate** and **cost
per successful task** for each arm, with bootstrap confidence intervals.

It was built to measure [tierline](https://github.com/rephol/tierline), a model-routing
proxy for Claude Code, in arms such as: all traffic to Opus, tierline routing on, and a
single cheaper model. Nothing in the harness is tierline-specific except the cost join; any
arm that differs by environment variables or `--model` works.

> **Status: early.** The harness has been run on real models: a pilot on 2026-11-02 and a
> cleaner run on 2026-11-03 (see [Results](#results)). Both are small, from one machine,
> on self-written tasks. Treat them as early signal, not proof.

## The problem

"Cheaper per session" is a misleading number for a router: a router that sends everything
to the weakest model is cheap because it fails. The honest metric is **cost per
successful task** (total spend divided by tasks that passed) next to the success rate, on
a fixed task set where "passed" is decided by code, not by a model's opinion.

## Method

- **Tasks** are small real Python programming jobs with deterministic checks (see
  [Tasks](#tasks)). Each attempt starts from a fresh temp-directory copy of the fixture.
- **The agent never sees the check.** `check.py` and `solution/` live outside the fixture
  (`repo/`). `check.py` is copied into the working directory only after the agent exits,
  then run with `python3 check.py`; exit code 0 is a pass. A timeout counts as a failure.
- **Arms x tasks x samples.** An arm is a name plus environment variables for the agent
  process (and optionally `--model`). Samples repeat each task, since agents are
  non-deterministic.
- **Success rate** per arm is the mean over tasks of that task's pass rate across its
  samples. The **95% CI** is a percentile bootstrap with 10,000 resamples of *tasks*
  (not individual attempts), seeded for reproducibility. This follows the method in
  Cloudflare's [auto-router evaluation](https://blog.cloudflare.com/auto-router/), which
  inspired this harness; the code is written from scratch.
- **Cost** per arm is the sum over all its attempts, failed ones included, divided by the
  number of successes.

### How cost is joined

Each attempt in `results.jsonl` records `start_ms` and `end_ms` (unix milliseconds, wall
clock) around the agent process. Each arm names a `tierline_log` in `bench.toml`: the JSONL
that a tierline instance wrote while that arm ran. `report` attributes a tierline record
to an attempt when

```
attempt.start_ms <= record.ts_ms <= attempt.end_ms
```

and sums tokens and `cost_usd` over the matching records. This is only sound if

1. attempts run **sequentially** (`run` never overlaps them),
2. each arm has **its own tierline instance and log file**, used by nothing else while the
   arm runs, and
3. the machine clock does not jump mid-run.

A request tierline could not price (`cost_usd` null) or an attempt with no matching
request is counted as a **cost gap** and shown next to the number; the total is then a
lower bound. If an arm has no tierline log, the report falls back to the `total_cost_usd`
that `claude --output-format json` reports about itself, labelled `agent-reported`. If
neither exists the cost is `n/a`. Nothing is estimated or invented.

## Tasks

25 tasks under `tasks/<id>/` (01-15 original, 16-25 tagged `hard-v2`; select with `agentbench run --tag hard-v2`):

```
task.toml    id, category, difficulty (trivial|easy|medium|hard), prompt
repo/        the fixture the agent works on
check.py     hidden pass/fail check (stdlib only, deterministic)
solution/    full reference tree
```

`cargo test` (and `agentbench validate`) assert for every task that the unmodified
fixture **fails** its check and the reference solution **passes** it. Python 3 is the
only requirement for the checks; no pytest.

| id | difficulty | what |
|---|---|---|
| 01-paginate-off-by-one | trivial | fix an off-by-one in `paginate` |
| 02-fix-failing-test | easy | make a failing unittest pass by fixing `slugify` |
| 03-roman-numerals | easy | implement `to_roman` from its docstring |
| 04-add-cli-flag | easy | add a `--shout` flag to an argparse CLI |
| 05-rename-across-files | easy | rename a function across modules and tests |
| 06-input-validation | medium | add input validation to `create_user` |
| 07-parse-access-log | medium | parse Common Log Format and summarize |
| 08-extract-money-helper | medium | extract duplicated formatting into a helper, tests stay green |
| 09-todo-remove-command | medium | add a `remove` command with non-reused ids |
| 10-merge-intervals | medium | implement `merge_intervals` with touching/overlap rules |
| 11-token-bucket-refill | medium | fix a rate limiter that loses fractional refills |
| 12-apply-unified-diff | hard | implement a unified-diff applier incl. no-newline markers |
| 13-ttl-lru-cache | hard | implement an LRU cache with TTL and exact counters |
| 14-expression-evaluator | hard | write a parser matching Python's arithmetic semantics, no `eval` |
| 15-task-scheduler-bugs | hard | fix several interacting bugs in a dependency planner |
| 16-json5-lite-parser | hard | lenient JSON reader with exact error positions |
| 17-semver-ranges | hard | npm-style version ranges incl. the prerelease rule |
| 18-cron-next-fire | hard | 5-field cron next-fire with day-of-month/week OR rule |
| 19-split-cents-invoice | hard | largest-remainder money split across two modules |
| 20-layered-config | hard | layered config merge, env coercion, provenance |
| 21-dependency-resolver | hard | version resolver with backtracking, deterministic choice |
| 22-editor-undo-redo | hard | undo/redo with groups, limits, deep-copy history |
| 23-decimal-strings | hard | exact decimal-string arithmetic and 7 rounding modes |
| 24-leaderboard-ranking | hard | competition ranking, paging, neighbours, percentiles |
| 25-grid-path-turns | hard | cheapest grid path with turn costs and one-way tiles |

## Running it

Requirements: Rust (stable), Python 3, and for real runs an authenticated `claude` CLI.

```bash
cargo run -- list            # show tasks
cargo run -- validate        # fixtures fail, solutions pass
cargo run -- run --agent fake-solve --out /tmp/demo.jsonl --samples 1   # no model involved
cargo run -- report --results /tmp/demo.jsonl
```

Agents: `claude`, `fake-solve` (installs the reference solution), `fake-noop` (does
nothing). The `claude` agent refuses to start without `--yes`, because it spends real
money.

### The `claude` adapter

For every attempt, in the attempt's temp directory:

```
claude -p "<task prompt>" --permission-mode dontAsk --allowedTools "Read,Edit,Write,Glob,Grep,Bash(python3:*)" --output-format json --no-session-persistence [--model <arm.model>] [clean flags] [--effort <arm.effort>] [arm.extra_args]
```

Permissions are restricted rather than bypassed: `dontAsk` mode denies anything not on the
allowlist (file read/edit/write/search tools, and Bash limited to `python3`) without
prompting. The arm's `env` is added to the inherited environment, and `run.timeout_secs`
kills a stuck attempt.

Arm and run options for this adapter:

| Key | Where | Effect |
|---|---|---|
| `clean = true` | `[run]` or `[[arm]]` (arm wins) | Removes `CLAUDE*` and `AI_AGENT*` env vars (keeps `CLAUDE_CODE_OAUTH_TOKEN`, `CLAUDE_CONFIG_DIR`) and adds `--setting-sources project,local --strict-mcp-config --mcp-config '{"mcpServers":{}}' --disable-slash-commands`, so your hooks, plugins and MCP servers don't enter the measurement |
| `effort = "medium"` | `[[arm]]` | Passes `--effort medium`; otherwise the effort level is inherited from your settings |
| `[arm.proxy]` | `[[arm]]` | `command`, `args`, `env`, `listen` (`host:port`), `log` (proxy stdout/stderr), `ready_timeout_secs`. `run` starts it, waits for the port, sets `ANTHROPIC_BASE_URL` to it, and kills it when the arm ends, including on error or Ctrl-C |

### Running a clean comparison against tierline

[`bench.clean.example.toml`](bench.clean.example.toml) defines three clean arms at medium
effort (all Opus, tierline routing with `TIERLINE_ROUTE=1`, Sonnet alone), each with its own
tierline proxy and log. Build tierline, copy its `pricing.example.json` and
`models.example.json` to `pricing.json` / `models.json` here, then:

```bash
agentbench run --config bench.clean.example.toml --tag hard-v2 --out results/clean.jsonl --yes
agentbench report --config bench.clean.example.toml --results results/clean.jsonl
```

Arms run one after another, so the timestamp join described above stays valid. `run`
appends to the results file and skips attempts already recorded, so an interrupted run
resumes. Without a `proxy` block you can still start tierline yourself and point the arm's
`env.ANTHROPIC_BASE_URL` at it, as `bench.toml` does.

`report` prints a markdown table and writes `report/report.md` and `report/report.svg`. It
also shows Claude's own per-model usage next to tierline's and flags models only Claude saw
(server-side calls such as the advisor).

## Results

**Small runs, not conclusions.** One machine, tasks written for this repo, Claude Code's
headless mode (`claude -p`) on a Claude subscription. All dollar figures are API-equivalent
estimates computed from token counts and published API prices; nothing was billed at these
rates.

### Main result: clean run, 2026-11-03

- **Tasks:** the `hard-v2` set, 10 tasks × 2 samples = 20 attempts per arm.
- **Config:** clean (no user hooks, plugins or MCP servers; see `clean = true` above), with
  `--effort medium` pinned on every arm. Reproduce with `bench.clean.example.toml`.
- **Cost source:** tierline's log, one proxy per arm.

| Arm | Passed | Est. cost | Cost per success |
|---|---|---|---|
| opus (every request on Opus) | 15/20, 75% (95% CI 50–100%) | $4.44 | $0.296 |
| route ([tierline](https://github.com/rephol/tierline), Opus requested, routed per request) | 18/20, 90% (CI 70–100%) | $2.09 | $0.116 |
| sonnet (Sonnet alone) | 17/20, 85% (CI 65–100%) | $1.55 | $0.091 |

The route arm sent 34 requests to Opus, 29 to Sonnet and 33 to Haiku. Its cost per success
was about 61% below Opus on every request.

**Read with care:**

- **These arms can't be ranked on quality.** Every confidence interval overlaps. Opus
  scoring lowest is most likely noise at 20 attempts, not a sign that Opus is worse.
- **Plain Sonnet was cheapest** at a similar pass rate ($0.091 per success vs $0.116 for
  routing). The fair reading is "a cheaper model was enough on these tasks", not that
  routing beat Opus.
- **Task 16 results use the old prompt.** Task 16 failed in every arm in both runs, which
  pointed at the task: its check required exact error positions for cases the prompt never
  specified. It is fixed as of the commit that adds this section, but the numbers above came
  from the old version.
- **Claude Code's self-reported cost is wrong for routed traffic.** It prices the model it
  requested, so all route traffic is priced as Opus. Tierline's log is the cost source for
  that arm. (Claude-reported cost for route was $7.10, against tierline's $2.09.)
- **No advisor arm.** `--advisor opus` exists, but Claude never called it unprompted in the
  pilot, so there's nothing to compare.
- **Each attempt has one startup request** tierline can't price (the report counts these as
  cost gaps), so costs are slight lower bounds.

### Earlier pilot, 2026-11-02

The same `hard-v2` set, 3 arms × 20 attempts, but not clean: the local user hooks were
active. They injected about 69 KB per request, against about 3 KB for a clean config, which
inflated cost and kept Haiku from ever being chosen by the router. Results:

| Arm | Passed | Est. cost | Cost per success |
|---|---|---|---|
| tierline-off (Opus) | 18/20 | $5.82 | $0.323 |
| tierline-route | 18/20 | $3.68 | $0.204 |
| sonnet (advisor configured, never fired) | 18/20 | $3.12 | $0.174 |

All arms also ran at **low effort**, inherited from local Claude Code settings rather than
pinned (the request bodies carry `output_config: {effort: "low"}`). Routing cost about 37%
less per success than Opus there; the only failures were task 16, in every arm. The earlier
easy set (15 tasks × 1 sample) passed 15/15 in all three arms.

Next steps: re-run with the fixed task 16, add tasks where Sonnet genuinely fails, and make
an advisor arm fire verifiably.

## Limitations

- 25 tasks is small: expect wide intervals, and treat small differences as noise.
- The tasks are small single-repo Python jobs; they say little about large codebases.
- Tasks cannot be shown to be free of training-set overlap.
- Wall-clock joining needs the sequential, one-proxy-per-arm discipline above.
- A Docker runner is not implemented; isolation is a temp directory, not a sandbox.

## License

MIT
