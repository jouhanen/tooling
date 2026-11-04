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

`test_review_contract.py` exercises the read-only operator validator in
`scripts/review_contract.py` with positive/negative declaration fixtures. It checks
strict JSON, assignment identity, required read declarations, target-only
comprehension, finding fields/IDs/severity, malformed/incomplete results, and CLI
exit codes without changing input files. The validator is not available as an
Elephant tool and cannot prove native completion or actual reads.

No test makes model calls, changes the live OpenCode configuration, or establishes
runtime enforcement or reviewer isolation. Native-host probes and live acceptance
tests belong to a later phase and must report their evidence separately.
