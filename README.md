# agentbench

[![CI](https://github.com/rephol/agentbench/actions/workflows/ci.yml/badge.svg)](https://github.com/rephol/agentbench/actions/workflows/ci.yml)

A small benchmark harness for coding agents. It runs a fixed set of coding tasks through
an agent under different configurations ("arms") and reports **success rate** and **cost
per successful task** for each arm, with bootstrap confidence intervals.

It was built to measure [tierline](https://github.com/rephol/tierline), a model-routing
proxy for Claude Code, in three arms: all traffic to Opus, tierline routing off, and
tierline routing on. Nothing in the harness is tierline-specific except the cost join; any
arm that differs by environment variables or `--model` works.

> **Status: harness complete, no real run yet.** The harness and all 15 tasks are tested
> against a fake agent only. Every result below is **TBD**.

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
claude -p "<task prompt>" --permission-mode dontAsk --allowedTools "Read,Edit,Write,Glob,Grep,Bash(python3:*)" --output-format json --no-session-persistence [--model <arm.model>]
```

Permissions are restricted rather than bypassed: `dontAsk` mode denies anything not on the
allowlist (file read/edit/write/search tools, and Bash limited to `python3`) without
prompting, so headless runs cannot hang or run arbitrary commands. The arm's `env` is added to the inherited environment
(so `ANTHROPIC_BASE_URL` can point at tierline), and a per-task timeout
(`run.timeout_secs`) kills the process.

### Running the three arms against tierline

Start one tierline per arm with its own port and log, then run that arm alone:

```bash
# in the tierline repo (see its README for pricing.json / models.json)
TIERLINE_LISTEN=127.0.0.1:8787 TIERLINE_LOG=../agentbench/logs/opus-direct.jsonl    cargo run --release   # pass-through
TIERLINE_LISTEN=127.0.0.1:8788 TIERLINE_LOG=../agentbench/logs/tierline-off.jsonl   cargo run --release   # pass-through
TIERLINE_LISTEN=127.0.0.1:8789 TIERLINE_LOG=../agentbench/logs/tierline-route.jsonl TIERLINE_ROUTE=1 cargo run --release

agentbench run --arms opus-direct    --yes
agentbench run --arms tierline-off   --yes
agentbench run --arms tierline-route --yes
agentbench report
```

`bench.toml` maps each arm to its port (`ANTHROPIC_BASE_URL`) and log. `opus-direct` pins
`--model opus`; the other two use Claude Code's default model, so routing has something to
override. `run` appends to the results file and skips attempts already recorded, so an
interrupted arm can be resumed.

`report` also shows Claude's own per-model usage (`modelUsage` from `--output-format json`) next to tierline's, and flags models that only Claude saw (server-side calls such as the advisor). `report` prints a markdown table and writes `report/report.md` and `report/report.svg`
(success rate with CI whiskers; cost per success).

## Results

**Pilot results, not a conclusion.** These come from one machine, on 2026-11-02, with tasks
written for this repo, using Claude Code's headless mode on a Claude subscription. All dollar
figures are API-equivalent estimates computed from token counts and published API prices.
Nothing was actually billed at these rates.

### Hard set (`hard-v2`: 10 tasks × 2 samples = 20 attempts per arm)

| Arm | Main model | Success rate (95% CI) | Est. cost | Cost per success |
|---|---|---|---|---|
| tierline-off | Opus on every request | 90% (18/20), 70–100% | $5.82 | $0.323 |
| tierline-route | routed per request by [tierline](https://github.com/rephol/tierline) | 90% (18/20), 70–100% | $3.68 | $0.204 |
| sonnet (advisor configured) | Sonnet | 90% (18/20), 70–100% | $3.12 | $0.174 |

### Easy set (15 tasks × 1 sample)

All three arms passed 15/15. The cost per success was $0.205 for tierline-off, $0.139 for
tierline-route and $0.108 for the Sonnet arm.

### What this does and doesn't show

- **The arms didn't differ on quality.** The only failures were task 16, which failed
  identically in every arm. That suggests a flaw in the task, not in the models; it is under
  review. With 20 attempts per arm, the intervals can't tell these arms apart.
- **Cost did differ.** Routing cost about 37% less per success than Opus on every request.
  Sonnet alone cost about 46% less. On these tasks a cheaper main model lost nothing, so the
  honest takeaway so far is "Sonnet was enough here", not "routing wins".
- **Routing behaved sensibly.** tierline sent 71 coding-edit and writing requests to Sonnet
  and kept all 23 debugging requests on Opus.
- **The advisor never fired.** The third arm ran Sonnet with `advisorModel: opus` set per
  invocation, but Claude Code's per-model usage shows no Opus calls. The arm therefore
  measures Sonnet alone. Whether the advisor wasn't triggered or the setting didn't take
  effect hasn't been checked yet.
- **Cost sources disagree.** Costs here come from tierline's log. Claude Code's
  self-reported cost was about 1.3–1.4× higher on identical token counts, and it reports the
  model it requested, so in the route arm it prices Sonnet traffic as Opus. Each attempt also
  includes one startup request tierline can't price. The costs are therefore slight lower
  bounds.

Next steps: fix or drop task 16, add tasks where Sonnet genuinely fails, add a plain Sonnet
arm, and make the advisor fire verifiably.

## Limitations

- 25 tasks is small: expect wide intervals, and treat small differences as noise.
- The tasks are small single-repo Python jobs; they say little about large codebases.
- Tasks cannot be shown to be free of training-set overlap.
- Wall-clock joining needs the sequential, one-proxy-per-arm discipline above.
- A Docker runner is not implemented; isolation is a temp directory, not a sandbox.

## License

MIT
