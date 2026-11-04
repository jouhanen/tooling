"""Installer tests use disposable directories only; no live OpenCode operations."""

import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

from scripts import install as installer
from test_elephant import ROOT
from test_goldfish import effect


def snapshot(root):
    if not root.exists():
        return {}
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in root.rglob("*") if p.is_file() and not p.is_symlink()}


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.project = self.base / "project with spaces ü"
        self.project.mkdir()
        self.target = self.project / ".opencode"

    def install(self, **kwargs):
        plan = installer.install_plan(self.target, **kwargs)
        installer.apply_plan(plan)
        return plan

    def source_copy(self):
        source = self.base / "source"
        source.mkdir()
        shutil.copytree(ROOT / "opencode", source / "opencode")
        for name in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
            shutil.copyfile(ROOT / name, source / name)
        return source

    def manifest(self):
        return json.loads((self.target / installer.MANIFEST).read_text())

    def test_preview_creates_nothing(self):
        plan = installer.install_plan(self.target)
        self.assertTrue(plan.changes)
        self.assertFalse(self.target.exists())
        self.assertEqual(plan.changes[-1].path, installer.MANIFEST)
        self.assertEqual(plan.changes[-1].before, None)

    def test_project_install_preserves_payload_bytes_and_resource_links(self):
        self.install()
        manifest = self.manifest()
        self.assertEqual(manifest["package"], installer.PACKAGE)
        self.assertEqual(manifest["scope"], "project")
        self.assertTrue(manifest["created_root"])
        self.assertEqual(set(manifest["files"]), set(snapshot(self.target)) - {installer.MANIFEST})
        for relative, sha in manifest["files"].items():
            installed = (self.target / relative).read_bytes()
            source = ROOT / Path(relative).name if relative in installer.LEGAL else ROOT / "opencode" / relative
            self.assertEqual(installed, source.read_bytes(), relative)
            self.assertEqual(installer.digest(installed), sha)
        for skill in installer.SKILLS:
            base = self.target / "skills" / skill
            self.assertTrue((base / "../../resources/standards/workflow.md").resolve().is_file())
        self.assertFalse((self.target / "opencode.json").exists())
        self.assertFalse((self.target / "opencode.jsonc").exists())

    def test_global_render_adds_only_bundled_resource_exception(self):
        plan = installer.install_plan(self.target, scope="global")
        installer.apply_plan(plan)
        resource = str(self.target / "resources") + "/*"
        for name in installer.AGENTS:
            text = (self.target / f"agents/{name}.md").read_text()
            _, header, body = text.split("---", 2)
            config = yaml.safe_load(header)
            original = (ROOT / f"opencode/agents/{name}.md").read_text()
            original_config = yaml.safe_load(original.split("---", 2)[1])
            self.assertEqual(body, original.split("---", 2)[2])
            if name == "goldfish-comprehension":
                self.assertEqual(config, original_config)
                self.assertEqual(effect(config, "external_directory", resource), "deny")
            else:
                self.assertEqual(config["permissions"][:-1], original_config["permissions"])
                self.assertEqual(config["permissions"][-1], {
                    "action": "external_directory", "resource": resource, "effect": "allow",
                })
                self.assertEqual(effect(config, "external_directory", str(self.target / "resources/templates") + "/*"), "allow")
                self.assertNotEqual(effect(config, "external_directory", str(self.target / "resources-other") + "/*"), "allow")
            for action in ("shell", "execute", "webfetch", "opencode_read_mcp_resource"):
                self.assertEqual(effect(config, action, "*"), "deny")
            self.assertEqual(effect(config, "edit", "/outside/document.md"), "deny")

    def test_rerun_is_noop(self):
        self.install()
        before = snapshot(self.target)
        self.assertEqual(installer.install_plan(self.target).changes, [])
        installer.apply_plan(installer.install_plan(self.target))
        self.assertEqual(snapshot(self.target), before)

    def test_jsonc_and_unrelated_files_preserved_byte_for_byte(self):
        self.target.mkdir()
        config = b'''// keep this comment\n{
  "default_agent": "plan",
  "model": "test/model",
  "providers": {"test": {"settings": {"apiKey": "synthetic-test-value"}}},
  "agents": {"custom": {"description": "not ours"}},
  "permissions": [{"action":"shell", "resource":"*", "effect":"ask"}],
  "references": {"url": "https://example.test/a//b/*literal*/"},
}\n'''
        (self.target / "opencode.jsonc").write_bytes(config)
        (self.target / "user-notes.txt").write_text("keep")
        self.install()
        self.assertEqual((self.target / "opencode.jsonc").read_bytes(), config)
        self.assertEqual((self.target / "user-notes.txt").read_text(), "keep")
        self.assertFalse(self.manifest()["created_root"])

    def test_unowned_matching_file_is_not_adopted(self):
        path = self.target / "resources/templates/design.md"
        path.parent.mkdir(parents=True)
        path.write_bytes((ROOT / "opencode/resources/templates/design.md").read_bytes())
        before = snapshot(self.target)
        with self.assertRaises(installer.InstallError):
            installer.install_plan(self.target)
        self.assertEqual(snapshot(self.target), before)

    def test_native_and_legacy_discovery_id_collisions(self):
        for relative in (
            "agents/elephant.md", "agent/elephant.md", "mode/elephant.md",
            "modes/elephant.md", "command/egm-review.md", "commands/egm-review.md",
            "skills/egm-review.md", "skill/egm-review/SKILL.md",
            "skills/group/egm-review/SKILL.md",
        ):
            with self.subTest(relative=relative):
                target = self.base / relative.replace("/", "-")
                path = target / relative
                path.parent.mkdir(parents=True)
                path.write_text("user work")
                before = snapshot(target)
                with self.assertRaises(installer.InstallError):
                    installer.install_plan(target)
                self.assertEqual(snapshot(target), before)

    def test_unowned_skill_directory_refused_even_without_skill_file(self):
        path = self.target / "skills/egm-review/notes.txt"
        path.parent.mkdir(parents=True)
        path.write_text("do not combine with this skill")
        with self.assertRaises(installer.InstallError):
            installer.install_plan(self.target)
        self.assertEqual(path.read_text(), "do not combine with this skill")

    def test_config_id_collisions_and_invalid_config_refuse_without_writes(self):
        for index, value in enumerate((
            {"agents": {"elephant": {}}}, {"agent": {"goldfish-design": {}}},
            {"commands": {"egm-review": {}}}, {"command": {"egm-draft": {}}},
            {"agents": []},
        )):
            target = self.base / f"config-{index}"
            target.mkdir()
            path = target / "opencode.json"
            path.write_text(json.dumps(value))
            before = snapshot(target)
            with self.subTest(value=value), self.assertRaises(installer.InstallError):
                installer.install_plan(target)
            self.assertEqual(snapshot(target), before)
        (self.project / "opencode.jsonc").write_text('{"agents":{"elephant":{}}}')
        with self.assertRaises(installer.InstallError):
            installer.install_plan(self.target)
        self.assertFalse(self.target.exists())

    def test_malformed_jsonc_refused_without_rewriting_it(self):
        self.target.mkdir()
        for value in ('{"agents":{/* unclosed', '{"agents":{},"agents":{}}', '[]'):
            path = self.target / "opencode.jsonc"
            path.write_text(value)
            with self.subTest(value=value), self.assertRaises(installer.InstallError):
                installer.install_plan(self.target)
            self.assertEqual(path.read_text(), value)
            self.assertEqual(set(snapshot(self.target)), {"opencode.jsonc"})

    def test_modified_owned_file_blocks_whole_update(self):
        self.install()
        path = self.target / "agents/elephant.md"
        path.write_text(path.read_text() + "\nUser addition\n")
        before = snapshot(self.target)
        with self.assertRaisesRegex(installer.InstallError, "Locally modified"):
            installer.install_plan(self.target)
        self.assertEqual(snapshot(self.target), before)

    def test_update_changes_unmodified_owned_files_and_restores_missing_files(self):
        source = self.source_copy()
        self.install(source=source)
        relative = "resources/templates/concepts.md"
        (source / "opencode" / relative).write_text("New source template\n")
        missing = self.target / "commands/egm-review.md"
        missing.unlink()
        installer.apply_plan(installer.install_plan(self.target, source=source))
        self.assertEqual((self.target / relative).read_text(), "New source template\n")
        self.assertTrue(missing.is_file())
        self.assertEqual(installer.install_plan(self.target, source=source).changes, [])

    def test_owned_file_mode_preserved_on_update(self):
        source = self.source_copy()
        self.install(source=source)
        relative = "commands/egm-review.md"
        (self.target / relative).chmod(0o640)
        (source / "opencode" / relative).write_text("updated command\n")
        installer.apply_plan(installer.install_plan(self.target, source=source))
        self.assertEqual(stat.S_IMODE((self.target / relative).stat().st_mode), 0o640)

    def test_obsolete_owned_file_removed_only_if_unchanged(self):
        source = self.source_copy()
        extra = source / "opencode/resources/templates/extra.md"
        extra.write_text("Old package file\n")
        self.install(source=source)
        extra.unlink()
        installed = self.target / "resources/templates/extra.md"
        installed.write_text("user edited obsolete file")
        with self.assertRaises(installer.InstallError):
            installer.install_plan(self.target, source=source)
        installed.write_text("Old package file\n")
        installer.apply_plan(installer.install_plan(self.target, source=source))
        self.assertFalse(installed.exists())

    def test_uninstall_only_removes_owned_files_and_created_empty_directories(self):
        self.target.mkdir()
        (self.target / "agents").mkdir()  # Preexisting empty directory must stay.
        self.install()
        extra = self.target / "resources/templates/user-note.md"
        extra.write_text("user work")
        (self.target / "opencode.json").write_text('{"default_agent":"build"}')
        plan = installer.uninstall_plan(self.target)
        self.assertEqual(plan.retained, [])
        installer.apply_plan(plan)
        self.assertEqual(snapshot(self.target), {
            "resources/templates/user-note.md": b"user work",
            "opencode.json": b'{"default_agent":"build"}',
        })
        self.assertTrue((self.target / "agents").is_dir())
        self.assertEqual(installer.uninstall_plan(self.target).changes, [])

    def test_uninstall_removes_created_root_only_when_empty(self):
        self.install()
        installer.apply_plan(installer.uninstall_plan(self.target))
        self.assertFalse(self.target.exists())
        self.assertTrue(self.project.exists())

    def test_uninstall_retains_local_edits_with_ownership_and_legal_notices(self):
        self.install()
        relative = "agents/elephant.md"
        path = self.target / relative
        original = path.read_bytes()
        path.write_bytes(original + b"\nUser addition\n")
        plan = installer.uninstall_plan(self.target)
        self.assertEqual(set(plan.retained), {relative, *installer.LEGAL})
        installer.apply_plan(plan)
        self.assertEqual(path.read_bytes(), original + b"\nUser addition\n")
        self.assertEqual(set(self.manifest()["files"]), {relative, *installer.LEGAL})
        self.assertEqual(installer.uninstall_plan(self.target).changes, [])
        path.write_bytes(original)
        installer.apply_plan(installer.uninstall_plan(self.target))
        self.assertFalse(self.target.exists())

    def test_symlink_target_parent_and_source_refused(self):
        outside = self.base / "outside"
        outside.mkdir()
        alias = self.base / "alias"
        alias.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(installer.InstallError):
            installer.install_plan(alias / "config")
        self.target.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(installer.InstallError):
            installer.install_plan(self.target)
        self.assertEqual(snapshot(outside), {})
        source = self.source_copy()
        (source / "opencode/resources/templates/link.md").symlink_to(ROOT / "README.md")
        with self.assertRaises(installer.InstallError):
            installer.install_plan(self.base / "other-target", source=source)

    def test_uninstall_keeps_symlinked_owned_file_and_does_not_touch_referent(self):
        self.install()
        path = self.target / "agents/elephant.md"
        path.unlink()
        referent = self.base / "private.md"
        referent.write_text("unrelated")
        path.symlink_to(referent)
        plan = installer.uninstall_plan(self.target)
        self.assertIn("agents/elephant.md", plan.retained)
        installer.apply_plan(plan)
        self.assertTrue(path.is_symlink())
        self.assertEqual(referent.read_text(), "unrelated")

    def test_symlinked_discovery_tree_refused_without_following_it(self):
        self.target.mkdir()
        outside = self.base / "outside"
        outside.mkdir()
        (self.target / "agents").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(installer.InstallError):
            installer.install_plan(self.target)
        self.assertEqual(snapshot(outside), {})

    def test_unsafe_destinations_and_source_overlap_refused(self):
        for name in ("bad*", "bad?", "{env:HOME}", "bad$root", "bad\nname", "egm.env.local"):
            with self.subTest(name=name), self.assertRaises(installer.InstallError):
                installer.install_plan(self.base / name)
        with self.assertRaises(installer.InstallError):
            installer.install_plan(ROOT / ".opencode")
        with self.assertRaises(installer.InstallError):
            installer.install_plan(self.base / "missing" / ".." / "target")

    def test_manifest_path_tampering_scope_and_destination_mismatch_refused(self):
        self.install()
        manifest_path = self.target / installer.MANIFEST
        original = manifest_path.read_bytes()
        for change in (
            {"files": {"../outside.md": "0" * 64}},
            {"files": {"opencode.json": "0" * 64}},
            {"created_dirs": ["../outside"]}, {"scope": "global"},
            {"destination": "/different/location"}, {"created_root": "yes"},
        ):
            manifest_path.write_bytes(installer.json_bytes(json.loads(original) | change))
            before = snapshot(self.target)
            with self.subTest(change=change), self.assertRaises(installer.InstallError):
                installer.uninstall_plan(self.target)
            self.assertEqual(snapshot(self.target), before)
        manifest_path.write_bytes(original)

    def test_apply_rechecks_preview_before_writing(self):
        plan = installer.install_plan(self.target)
        path = self.target / "agents/elephant.md"
        path.parent.mkdir(parents=True)
        path.write_text("user created after preview")
        before = snapshot(self.target)
        with self.assertRaisesRegex(installer.InstallError, "changed since preview"):
            installer.apply_plan(plan)
        self.assertEqual(snapshot(self.target), before)

    def test_apply_also_rechecks_owned_files_that_did_not_need_updates(self):
        source = self.source_copy()
        self.install(source=source)
        (source / "opencode/commands/egm-review.md").write_text("updated command\n")
        plan = installer.install_plan(self.target, source=source)
        unchanged = self.target / "agents/elephant.md"
        unchanged.write_text(unchanged.read_text() + "\nNew user edit\n")
        before = snapshot(self.target)
        with self.assertRaisesRegex(installer.InstallError, "changed since preview"):
            installer.apply_plan(plan)
        self.assertEqual(snapshot(self.target), before)

    def test_caught_initial_install_error_removes_only_new_files_and_directories(self):
        plan = installer.install_plan(self.target)
        real_open = installer.os.open
        calls = 0

        def fail_once(path, flags, *args, **kwargs):
            nonlocal calls
            if str(path).startswith(str(self.target)) and flags & os.O_EXCL:
                calls += 1
                if calls == 2:
                    raise OSError("synthetic creation failure")
            return real_open(path, flags, *args, **kwargs)

        with patch.object(installer.os, "open", side_effect=fail_once):
            with self.assertRaisesRegex(installer.InstallError, "rolled back"):
                installer.apply_plan(plan)
        self.assertFalse(self.target.exists())
        self.assertTrue(self.project.is_dir())

    def test_caught_io_error_rolls_back_installed_updates(self):
        source = self.source_copy()
        self.install(source=source)
        for name in ("egm-brainstorm", "egm-draft"):
            path = source / f"opencode/commands/{name}.md"
            path.write_text(path.read_text() + "\nUpdated source\n")
        before = snapshot(self.target)
        real_replace = installer.os.replace
        calls = 0

        def fail_once(source_path, target_path):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("synthetic write failure")
            return real_replace(source_path, target_path)

        with patch.object(installer.os, "replace", side_effect=fail_once):
            with self.assertRaisesRegex(installer.InstallError, "rolled back"):
                installer.apply_plan(installer.install_plan(self.target, source=source))
        self.assertEqual(snapshot(self.target), before)
        self.assertEqual(list(self.target.rglob(".egm-write-*")), [])

    def test_cli_defaults_to_preview_and_respects_global_xdg(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(installer.main(["install", "--project", str(self.project)]), 0)
        self.assertIn("DRY RUN", output.getvalue())
        self.assertFalse(self.target.exists())
        fake_config = self.base / "config-home"
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(fake_config)}):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(installer.main(["install", "--global", "--apply"]), 0)
            global_target = fake_config / "opencode"
            self.assertEqual(json.loads((global_target / installer.MANIFEST).read_text())["scope"], "global")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(installer.main(["uninstall", "--global", "--apply"]), 0)
            self.assertFalse(global_target.exists())

    def test_cli_partial_uninstall_returns_two_and_failure_returns_one(self):
        self.install()
        (self.target / "agents/elephant.md").write_text("user edit")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(installer.main(["uninstall", "--project", str(self.project), "--apply"]), 2)
            self.assertEqual(installer.main(["install", "--project", str(self.project), "--apply"]), 1)

    def test_global_home_fallback_and_relative_xdg_refusal(self):
        args = type("Args", (), {"project": None})()
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": ""}):
            with patch.object(installer.Path, "home", return_value=self.base / "fake-home"):
                target, scope = installer.target_from_args(args)
                self.assertEqual(target, self.base / "fake-home/.config/opencode")
                self.assertEqual(scope, "global")
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": "relative"}):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(installer.main(["install", "--global"]), 1)

    def test_real_cli_works_without_site_packages_from_another_directory(self):
        command = [sys.executable, "-S", str(ROOT / "scripts/install.py")]
        install = subprocess.run(
            [*command, "install", "--project", str(self.project), "--apply"],
            cwd=self.base, capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(install.returncode, 0, install.stdout + install.stderr)
        self.assertTrue((self.target / installer.MANIFEST).is_file())
        uninstall = subprocess.run(
            [*command, "uninstall", "--project", str(self.project), "--apply"],
            cwd=self.base, capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(uninstall.returncode, 0, uninstall.stdout + uninstall.stderr)
        self.assertFalse(self.target.exists())


if __name__ == "__main__":
    unittest.main()
