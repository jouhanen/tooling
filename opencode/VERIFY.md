# Verification and acceptance

Keep installation/discovery, native mechanical behavior, live model workflow, and
context-isolation conclusions separate. A successful installer or scripted model
cannot establish that a real model follows the review and approval protocol.

## Current evidence levels

| Category | Status | Scope |
| --- | --- | --- |
| Offline authoring/installer/declaration checks | Passing locally | Python 3.14; CI also targets 3.10, but no CI run is claimed here |
| Native discovery | Passed in isolated project and global profiles | OpenCode 2.2.5, Linux/WSL2; eight agents, four commands and skills |
| Native dispatch and sampled tool boundaries | Passed with scripted loopback model | All seven reviewer types, repeated fresh design reviewer, required fixture reads, selected denials |
| Parent conversation boundary | Scoped marker probe passed | Captured child requests lacked a random parent-only marker; project instructions were inherited |
| General context/filesystem/process isolation | Unverified; no sandbox provided | Shared local reads and host-injected context remain possible |
| Live brainstorm/draft/review/resolve and approval pauses | Not run | Requires separate user authorization and a real human checkpoint |

The [recorded run](verification/2026-11-04-native.md) identifies the exact tested
payload and probe. Conclusions do not automatically apply to other OpenCode
versions, models, profiles, policies, platforms, or modified prompts.

## 1. Offline checks

Follow [the test instructions](../tests/README.md). Ordinary CI runs only the
offline suite; it does not install OpenCode, access model credentials, invoke
native agent loops, or perform paid tests. The probe regression tests exercise
synthetic fixtures and parsers, not the installed host.

Malformed JSON, wrong identities, incomplete reads, absent child links, failed
completions, reused sessions, truncated results, and arbitrary non-permission
errors must not become passing evidence. Offline fixtures cover those distinctions.

## 2. Opt-in native mechanical probe

Requirements: Python 3.10+, the exact installed OpenCode **2.2.5** executable,
Linux/POSIX, and a new evidence directory outside this checkout. No real model
account or GPU is needed. The fake provider implements OpenAI-compatible streamed
tool calls on loopback; its strings are scripts, not generated reviews.

```sh
python3 scripts/native_probe.py \
  --opencode /absolute/path/to/opencode \
  --output /tmp/opencode/egm-native-new-run \
  --scope both
```

Choose a path that does not already exist. The script refuses other host versions;
adapt its contracts deliberately for a future version rather than removing the
version gate. `--scope project` or `--scope global` limits the run to one profile.
Global here means an isolated temporary XDG profile, **not your real profile**.

The runner:

1. Creates private HOME/XDG directories and allowlists the child environment.
   Provider credentials, existing OpenCode overrides, proxies, and personal
   account databases are not inherited. It never changes the shared service.
2. Installs a source candidate in each disposable project/global profile using
   the actual installer. The application project contains synthetic files only.
3. Starts its own authenticated foreground server on loopback and checks its PID
   and version. API calls use OpenCode's CLI with that explicit server and the
   same private authentication context. Processes owned by the run are stopped
   on normal exit or caught failure; evidence is retained, not deleted.
4. Denies every provider except the loopback fixture, disables free models, and
   checks that only `probe/scripted` is enabled before starting agent loops. It
   refuses unexpected ambient configuration documents.
5. Verifies native registration, agent modes, skill paths/autoinvoke settings,
   and retained Build/Plan definitions. Executes all four commands from Build and
   checks they select Elephant, load the matching skill, and can read every
   required shared resource from the installed layout.
6. Forces one allowed Elephant documentation write, one forbidden source write,
   and a denied `general` dispatch. Dispatches all seven Goldfish types, including
   two separate design reviewers, with no reused child ID. It binds parent tool
   completions to native child IDs, parent relationships, agents, outcomes, and
   completion timing rather than accepting a parent summary.
7. Checks native target reads including an untruncated final fixture sentinel.
   Source-aware reviewers read source and bundled standards, while `.env`, other
   external reads, and skill loading produce `permission.rejected`. Global
   comprehension cannot read the globally installed resource directory.
