"""Fixture-only probe regression tests; ordinary tests never invoke OpenCode."""

import copy
import json
import os
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

from scripts.native_probe import (
    COMMAND_RESOURCES, DISPATCH_ORDER, HEADINGS, ProbeError, ScriptedModel, clean_environment,
    is_denied, require_call, tool_parts, verify_children,
)
from test_elephant import REVIEWERS, ROOT


def tool(name, arguments, status="completed"):
    state = {"input": arguments, "status": status}
    if status == "completed":
        state["content"] = [{"type": "text", "text": "Synthetic output"}]
    else:
        state["error"] = {"type": "permission.rejected", "message": "Permission denied"}
    return {"type": "tool", "id": "fixture_call", "name": name, "state": state,
            "time": {"created": 1, "ran": 2, "completed": 3}}


def context(*parts):
    return {"data": [{"id": "msg_fixture", "type": "assistant", "content": list(parts)}]}


def children_fixture():
    children, parts = [], []
    for index, reviewer in enumerate(DISPATCH_ORDER):
        session = f"ses_fixture{index}"
        children.append({"id": session, "parentID": "ses_parent", "agent": reviewer, "outcome": "succeeded"})
        part = tool("subagent", {"agent": reviewer, "description": "Fixture", "prompt": "{}"})
        part["state"]["metadata"] = {"sessionID": session, "status": "completed", "truncated": False}
        parts.append(part)
    return context(*parts), children


