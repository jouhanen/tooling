# SPDX-License-Identifier: Apache-2.0

"""Preview/apply a file-owned OpenCode workflow installation or removal.

Python standard library only. Never edits OpenCode JSON(C), calls OpenCode, or
contacts a provider. Filesystem preflight is conservative, not a sandbox against
concurrent hostile changes. Stop sessions/editors before applying package changes.
"""

import argparse
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "personal-elephant-goldfish"
MANIFEST = "egm-package/installation.json"
LEGAL = {"egm-package/LICENSE", "egm-package/THIRD_PARTY_NOTICES.md"}
AGENTS = {
    "elephant", "goldfish-zoom-out", "goldfish-comprehension", "goldfish-design",
    "goldfish-structure", "goldfish-style", "goldfish-codebase", "goldfish-readiness",
}
SKILLS = {"egm-brainstorm", "egm-draft", "egm-review", "egm-resolve"}


class InstallError(ValueError):
    """Unsafe target, invalid ownership metadata, or an installation conflict."""


def require(condition, message):
    if not condition:
        raise InstallError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result

    def constant(_):
        raise InstallError("Non-JSON constant")

    try:
        return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    except InstallError:
        raise
    except (ValueError, RecursionError) as error:
        raise InstallError("Invalid JSON/JSONC document") from error


def read_jsonc(path):
    # Preserve string literals; remove comments and trailing commas outside them.
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/',
        lambda m: m[0] if m[0].startswith('"') else " ", text,
    )
    text = re.sub(r'("(?:\\.|[^"\\])*")|,(\s*[}\]])', lambda m: m[1] or m[2], text)
    value = strict_json(text)
    require(isinstance(value, dict), f"Configuration is not an object: {path}")
    return value


def check_directories(path):
    """Refuse symlink/non-directory components, including dangling symlinks."""
    for current in reversed((path, *path.parents)):
        require(not current.is_symlink(), f"Symlink directory is not supported: {current}")
        require(not current.exists() or current.is_dir(), f"Not a directory: {current}")


def destination(path):
    require(os.name == "posix" and hasattr(os, "O_NOFOLLOW"), "Installer requires Linux/POSIX (including WSL2)")
    path = Path(path).expanduser().absolute()
    require(".." not in path.parts, "Use a destination without parent traversal")
    check_directories(path)
    path = path.resolve()
    text = str(path)
    require(not any(c in text for c in '*?{}$`!\\') and not any(ord(c) < 32 for c in text),
            "Destination contains permission/template characters or control characters")
    require(".env." not in text.lower(), "Destination conflicts with sensitive-file read rules")
    require(path != Path(path.anchor), "Cannot install at filesystem root")
    return path


def allowed_file(relative):
    if (not isinstance(relative, str) or any(c in relative for c in '*?{}$`!\\')
            or any(ord(c) < 32 for c in relative)):
        return False
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != relative:
        return False
    if relative in LEGAL:
        return True
    parts = path.parts
    if len(parts) == 2 and parts[0] == "agents":
        return path.suffix == ".md" and path.stem in AGENTS
    if len(parts) == 2 and parts[0] == "commands":
        return path.suffix == ".md" and path.stem in SKILLS
    if len(parts) >= 3 and parts[0] == "skills" and parts[1] in SKILLS:
        return path.suffix == ".md" and not any(part.startswith(".") for part in parts)
    return (len(parts) >= 3 and parts[0] == "resources"
            and parts[1] in {"standards", "templates"} and path.suffix == ".md"
            and not any(part.startswith(".") for part in parts))


def read_owned(root, relative):
    path = root / relative
    check_directories(path.parent)
    require(not path.is_symlink(), f"Symlink file is not supported: {path}")
    require(not path.exists() or path.is_file(), f"Not a regular file: {path}")
    return path.read_bytes() if path.exists() else None


