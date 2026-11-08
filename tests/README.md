# Offline checks

Use Python 3.10+ with PyYAML (test dependency only):

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r tests/requirements.txt
.venv/bin/python -m unittest discover -s tests -v
```

These checks parse agent frontmatter and examine artifact, provenance, and
permission contracts. The small policy matcher uses documented whole-value
wildcards on normalized POSIX inputs, not OpenCode's runtime. It does not model
path canonicalization, configuration merging, saved permissions, or policies.
Text assertions do not prove that a model follows instructions.

Elephant checks cover write scope, exact skill/reviewer allowlists, templates, and
approval/resume rules. Goldfish checks cover all seven IDs, read-only policies,
comprehension's no-glob/target-only rules, distinct lenses, parseable JSON examples,
shared contract consistency, and adaptation notices. Workflow checks cover the
four skill/command pairs, relative resource paths, preset coverage, approval and
failure rules, snapshots, and provenance. These text checks are not model-behavior
tests or evidence of native host discovery.

Installer checks use disposable directories, never the live host profile. They
cover project/global layouts, generated permission exceptions, collision refusal,
JSONC/config preservation, ownership hashes, idempotency, updates, missing and
obsolete files, modified-file retention, symlink/traversal rejection, preview
rechecks, best-effort rollback for injected I/O failures, and CLI exit codes.
Native discovery, effective merged configuration, and runtime enforcement still
need separate probes; source-policy simulations cannot establish those outcomes.
The [opt-in native runner](../opencode/VERIFY.md) has recorded scoped 2.2.5 results
outside ordinary CI; it is not invoked by unittest discovery.

`test_review_contract.py` exercises the read-only operator validator in
`scripts/review_contract.py` with positive/negative declaration fixtures. It checks
strict JSON, assignment identity, required read declarations, target-only
comprehension, finding fields/IDs/severity, malformed/incomplete results, and CLI
exit codes without changing input files. The validator is not available as an
Elephant tool and cannot prove native completion or actual reads.
Live-audit regression cases specifically reject missing certainty on either
finding without repairing it, reject trailing slashes in assignment/read paths
while accepting `/`, and preserve malformed input bytes on CLI failure. Workflow
text checks require explicit raw-copy, native-ID, validation-record, and erratum
instructions; they do not establish that a real model obeys those instructions.
Read-evidence regression text checks separate mandatory read declarations from
independent trace verification: unavailable traces alone must not cause retries
or incomplete coverage, while missing declarations and contradictory evidence
still block acceptance. These checks do not prove actual reads or live compliance.

`test_native_probe.py` uses synthetic contexts and in-memory scripted responses
to check failed/missing native evidence, identity linkage, session reuse,
environment stripping, provider policy, and resource wiring. It never invokes
OpenCode or a model; it may bind a temporary loopback fixture socket.

The ordinary suite makes no model calls and changes no live OpenCode configuration.
It does not establish runtime enforcement or reviewer isolation. The optional
native runner does invoke a private OpenCode server and its own scripted loopback
provider. A [partial live exercise](../opencode/verification/2026-11-08-live-audit.md)
exposed validation/evidence failures; full acceptance of the repaired workflow
remains separately authorized and pending.
