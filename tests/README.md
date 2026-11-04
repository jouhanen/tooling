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

No test makes model calls, changes the live OpenCode configuration, or establishes
runtime enforcement or reviewer isolation. Native-host probes and live acceptance
tests belong to a later phase and must report their evidence separately.