def source_payload(source, target, scope):
    source = Path(source).resolve()
    require(not target.is_relative_to(source) and not source.is_relative_to(target),
            "Installation destination and source tree must not overlap")
    raw = {}
    for directory in ("agents", "commands", "skills", "resources"):
        base = source / "opencode" / directory
        check_directories(base)
        require(base.is_dir(), f"Missing source directory: {base}")
        for path in sorted(base.rglob("*")):
            require(not path.is_symlink(), f"Source symlink is not supported: {path}")
            if path.is_dir():
                continue
            relative = path.relative_to(source / "opencode").as_posix()
            require(path.is_file() and allowed_file(relative), f"Unsupported package file: {relative}")
            raw[relative] = path.read_bytes()
    require({Path(p).stem for p in raw if p.startswith("agents/")} == AGENTS, "Incomplete agent package")
    require({Path(p).stem for p in raw if p.startswith("commands/")} == SKILLS, "Incomplete command package")
    require(all(f"skills/{name}/SKILL.md" in raw for name in SKILLS), "Incomplete skill package")
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
        path = source / name
        require(not path.is_symlink() and path.is_file(), f"Missing or unsafe legal source: {name}")
        raw[f"egm-package/{name}"] = path.read_bytes()
    payload = dict(raw)
    if scope == "global":
        # Global resources are external to a consumer project. Add only that
        # directory exception; comprehension still has no external access.
        rule = ("  # Installer-generated: bundled resources only; no additional tools.\n"
                "  - action: external_directory\n"
                f"    resource: {json.dumps(str(target / 'resources') + '/*', ensure_ascii=False)}\n"
                "    effect: allow\n")
        for name in AGENTS - {"goldfish-comprehension"}:
            relative = f"agents/{name}.md"
            text = raw[relative].decode("utf-8")
            header, separator, body = text.partition("\n---\n")
            require(header.startswith("---\n") and "\npermissions:\n" in header and separator,
                    f"Cannot render agent permissions: {name}")
            payload[relative] = (header + "\n" + rule + "---\n" + body).encode("utf-8")
    hashes = {path: digest(data) for path, data in raw.items()}
    return payload, digest(json_bytes(hashes))


