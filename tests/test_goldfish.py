"""Offline Goldfish prompt contracts; no model or OpenCode calls."""

import json
import re
import unittest

import yaml

from test_elephant import REVIEWERS, ROOT, matches


SOURCES = {
    "goldfish-zoom-out": "agents/zoom_out.md",
    "goldfish-comprehension": "agents/comprehension.md",
    "goldfish-design": "agents/design_critic.md",
    "goldfish-structure": "agents/structural.md",
    "goldfish-style": "agents/style.md",
    "goldfish-codebase": "agents/codebase_details.md",
    "goldfish-readiness": "agents/implementation_readiness.md",
}
RESULT_KEYS = {
    "reviewer", "status", "target", "revision", "round", "scope", "reads",
    "missing_inputs", "summary", "findings",
}


def effect(config, action, resource):
    result = None
    for rule in config["permissions"]:
        if matches(rule["action"], action) and matches(rule["resource"], resource):
            result = rule["effect"]
    return result


class GoldfishContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agents = {}
        for file in (ROOT / "opencode/agents").glob("goldfish-*.md"):
            text = file.read_text(encoding="utf-8")
            _, header, body = text.split("---", 2)
            cls.agents[file.stem] = (yaml.safe_load(header), body)

    def test_agents_match_elephant_allowlist(self):
        self.assertEqual(set(self.agents), REVIEWERS)
        self.assertEqual(set(self.agents), set(SOURCES))

    def test_native_frontmatter(self):
        descriptions = set()
        for name, (config, _) in self.agents.items():
            with self.subTest(reviewer=name):
                self.assertEqual(set(config), {"description", "mode", "color", "permissions"})
                self.assertEqual(config["mode"], "subagent")
                self.assertTrue(config["description"])
                self.assertRegex(config["color"], r"^#[0-9A-Fa-f]{6}$")
                descriptions.add(config["description"])
                for rule in config["permissions"]:
                    self.assertEqual(set(rule), {"action", "resource", "effect"})
                    self.assertTrue(all(isinstance(v, str) for v in rule.values()))
                    self.assertIn(rule["effect"], {"allow", "deny", "ask"})
        self.assertEqual(len(descriptions), 7)

    def test_deny_everything_except_read_and_optional_glob(self):
        for name, (config, _) in self.agents.items():
            with self.subTest(reviewer=name):
                rules = config["permissions"]
                self.assertEqual(rules[0], {"action": "*", "resource": "*", "effect": "deny"})
                allowed_actions = {"read"} if name == "goldfish-comprehension" else {"read", "glob"}
                self.assertEqual(
                    {r["action"] for r in rules if r["effect"] == "allow"}, allowed_actions
                )
                self.assertFalse(any(r["effect"] == "ask" for r in rules))
                for action in (
                    "edit", "shell", "subagent", "question", "skill", "grep",
                    "webfetch", "websearch", "execute", "external_directory",
                    "opencode_list_mcp_resources", "opencode_read_mcp_resource",
                    "example_mcp_tool", "unknown_plugin_tool", "experimental_image_generate",
                ):
                    self.assertEqual(effect(config, action, "*"), "deny", (name, action))
                for path in ("design.md", "src/main.py", "docs/designs/a/design.md"):
                    self.assertEqual(effect(config, "edit", path), "deny")
                self.assertEqual(effect(config, "subagent", "general"), "deny")

    def test_sensitive_read_rules(self):
        for name, (config, _) in self.agents.items():
            with self.subTest(reviewer=name):
                self.assertEqual(effect(config, "read", "docs/designs/a/design.md"), "allow")
                self.assertEqual(effect(config, "read", "src/service.py"), "allow")
                for path in (".env", "app/.env", "app/.env.local", "/outside/.env.production"):
                    self.assertEqual(effect(config, "read", path), "deny", path)
                self.assertEqual(effect(config, "read", "app/.env.example"), "allow")
                self.assertEqual(effect(config, "external_directory", "/outside/*"), "deny")

    def test_comprehension_target_only(self):
        config, body = self.agents["goldfish-comprehension"]
        self.assertEqual(effect(config, "glob", "**/*"), "deny")
        flat = " ".join(body.split())
        for phrase in (
            "Read only the entire target document",
            "ReadingList (must be empty)", "Standard (must be explicit none)",
            "What this proposes:", "How the existing system works, per this document:",
            "return incomplete before reading them", "prompt boundary",
        ):
            self.assertIn(phrase, flat)

    def test_shared_source_read_boundary(self):
        contracts = []
        for name, (_, body) in self.agents.items():
            if name == "goldfish-comprehension":
                continue
            contract = body.split("## Assignment and read boundary\n", 1)[1].split(
                "## Result contract\n", 1
            )[0]
            contracts.append(contract)
            flat = " ".join(contract.split())
            for phrase in (
                "every ReadingList file", "within approved DiscoveryRoots",
                "Do not consult other reviewers' results",
                "a core claim cannot be assessed", "incomplete",
                "An unanswered design question is a finding",
            ):
                self.assertIn(phrase, flat)
        self.assertEqual(len(set(contracts)), 1, "Shared boundaries drifted between agents")

    def test_consistent_json_result_contract(self):
        normalized_contracts = []
        for name, (_, body) in self.agents.items():
            with self.subTest(reviewer=name):
                contract = body.split("## Result contract\n", 1)[1]
                examples = re.findall(r"```json\n(.*?)\n```", contract, flags=re.DOTALL)
                self.assertEqual(len(examples), 1)
                example = json.loads(examples[0])
                self.assertEqual(set(example), RESULT_KEYS)
                self.assertEqual(example["reviewer"], name)
                self.assertEqual(example["status"], "incomplete")
                self.assertTrue(example["missing_inputs"])
                self.assertEqual(example["findings"], [])
                self.assertEqual(example["reads"], [])
                for key in ("target", "revision", "round", "scope"):
                    self.assertIsNone(example[key])
                normalized_contracts.append(contract.replace(name, "<reviewer>"))
                flat = " ".join(contract.split())
                for phrase in (
                    "Completion is not approval", "never counts as a clean review",
                    "Do not invent tool records", "severity is Blocker, Major, or Nit",
                    "certainty is confirmed or risk", "<reviewer>-<round>-<n>",
                    "never fabricate line numbers",
                ):
                    self.assertIn(phrase, flat)
        self.assertEqual(len(set(normalized_contracts)), 1, "Result contract drifted between agents")

    def test_distinct_review_lenses(self):
        phrases = {
            "goldfish-zoom-out": ("doing nothing", "reuse", "complexity"),
            "goldfish-comprehension": ("Paraphrase", "project-specific", "ordinary engineering terms"),
            "goldfish-design": ("data integrity", "security", "quotas"),
            "goldfish-structure": ("heading hierarchy", "placeholders", "Equivalent headings"),
            "goldfish-style": ("DROP", "CALIBRATE", "RELOCATE"),
            "goldfish-codebase": ("Proposed files", "Create/Modify/Delete", "Do not infer"),
            "goldfish-readiness": ("acceptance criteria", "rollback", "ordinary coding choices"),
        }
        for name, expected in phrases.items():
            lens = " ".join(self.agents[name][1].split("## Review lens\n", 1)[1].split(
                "## Assignment and read boundary\n", 1
            )[0].split())
            for phrase in expected:
                self.assertIn(phrase.lower(), lens.lower(), (name, phrase))

    def test_all_adaptations_have_source_and_change_notices(self):
        notice = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        for name, (_, body) in self.agents.items():
            with self.subTest(reviewer=name):
                self.assertIn("Copyright 2026 Google LLC", body)
                self.assertIn("SPDX-License-Identifier: Apache-2.0", body)
                self.assertIn("Changes:", body)
                self.assertIn(SOURCES[name], body)
                self.assertIn("464db031e7dd1b9a79803ac8ea45f55c7c20c5bc", body)
                self.assertIn(f"opencode/agents/{name}.md", notice)
                self.assertIn(SOURCES[name], notice)


if __name__ == "__main__":
    unittest.main()
