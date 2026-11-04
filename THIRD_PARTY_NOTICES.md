# Third-party notices and provenance

## Elephant-Goldfish Model

- Project: Elephant-Goldfish Model (EGM)
- Source: <https://github.com/google/elephant-goldfish-model>
- Reference commit: `464db031e7dd1b9a79803ac8ea45f55c7c20c5bc`
- License: Apache License, Version 2.0; see [`LICENSE`](LICENSE).
- Upstream attribution: Copyright 2026 Google LLC.

This independent project derives its design/review approach from EGM. It is not
endorsed by or affiliated with the upstream maintainers or Google. The upstream
project describes itself as not an officially supported Google product.

### Imported-file inventory

| Local file | Upstream file | Treatment |
| --- | --- | --- |
| `LICENSE` | `LICENSE` | Copied unchanged from the reference commit |
| `opencode/agents/elephant.md` | `skills/egm-brainstorm/SKILL.md`; `skills/egm-draft/SKILL.md` | Adapted questioning, artifact-first drafting, independent review, and approval rules into a V2 primary agent; added local permissions and resume contracts |
| `opencode/resources/templates/concepts.md` | `skills/egm-brainstorm/SKILL.md` | Adapted concept structure; added evidence, revision, and explicit approval fields |
| `opencode/resources/templates/design.md` | `skills/egm-draft/SKILL.md` | Adapted drafting sections; added revision, operational risks, and implementation approval fields |
| `opencode/agents/goldfish-zoom-out.md` | `agents/zoom_out.md` | Adapted necessity, simplicity, and reuse lens into a V2 agent with bounded reads and unified results |
| `opencode/agents/goldfish-comprehension.md` | `agents/comprehension.md` | Adapted paraphrase and self-containment checks; target-only reads, no glob, calibrated severity |
| `opencode/agents/goldfish-design.md` | `agents/design_critic.md` | Adapted architecture, failure, and resource checks; concept-aware expectations and unified results |
| `opencode/agents/goldfish-structure.md` | `agents/structural.md` | Adapted structure checks; prioritize substantive coverage over exact heading spelling |
| `opencode/agents/goldfish-style.md` | `agents/style.md` | Adapted precision, claim calibration, and editorial actions; preserve useful operational cautions |
| `opencode/agents/goldfish-codebase.md` | `agents/codebase_details.md` | Adapted current-state verification and proposed-file distinction; bounded source evidence rather than exhaustive documentation |
| `opencode/agents/goldfish-readiness.md` | `agents/implementation_readiness.md` | Adapted actionability, compatibility, and rollout checks; preserve ordinary implementation discretion |

All adaptations above use the reference commit recorded at the top of this file
and carry source and change notices. `review-state.md`, the shared
`resources/standards/goldfish-report.md` protocol under `opencode/`, the offline
tests, and repository documentation are original local additions, not copied
upstream files. No upstream `NOTICE` file was found in the reference checkout.

### Rules for subsequent adaptations

When importing or adapting a file, update the inventory with its source path and
reference commit. Retain applicable upstream copyright, attribution, and license
notices. Prominently mark modified files as adapted and describe the changes.
Do not attribute original local additions to Google.

Candidate reference material includes upstream `skills/egm-brainstorm/`,
`skills/egm-draft/`, `skills/egm-review/`, `skills/egm-review-loop/`,
`skills/egm-resolve/`, the seven reviewer personas under `agents/`, and selected
files under `resources/document_standards/`. This list is not an imported-file
inventory or a promise of compatibility with the full upstream protocol.

All material required at runtime will live in this repository and its installed
package. The upstream checkout is a development reference only.