def load_manifest(root, scope):
    raw = read_owned(root, MANIFEST)
    if raw is None:
        return None, None
    value = strict_json(raw.decode("utf-8"))
    keys = {"format", "package", "destination", "scope", "source_digest", "files", "created_dirs", "created_root"}
    require(isinstance(value, dict) and set(value) == keys, "Invalid installation manifest fields")
    require(type(value["format"]) is int and value["format"] == 1 and value["package"] == PACKAGE,
            "Unsupported installation manifest")
    require(value["destination"] == str(root) and value["scope"] == scope,
            "Manifest destination/scope mismatch; do not move an installed package")
    require(isinstance(value["source_digest"], str) and re.fullmatch(r"[0-9a-f]{64}", value["source_digest"]),
            "Invalid source digest")
    require(isinstance(value["files"], dict), "Invalid manifest file inventory")
    for relative, sha in value["files"].items():
        require(allowed_file(relative), "Unsafe manifest file path")
        require(isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{64}", sha), "Invalid manifest file hash")
    dirs = value["created_dirs"]
    require(isinstance(dirs, list) and all(isinstance(p, str) for p in dirs), "Invalid directory inventory")
    permitted_dirs = {"egm-package"}
    for relative in value["files"]:
        permitted_dirs.update(str(p) for p in PurePosixPath(relative).parents if str(p) != ".")
    require(len(dirs) == len(set(dirs)) and set(dirs) <= permitted_dirs, "Unsafe manifest directory path")
    require(type(value["created_root"]) is bool, "Invalid created_root flag")
    return value, raw


def check_collisions(root, owned):
    """Check IDs in this target's native files and adjacent project config only.

    This is not OpenCode's effective registry: inherited/global/managed files,
    explicit skill paths, compatibility catalogs, and plugins need host checks.
    """
    for directory in ("agents", "agent", "modes", "mode", "commands", "command", "skills", "skill"):
        base = root / directory
        check_directories(base)
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            require(not path.is_symlink(), f"Cannot inspect symlink discovery entry: {path}")
            if not path.is_file() or path.suffix != ".md":
                continue
            if directory in ("skills", "skill"):
                identity = path.parent.name if path.name == "SKILL.md" else path.stem if path.parent == base else None
                collision = identity in SKILLS
            else:
                identity = path.relative_to(base).with_suffix("").as_posix()
                collision = identity in (AGENTS if directory in ("agents", "agent", "modes", "mode") else SKILLS)
            require(not collision or path.relative_to(root).as_posix() in owned, f"Discovery ID collision: {path}")
    for name in SKILLS:
        base = root / "skills" / name
        require(not base.exists() or f"skills/{name}/SKILL.md" in owned,
                f"Unowned skill directory: {base}")
    configs = [root / f"opencode.{extension}" for extension in ("json", "jsonc")]
    if root.name == ".opencode":
        configs += [root.parent / f"opencode.{extension}" for extension in ("json", "jsonc")]
    for path in configs:
        require(not path.is_symlink(), f"Configuration symlink cannot be collision-checked: {path}")
        if not path.exists():
            continue
        require(path.is_file(), f"Configuration is not a regular file: {path}")
        config = read_jsonc(path)
        for key in ("agents", "agent", "mode", "modes", "commands", "command"):
            if key not in config:
                continue
            require(isinstance(config[key], dict), f"Cannot inspect config map {key}: {path}")
            reserved = SKILLS if key in ("commands", "command") else AGENTS
            require(not set(config[key]) & reserved, f"Configuration ID collision in {key}: {path}")


@dataclass
class Change:
    path: str
    before: bytes | None
    after: bytes | None


@dataclass
class Plan:
    root: Path
    operation: str
    changes: list[Change] = field(default_factory=list)
    observed: dict[str, bytes | None] = field(default_factory=dict)
    retained: list[str] = field(default_factory=list)
    cleanup_dirs: list[str] = field(default_factory=list)
    cleanup_root: bool = False


def install_plan(target, *, scope="project", source=ROOT):
    require(scope in ("project", "global"), "Unknown installation scope")
    root = destination(target)
    payload, source_digest = source_payload(source, root, scope)
    manifest, manifest_raw = load_manifest(root, scope)
    owned = manifest["files"] if manifest else {}
    check_collisions(root, owned)
    plan = Plan(root, "install")
    for relative in sorted(set(payload) | set(owned)):
        before = read_owned(root, relative)
        plan.observed[relative] = before
        if relative in owned:
            require(before is None or digest(before) == owned[relative], f"Locally modified owned file: {relative}")
        else:
            require(before is None, f"Unowned file collision: {relative}")
        after = payload.get(relative)
        if before != after:
            plan.changes.append(Change(relative, before, after))
    created_dirs = set(manifest["created_dirs"]) if manifest else set()
    for relative in (*payload, MANIFEST):
        for parent in PurePosixPath(relative).parents:
            if str(parent) != "." and not (root / str(parent)).exists():
                created_dirs.add(str(parent))
    # Drop historical directories that no longer belong to any inventory path.
    current_dirs = {str(p) for relative in (*payload, MANIFEST)
                    for p in PurePosixPath(relative).parents if str(p) != "."}
    new_manifest = {
        "format": 1, "package": PACKAGE, "destination": str(root), "scope": scope,
        "source_digest": source_digest,
        "files": {path: digest(data) for path, data in payload.items()},
        "created_dirs": sorted(created_dirs & current_dirs),
        "created_root": manifest["created_root"] if manifest else not root.exists(),
    }
    plan.cleanup_dirs = sorted(created_dirs - current_dirs, key=lambda p: (p.count("/"), p), reverse=True)
    after = json_bytes(new_manifest)
    plan.observed[MANIFEST] = manifest_raw
    if after != manifest_raw:
        plan.changes.append(Change(MANIFEST, manifest_raw, after))
    return plan


def uninstall_plan(target, *, scope="project"):
    require(scope in ("project", "global"), "Unknown installation scope")
    root = destination(target)
    manifest, raw = load_manifest(root, scope)
    plan = Plan(root, "uninstall")
    if manifest is None:
        return plan
    retained = {}
    removable = {}
    for relative, sha in manifest["files"].items():
        try:
            current = read_owned(root, relative)
        except InstallError:
            current = None
            retained[relative] = sha
        else:
            if current is not None and digest(current) != sha:
                retained[relative] = sha
            elif current is not None:
                removable[relative] = current
    if retained:
        # Keep license/attribution alongside any retained modified components.
        for relative in LEGAL & removable.keys():
            retained[relative] = manifest["files"][relative]
            del removable[relative]
    plan.retained = sorted(retained)
    plan.changes = [Change(path, data, None) for path, data in sorted(removable.items())]
    if retained:
        manifest["files"] = retained
        permitted_dirs = {"egm-package"}
        for relative in retained:
            permitted_dirs.update(str(p) for p in PurePosixPath(relative).parents if str(p) != ".")
        manifest["created_dirs"] = [p for p in manifest["created_dirs"] if p in permitted_dirs]
        after = json_bytes(manifest)
    else:
        after = None
    if after != raw:
        plan.changes.append(Change(MANIFEST, raw, after))
    # Only empty directories created by this installation are eligible.
    original, _ = load_manifest(root, scope)
    plan.cleanup_dirs = sorted(original["created_dirs"], key=lambda p: (p.count("/"), p), reverse=True)
    plan.cleanup_root = original["created_root"] and not retained
    return plan


def ensure_directories(path, created):
    check_directories(path)
    for current in reversed((path, *path.parents)):
        if not current.exists():
            current.mkdir()
            created.append(current)


def replace_file(path, data, mode):
    """Same-directory atomic replacement; always remove a failed temp file."""
    descriptor, name = tempfile.mkstemp(prefix=".egm-write-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as file:
            file.write(data)
            file.flush()
            os.fsync(file.fileno())
        temporary.chmod(mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def apply_plan(plan):
    """Recheck all preimages, then apply; caught I/O errors get best-effort rollback.

    This is not crash-atomic or hardened against hostile concurrent filesystem
    changes. An interrupted process may need manual recovery; never adopt unknown
    files or delete broad directory trees to recover.
    """
    for relative, before in plan.observed.items():
        require(read_owned(plan.root, relative) == before,
                f"Destination changed since preview: {relative}")
    for change in plan.changes:
        require(read_owned(plan.root, change.path) == change.before,
                f"Destination changed since preview: {change.path}")
    created, applied = [], []
    try:
        for change in plan.changes:
            path = plan.root / change.path
            ensure_directories(path.parent, created)
            require(read_owned(plan.root, change.path) == change.before,
                    f"Destination changed during apply: {change.path}")
            mode = stat.S_IMODE(path.stat().st_mode) if change.before is not None else (0o600 if change.path == MANIFEST else 0o644)
            if change.after is None:
                path.unlink()
                applied.append((change, mode))
            elif change.before is None:
                descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
                applied.append((change, mode))
                with os.fdopen(descriptor, "wb") as file:
                    file.write(change.after)
                    file.flush()
                    os.fsync(file.fileno())
            else:
                replace_file(path, change.after, mode)
                applied.append((change, mode))
    except (OSError, InstallError) as error:
        rollback_errors = []
        for change, mode in reversed(applied):
            try:
                path = plan.root / change.path
                check_directories(path.parent)
                require(not path.is_symlink(), f"Rollback path became a symlink: {path}")
                if change.before is None:
                    path.unlink(missing_ok=True)
                else:
                    replace_file(path, change.before, mode)
            except (OSError, InstallError) as rollback_error:
                rollback_errors.append(str(rollback_error))
        for path in reversed(created):
            try:
                path.rmdir()
            except OSError:
                pass
        suffix = f"; rollback needs manual inspection: {rollback_errors}" if rollback_errors else "; rolled back applied file changes"
        raise InstallError(f"Apply failed: {error}{suffix}") from error
    for relative in plan.cleanup_dirs:
        try:
            path = plan.root / relative
            check_directories(path)
            path.rmdir()
        except (OSError, InstallError):
            pass  # Modified files, extra files, or preexisting directories stay.
    if plan.cleanup_root:
        try:
            plan.root.rmdir()
        except OSError:
            pass


def target_from_args(args):
    if args.project is not None:
        project = Path(args.project).expanduser().absolute()
        check_directories(project)
        require(project.is_dir(), "Project directory must already exist")
        return project / ".opencode", "project"
    home = os.environ.get("XDG_CONFIG_HOME")
    if home:
        require(Path(home).is_absolute(), "XDG_CONFIG_HOME must be absolute")
        return Path(home) / "opencode", "global"
    return Path.home() / ".config" / "opencode", "global"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("install", "uninstall"))
    location = parser.add_mutually_exclusive_group(required=True)
    location.add_argument("--project", type=Path, help="Existing project; targets its .opencode directory")
    location.add_argument("--global", dest="global_install", action="store_true", help="Targets the user's OpenCode config directory")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--apply", action="store_true", help="Explicitly apply the displayed changes")
    action.add_argument("--dry-run", action="store_true", help="Preview only (the default)")
    args = parser.parse_args(argv)
    try:
        target, scope = target_from_args(args)
        plan = install_plan(target, scope=scope) if args.operation == "install" else uninstall_plan(target, scope=scope)
        print(f"{'APPLY' if args.apply else 'DRY RUN'} {args.operation}: {plan.root}")
        if args.operation == "install" and scope == "global":
            print(f"  Agent exception: bundled {plan.root / 'resources'}/* only; none for comprehension.")
        for change in plan.changes:
            label = "REMOVE" if change.after is None else "CREATE" if change.before is None else "UPDATE"
            print(f"  {label} {change.path}")
        for path in plan.retained:
            print(f"  KEEP {path} (modified/unsafe component or retained legal notice)")
        if not plan.changes:
            print("  No file changes.")
        if args.apply:
            apply_plan(plan)
        print("No JSON(C) files or provider/model/default-agent settings were rewritten; no service commands ran.")
        print("Native discovery, effective configuration, and enforcement still require host verification.")
        return 2 if plan.retained else 0
    except (InstallError, OSError, UnicodeError) as error:
        print(f"REFUSED: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