class NativeEvidenceTests(unittest.TestCase):
    def test_exact_permission_rejection_not_arbitrary_error(self):
        denied = tool("read", {"path": ".env"}, "error")
        self.assertTrue(is_denied(denied))
        require_call(context(denied), "read", "path", ".env", "error")
        for error in ({"type": "file.notfound", "message": "Denied-looking text"},
                      {"type": "unknown.tool", "message": "Permission denied"}):
            invalid = copy.deepcopy(denied)
            invalid["state"]["error"] = error
            self.assertFalse(is_denied(invalid))
            with self.assertRaises(ProbeError):
                require_call(context(invalid), "read", "path", ".env", "error")

    def test_missing_duplicate_failed_or_empty_read_cannot_pass(self):
        good = tool("read", {"path": "target.md"})
        require_call(context(good), "read", "path", "target.md", "completed")
        for evidence in (context(), context(good, good), context(tool("read", {"path": "target.md"}, "error"))):
            with self.assertRaises(ProbeError):
                require_call(evidence, "read", "path", "target.md", "completed")
        good["state"]["content"] = []
        with self.assertRaises(ProbeError):
            require_call(context(good), "read", "path", "target.md", "completed")

    def test_malformed_native_context_fails_closed(self):
        for value in ([], {}, {"data": None}, {"data": [None]},
                      {"data": [{"type": "assistant", "content": {}}]}, context(None),
                      context({"type": "tool", "state": {}})):
            with self.subTest(value=value), self.assertRaises(ProbeError):
                tool_parts(value)

    def test_native_linkage_and_fresh_children(self):
        evidence, children = children_fixture()
        verify_children("ses_parent", evidence, children)
        self.assertEqual(set(DISPATCH_ORDER), REVIEWERS)
        self.assertEqual(set(HEADINGS), REVIEWERS)
        self.assertEqual(DISPATCH_ORDER.count("goldfish-design"), 2)

    def test_missing_start_completion_and_wrong_agent_fail(self):
        for mutation in ("missing_child", "missing_result", "wrong_parent", "failed_child", "duplicate_id",
                         "missing_id", "wrong_agent", "wrong_result_child", "truncated", "reused", "background", "missing_timing"):
            evidence, children = children_fixture()
            part = evidence["data"][0]["content"][0]
            if mutation == "missing_child":
                children.pop()
            elif mutation == "missing_result":
                evidence["data"][0]["content"].pop()
            elif mutation == "wrong_parent":
                children[0]["parentID"] = "ses_unrelated"
            elif mutation == "failed_child":
                children[0]["outcome"] = "failed"
            elif mutation == "duplicate_id":
                children[0]["id"] = children[1]["id"]
            elif mutation == "missing_id":
                del children[0]["id"]
            elif mutation == "wrong_agent":
                children[0]["agent"] = "general"
            elif mutation == "wrong_result_child":
                part["state"]["metadata"]["sessionID"] = "ses_wrong"
            elif mutation == "truncated":
                part["state"]["metadata"]["truncated"] = True
            elif mutation == "reused":
                part["state"]["input"]["sessionID"] = children[0]["id"]
            elif mutation == "background":
                part["state"]["input"]["background"] = True
            elif mutation == "missing_timing":
                del part["time"]["completed"]
            with self.subTest(mutation=mutation), self.assertRaises(ProbeError):
                verify_children("ses_parent", evidence, children)

    def test_clean_profile_environment_does_not_inherit_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inherited = {"OPENAI_API_KEY": "synthetic-secret", "OPENCODE_CONFIG": "wrong.json",
                         "OPENCODE_SERVER": "http://wrong.test", "HTTP_PROXY": "http://wrong.test",
                         "GITHUB_TOKEN": "synthetic-secret"}
            with patch.dict(os.environ, inherited):
                env = clean_environment(root, "synthetic-private-password")
            self.assertFalse(set(inherited) & set(env))
            self.assertEqual(env["PATH"], os.defpath)
            self.assertEqual(env["OPENCODE_DISABLE_FREE_MODELS"], "1")
            for key in ("HOME", "TMPDIR", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME", "XDG_RUNTIME_DIR"):
                self.assertTrue(Path(env[key]).is_relative_to(root))
                self.assertTrue(Path(env[key]).is_dir())


class ScriptedModelFixtureTests(unittest.TestCase):
    def setUp(self):
        self.model = ScriptedModel(Path("/fixture/project"), Path("/fixture/resources"), Path("/fixture/outside.md"))
        self.addCleanup(self.model.server.server_close)

    def body(self, system, user="", step=0):
        return {"model": "scripted", "tools": [{"function": {"name": "read"}}],
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]
                + [{"role": "tool", "content": "fixture output"}] * step}

    def test_provider_policy_allows_only_loopback_fixture(self):
        config = self.model.configuration()
        self.assertEqual(config["policies"], [
            {"action": "provider.use", "resource": "*", "effect": "deny"},
            {"action": "provider.use", "resource": "probe", "effect": "allow"},
        ])
        self.assertEqual(set(config["providers"]), {"probe"})
        self.assertTrue(config["providers"]["probe"]["settings"]["baseURL"].startswith("http://127.0.0.1:"))

    def test_command_probe_resources_match_authored_skill_links(self):
        for skill, resources in COMMAND_RESOURCES.items():
            body = (ROOT / "opencode/skills" / skill / "SKILL.md").read_text()
            linked = re.findall(r"\]\(../../resources/([^)]+)\)", body)
            self.assertEqual(linked, resources)

    def test_parent_dispatch_never_includes_parent_history_or_session_reuse(self):
        for number, reviewer in enumerate(DISPATCH_ORDER, 2):
            delta, finish, role = self.model.response(self.body("# Elephant", "EGM_PROBE_PARENT secret-parent-marker", number))
            call = delta["tool_calls"][0]["function"]
            args = json.loads(call["arguments"])
            self.assertEqual(call["name"], "subagent")
            self.assertEqual(args["agent"], reviewer)
            self.assertNotIn("secret-parent-marker", args["prompt"])
            self.assertNotIn("sessionID", args)
            self.assertEqual(finish, "tool_calls")
            self.assertEqual(role, "parent")

    def test_every_reviewer_has_a_bounded_mechanical_script(self):
        for reviewer, heading in HEADINGS.items():
            delta, _, role = self.model.response(self.body(heading))
            self.assertEqual(role, f"child:{reviewer}")
            self.assertEqual(delta["tool_calls"][0]["function"]["name"], "read")
            done, finish, _ = self.model.response(self.body(heading, step=20))
            self.assertEqual(finish, "stop")
            self.assertIn("NOT_A_REVIEW", done["content"])

    def test_comprehension_assignment_has_no_extra_inputs(self):
        value = json.loads(self.model.assignment(3, comprehension=True))
        self.assertEqual(value["ReadingList"], [])
        self.assertEqual(value["Standard"], "none")

    def test_unknown_requests_and_models_are_rejected(self):
        for body in (self.body("Unknown agent"), self.body("# Elephant", "unrecognized"),
                     self.body("# Elephant", "EGM_PROBE_PARENT") | {"model": "real-provider"}):
            with self.assertRaises(ProbeError):
                self.model.response(body)


if __name__ == "__main__":
    unittest.main()