8. Captures the actual loopback model request bodies. Children must not contain
   the random parent-only marker; they must contain the project instruction
   marker. Synthetic `.env` contents must not appear in any model request.
9. Confirms source guards and installed-package hashes remain unchanged, records
   source/probe identity, and writes a summary with separate verification levels.

The native tool catalog can expose a loader whose operation remains denied:
Goldfish see `skill`, but actual skill calls are rejected. Visibility alone is not
permission enforcement. Write/shell/delegation tools were absent from the tested
Goldfish catalogs. Elephant can expose platform tools associated with partial
edit grants; this probe does not exercise every platform operation, worktree
operation, permission resource, path alias, or possible bypass.

This runner is **not an OS/network sandbox**. OpenCode may perform background
catalog or integration discovery. No real provider is authorized and no real
provider credentials are supplied, but the runner does not claim all outbound
traffic is blocked. Test in a separately isolated machine/container if that is a
requirement. Likewise, changed HOME/XDG settings do not erase system policy or
prove the absence of every host-injected instruction.

### Evidence and failure handling

The output root is created with mode 0700. Keep it private: it contains temporary
profiles, the private database, server logs, resolved prompts, model request bodies,
native contexts, and source paths. Authorization headers and the random server
password are not deliberately recorded. Do not upload raw directories or commit
them to this public repository without reviewing/redacting them.

`summary.json` includes the version, platform, base Git commit, dirty-worktree flag,
probe SHA-256, payload digest, tested scopes, and limits. Exit code 0 means the
requested mechanical probes passed, not that live EGM acceptance or general
isolation passed. Exit code 1 means incomplete/refused/failed verification; an
absent scope result never counts as passing. Inspect retained evidence rather
than deleting profiles, changing the real database, or weakening permissions.

## 3. Separately authorized live acceptance

Do not start this step merely because the native runner passes. First obtain
explicit authorization for the real provider/model, disposable project, expected
reviewer calls/retries, and any cost/usage limit. Reuse an existing authenticated
profile only with the user's approval; never copy credentials into this repo.

Use a small fixture problem, such as a local webhook retry design. Retain evidence
privately and record candidate commit/dirty flag, installed hashes, host version,
model/variant, surface, date, and any inherited instructions or policy differences.

Required live checkpoints:

1. Start `/egm-brainstorm` and verify critical questioning over actual user turns.
   Confirm the artifact destination. Do not let a scripted advance response stand
   in for a human approval pause.
2. Approve the concept direction, then separately confirm reviewer selection and
   reading inputs. Verify fresh native reviewer starts, reads, completions, and
   structured results; missing evidence is incomplete, not zero findings.
3. Approve drafting explicitly. Have Elephant write one section and stop. Record
   that it does not draft the next section until the human responds. Continue
   section-by-section and reconcile contradictions with the concept.
4. Run a focused review of the current design, preserving snapshot, attempts,
   paraphrase where selected, report provenance, and unresolved coverage.
5. Ask `/egm-resolve` to propose fixes. Verify no target edit occurs before approval.
   Approve one exact repair, check revision/state updates, and verify it remains
   fixed-unverified until fresh evidence checks it. Reject or defer another item
   to confirm it is not silently applied or treated as accepted risk.
6. Approve a fresh follow-up round. Verify new child IDs, refreshed scope/snapshot,
   and no previous conversation or results forwarded without an explicit stage
   requirement. Do not call one clean round converged.
7. Pause/resume after an external edit. Verify old approvals/coverage become stale
   as appropriate and the next action is confirmed before proceeding.
8. Explicitly approve implementation of the current revision. Verify Elephant
   hands off to Build rather than writing application code itself.

Record install, workflow, and context-boundary outcomes separately. A missing
live checkpoint remains not run/unverified; never upgrade it based on scripted
behavior or a missing marker alone. Report discovered compatibility problems
before installing into the real global profile.
