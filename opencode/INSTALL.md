# Install, update, and remove the personal workflow

The installer has offline tests but native OpenCode discovery, permissions, and
live workflow behavior are not verified yet. Start with a disposable project.
Installing files is not proof that a Goldfish review is isolated or completes.

Requirements: Python 3.10+ and a Linux/POSIX filesystem, including WSL2. The
installer uses only the Python standard library; PyYAML is for tests, not install
or runtime. Native Windows installation is outside the current scope. Prefer
WSL's Linux filesystem rather than Windows-mounted directories.

Run commands from this repository root. The source checkout must remain available
for updates; the installed runtime does not depend on it or on a sibling EGM repo.
Do not install inside the source checkout or into a directory containing it.

## Preview first

All operations are **dry runs by default**. They create no target directories,
files, locks, or backups unless `--apply` is present. An explicit `--dry-run` is
also accepted. Read the preview and resolve conflicts before applying.

### One project

The project directory must already exist. The target is its `.opencode/` directory:

```sh
python3 scripts/install.py install --project /path/to/project
python3 scripts/install.py install --project /path/to/project --apply
```

Open OpenCode from that project. This does not install into the source tooling
repository or change other projects' configuration. Paths with spaces or Unicode
are supported; quote them in the shell. Use paths without `..` traversal.

### All projects for the current user

```sh
python3 scripts/install.py install --global
python3 scripts/install.py install --global --apply
```

The target is `$XDG_CONFIG_HOME/opencode` when that environment variable is set
to a nonempty absolute path, otherwise `~/.config/opencode`. No system-wide
configuration is modified. Use the same environment and scope for later updates
and removal; do not accidentally target a different profile.

The installer does not run OpenCode, start/restart a service, or make model calls.
OpenCode watches definitions and normally reloads them after a save. Use `/reload`
if needed; a service restart is not required just to load the installed files.
Review effective agents, permissions, skills, and commands before relying on them.
Build, Plan, the default agent, model selection, providers, MCP, and unrelated
settings are not rewritten. Select Elephant explicitly when using this workflow.

## Files and permissions

The installer copies these owned files into the target:

```text
agents/elephant.md
agents/goldfish-*.md
commands/egm-*.md
skills/egm-*/SKILL.md
resources/standards/*.md
resources/templates/*.md
egm-package/LICENSE
egm-package/THIRD_PARTY_NOTICES.md
egm-package/installation.json
```

Skill resource links keep the `../../resources/` layout. No plugin, runtime Python
helper, global AGENTS.md, or opencode.json(c) is installed. Documentation and
operator scripts remain in the source checkout.

For a project install, agent files match the source bytes exactly. Resources are
inside the project worktree, so no external-directory exception is added.

For a global install, Elephant and six source-aware Goldfish receive one generated
`external_directory` allow rule for the absolute installed `resources/*` directory.
It does not grant edits, shell, MCP, network, or general external-project access.
Comprehension is unchanged and receives no such exception. Sensitive-file read
exclusions remain in place. This is a directory exception, not a dynamically
enforced per-assignment reading list; inspect installed policies before use.

The local manifest records package identity, scope/destination, a digest of source
payload hashes, installed SHA-256 hashes, and which directories were created.
It is ownership bookkeeping, not a signed authenticity guarantee. Global rendered
agents and the manifest contain machine-specific installation paths; do not commit
those generated files as the portable source package. Keep this repository as
the source of truth. Do not move or clone an installed ownership manifest to a
different destination; remove/reinstall deliberately at the intended location.

## Collision and update policy

Re-run the same install command to update. An unchanged candidate is a no-op.
Missing owned files are restored; obsolete owned files are removed only when
unchanged. An update refuses the entire preflight if any owned file is locally
modified, even if another file could be updated safely. There is no force/adopt
flag. Keep customizations in the source package, or move local edits aside for
manual reconciliation before updating. Never discard them just to pass the check.

The installer refuses:

- Any unowned file at an intended destination, even with matching content.
- A preexisting unowned directory for one of the four skill IDs.
- Matching agent/command/skill IDs in native or legacy discovery files inside
  this target, including nested skill grouping directories.
- Matching IDs in the target's opencode.json(c), and the adjacent direct project
  opencode.json(c) when targeting `.opencode/`. Intentional same-ID overrides also
  require manual conflict review; the installer will not decide which should win.
- Malformed/uninspectable JSON(C), unsupported ownership metadata, source/destination
  overlap, symlinked targets/parents/discovery entries, and unsafe manifest paths.
- Destination paths containing permission/template metacharacters, control
  characters, or a `.env.` component that would conflict with read exclusions.

It reads supported JSONC for ID checks but never rewrites comments, keys, or
secrets. Conflict messages identify the map/path, not provider credential values.

These checks are **target-local**, not a reconstruction of the effective OpenCode
registry. They do not resolve ancestor/global/managed settings, `.claude`/`.agents`
compatibility sources, explicit extra skill paths/catalogs, plugins, or policies.
An inherited definition can override or interfere with these files. Native host
inspection and isolated-profile probes are still required. Existing symlink-based
dotfile setups need a separate reviewed integration rather than bypassing checks.

## Uninstall

Use the same scope and environment as installation:

```sh
python3 scripts/install.py uninstall --project /path/to/project
python3 scripts/install.py uninstall --project /path/to/project --apply

python3 scripts/install.py uninstall --global
python3 scripts/install.py uninstall --global --apply
```

Only owned files whose bytes match the recorded hashes are removed. Missing owned
files are harmless. Locally modified, symlinked, or unsafe components are retained,
along with available legal notices and a reduced manifest tracking what remains.
Unrelated files and preexisting directories are never recursively deleted.
Only empty directories recorded as created by this installation are eligible for
removal, including the target root when it was created and is now empty.

If local edits remain, inspect the retained paths. Restore the original owned
bytes to opt into their removal, or move the edits aside yourself and rerun
uninstall. Do not delete the manifest to bypass ownership checks. No manifest
means nothing is owned: uninstall does nothing, even if matching filenames exist.
The tool does not restore the old safety policy or touch design/review artifacts
under the project's docs/designs/ tree.

Exit codes: **0** successful preview/apply (including no-op), **1** refusal/error,
**2** partial uninstall with retained files (also reported by its preview).

## Interrupted operations and recovery

Stop work using these definitions and avoid simultaneous edits/installers while
applying updates. The tool rechecks observed files, uses exclusive creation and
same-directory replacements, and attempts to roll back caught write failures.
It preserves existing file modes when replacing owned files. New payload files
are created with mode 0644 subject to umask, and the manifest with mode 0600.

This is not a crash-atomic multi-file transaction or protection against hostile
concurrent filesystem changes. A kill, power loss, permission error during
rollback, or filesystem failure can require manual inspection. Keep a backup of
the profile before the first install. If a partial first install lacks a manifest,
the next run refuses those files as unowned; compare them with the preview/source
and recover deliberately. Do not use recursive deletion or forced adoption as a
recovery shortcut. No known-good user files are intentionally overwritten.
