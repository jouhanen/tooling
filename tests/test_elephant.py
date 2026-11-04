"""Offline authoring/policy contracts, not proof of OpenCode enforcement."""

import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "opencode/agents/elephant.md"
TEMPLATES = ROOT / "opencode/resources/templates"
REVIEWERS = {
    "goldfish-zoom-out", "goldfish-comprehension", "goldfish-design",
    "goldfish-structure", "goldfish-style", "goldfish-codebase",
    "goldfish-readiness",
}
SKILLS = {"egm-brainstorm", "egm-draft", "egm-review", "egm-resolve"}


def matches(pattern, value):
    """Documented V2 whole-value wildcard semantics on normalized POSIX inputs.

    This deliberately does not emulate host path canonicalization, saved
    approvals, external-directory checks, configuration merging, or policies.
    """
    expression = re.escape(pattern).replace(r"\*", ".*").replace(r"\?", ".")
    return re.fullmatch(expression, value, flags=re.DOTALL) is not None


class ElephantContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        text = AGENT.read_text(encoding="utf-8")
        _, header, cls.body = text.split("---", 2)
        cls.config = yaml.safe_load(header)
        cls.rules = cls.config["permissions"]

    def effect(self, action, resource):
        result = None
        for rule in self.rules:
            if matches(rule["action"], action) and matches(rule["resource"], resource):
                result = rule["effect"]
        return result

    def test_native_v2_frontmatter(self):
        self.assertEqual(
            set(self.config), {"description", "mode", "color", "permissions"}
        )
        self.assertEqual(self.config["mode"], "primary")
        self.assertTrue(self.config["description"])
        self.assertRegex(self.config["color"], r"^#[0-9A-Fa-f]{6}$")
        for rule in self.rules:
            self.assertEqual(set(rule), {"action", "resource", "effect"})
            self.assertTrue(all(isinstance(v, str) for v in rule.values()))
            self.assertIn(rule["effect"], {"allow", "deny", "ask"})

    def test_deny_by_default(self):
        self.assertEqual(
            self.rules[0], {"action": "*", "resource": "*", "effect": "deny"}
        )
        for action in (
            "shell", "webfetch", "websearch", "execute", "unknown_plugin_tool",
            "opencode_list_mcp_resources", "opencode_read_mcp_resource",
            "experimental_image_generate", "grep",
        ):
            with self.subTest(action=action):
                self.assertEqual(self.effect(action, "*"), "deny")

    def test_markdown_artifact_writes(self):
        for path in (
            "docs/designs/concepts.md", "docs/designs/example/design.md",
            "docs/designs/example/reviews/round-01.md",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.effect("edit", path), "allow")

    def test_other_writes_denied(self):
        for path in (
            "src/main.py", "README.md", "docs/designs/example/worker.py",
            "docs/designs/example/state.json", ".opencode/agents/elephant.md",
            "other-project/docs/designs/example.md", "notes/design.md",
            "/outside/docs/designs/example.md",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.effect("edit", path), "deny")

    def test_discovery_and_questions(self):
        for action, resource in (
            ("read", "src/main.py"), ("glob", "src/**/*.py"), ("question", "*"),
        ):
            self.assertEqual(self.effect(action, resource), "allow")

    def test_external_access_asks_separately(self):
        self.assertEqual(self.effect("external_directory", "/outside/*"), "ask")

    def test_sensitive_reads(self):
        for path in (".env", "app/.env", "app/.env.production", "/outside/.env"):
            with self.subTest(path=path):
                self.assertEqual(self.effect("read", path), "deny")
        self.assertEqual(self.effect("read", "app/.env.example"), "allow")

    def test_exact_reviewer_allowlist(self):
        allowed = {
            r["resource"] for r in self.rules
            if r["action"] == "subagent" and r["effect"] == "allow"
        }
        self.assertEqual(allowed, REVIEWERS)
        for reviewer in REVIEWERS:
            self.assertEqual(self.effect("subagent", reviewer), "allow")
        for reviewer in ("general", "explore", "elephant", "goldfish-unregistered"):
            self.assertEqual(self.effect("subagent", reviewer), "deny")

    def test_exact_skill_allowlist(self):
        allowed = {
            r["resource"] for r in self.rules
            if r["action"] == "skill" and r["effect"] == "allow"
        }
        self.assertEqual(allowed, SKILLS)
        self.assertEqual(self.effect("skill", "unrelated"), "deny")

    def test_guardrails_present(self):
        # Text contracts guard accidental removal, not model compliance.
        body = " ".join(self.body.split())
        for phrase in (
            "Ask one consequential, open-ended question at a time",
            "wait for approval before drafting the next section",
            "a review request is not permission to revise the target",
            "never resume a reviewer",
            "must not claim a complete review workflow without them",
            "mark affected approvals/reviews stale",
            "Tell the user to switch to Build",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase.lower(), body.lower())

    def test_templates_have_revision_and_pending_approval(self):
        for name, revision in (("concepts.md", "concepts-r1"), ("design.md", "design-r1")):
            text = (TEMPLATES / name).read_text(encoding="utf-8")
            self.assertIn(revision, text)
            self.assertIn("## Approval", text)
            self.assertIn("pending", text)

    def test_state_captures_resume_and_findings(self):
        text = (TEMPLATES / "review-state.md").read_text(encoding="utf-8")
        for heading in (
            "## Approval record", "## Section checkpoints", "## Review rounds",
            "## Findings ledger", "## Resume checkpoint",
        ):
            self.assertIn(heading, text)
        for field in ("snapshot", "Actual user response", "fixed-unverified", "stale"):
            self.assertIn(field, text)

    def test_adaptations_have_provenance(self):
        notice = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        for file in (AGENT, TEMPLATES / "concepts.md", TEMPLATES / "design.md"):
            text = file.read_text(encoding="utf-8")
            self.assertIn("Copyright 2026 Google LLC", text)
            self.assertIn("Changes:", text)
            self.assertIn("464db031e7dd1b9a79803ac8ea45f55c7c20c5bc", text)
            self.assertIn(file.relative_to(ROOT).as_posix(), notice)


if __name__ == "__main__":
    unittest.main()
