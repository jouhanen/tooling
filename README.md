# Personal OpenCode design workflow

An independently maintained, Elephant-Goldfish Model (EGM)-derived workflow for
OpenCode V2. Discuss and challenge ideas with an Elephant agent, then review the
design with fresh, specialized Goldfish subagents before implementing it.

This is a personal tooling project, not an official EGM distribution or a Google
product. It does not aim to track upstream EGM behavior exactly.

## Status

Elephant, seven Goldfish agents, four workflow skills/commands, artifact templates,
and review/validation contracts are authored, with offline checks and a read-only
operator validator. The project/global installer supports dry-run, owned-file
updates, and conservative uninstall. Native discovery and sampled dispatch/tool
boundaries passed scripted probes on OpenCode 2.2.5 in isolated project/global
profiles. An earlier live exercise exposed validation and evidence-preservation
failures. A subsequent live test of the repaired workflow exercised reviews,
resolution, stale-coverage detection, and handoff; synthetic saved-result
validation passed, but native malformed-response handling remains unverified.
Full acceptance remains pending. Start with a disposable project.
See [verification](opencode/VERIFY.md) for scope
and evidence, not a general isolation claim.

The initial target is OpenCode **V2.2.5 on Linux, including WSL2**. This is a
development baseline, not a claim of verified workflow support.

## Intended workflow

1. **Brainstorm:** Elephant explores the problem, challenges assumptions, and
   discusses alternatives with you.
2. **Draft:** Elephant writes a design in sections, pausing for your approval.
3. **Review:** fresh Goldfish subagents independently inspect the document and
   approved reference material.
4. **Resolve:** Elephant consolidates findings and applies only approved changes.
5. **Implement:** you switch to Build with the approved design.

Goldfish reviewers will cover the big picture, comprehension, architecture,
structure, style, codebase accuracy, and implementation readiness. Fresh
conversations and tool restrictions are not a filesystem or process sandbox.

## Scope

- Native V2 agents, skills, and slash commands; no custom runtime plugin initially.
- Documentation-only Elephant and read-only Goldfish permissions.
- Explicit human checkpoints and durable design/review artifacts.
- Portable, opt-in project or global installation that preserves unrelated settings.
- Offline checks and separately authorized host/model verification.

The workflow will not replace Build or Plan, change the default agent, prescribe
a model, or impose a global Git/GitHub policy. Bootstrap workers, application-code
generation, automatic commits, and marketplace publishing are outside the initial
scope.

## Repository

- [`opencode/`](opencode/README.md): workflow package and development status.
- [`opencode/WORKFLOW.md`](opencode/WORKFLOW.md): commands, review presets,
  approval gates, and artifact lifecycle.
- [`opencode/INSTALL.md`](opencode/INSTALL.md): opt-in installation, updates,
  collision checks, and removal.
- [`opencode/VERIFY.md`](opencode/VERIFY.md): native probes, recorded limits, and
  the separately authorized live acceptance checklist.
- [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md): EGM attribution and source
  provenance.
- [`tests/`](tests/README.md): offline checks and their verification limits.
- [`LICENSE`](LICENSE): Apache License 2.0, covering this repository unless a file
  states otherwise.

The package will be self-contained: users will not need an EGM checkout beside
this repository. Development here does not install anything into the host's
OpenCode configuration.
