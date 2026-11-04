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
shared contract consistency, and adaptation notices. These are authoring checks,
not a runtime reviewer-result validator or evidence of host discovery.

No test makes model calls, changes the live OpenCode configuration, or establishes
runtime enforcement or reviewer isolation. Native-host probes and live acceptance
tests belong to a later phase and must report their evidence separately.
