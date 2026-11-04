"""Offline workflow wiring/checkpoint contracts, not model-behavior tests."""

import re
import unittest

import yaml

from scripts.review_contract import REVIEWERS as VALIDATOR_REVIEWERS, parse_json, validate_result
from test_elephant import REVIEWERS, ROOT, SKILLS


PACKAGE = ROOT / "opencode"
SOURCES = {
    "egm-brainstorm": ["skills/egm-brainstorm/SKILL.md"],
    "egm-draft": ["skills/egm-draft/SKILL.md"],
    "egm-review": ["skills/egm-review/SKILL.md", "skills/egm-review-loop/SKILL.md"],
    "egm-resolve": ["skills/egm-resolve/SKILL.md"],
}


def markdown(file):
    text = file.read_text(encoding="utf-8")
    _, header, body = text.split("---", 2)
    return yaml.safe_load(header), body


class WorkflowContractTests(unittest.TestCase):
    def test_four_skills_match_elephant_permissions(self):
        files = list((PACKAGE / "skills").glob("*/SKILL.md"))
        self.assertEqual({file.parent.name for file in files}, SKILLS)
        for file in files:
            config, body = markdown(file)
            with self.subTest(skill=file.parent.name):
                self.assertEqual(config["name"], file.parent.name)
                self.assertEqual(config["license"], "Apache-2.0")
                self.assertTrue(config["description"])
                self.assertEqual(config["metadata"], {"opencode/autoinvoke": False})
                self.assertIn("Run only as Elephant", body)
                self.assertIn("../../resources/standards/workflow.md", body)
                self.assertIn("If a required", body)

    def test_commands_load_matching_skills_in_current_elephant_session(self):
        files = list((PACKAGE / "commands").glob("*.md"))
        self.assertEqual({file.stem for file in files}, SKILLS)
        for file in files:
            config, body = markdown(file)
            with self.subTest(command=file.stem):
                self.assertEqual(set(config), {"description", "agent", "subagent"})
                self.assertEqual(config["agent"], "elephant")
                self.assertIs(config["subagent"], False)
                self.assertTrue(config["description"])
                self.assertIn(f"Load the `{file.stem}` skill with the skill tool", body)
                self.assertEqual(body.count("$ARGUMENTS"), 1)
                self.assertNotIn("!`", body, "No shell preprocessing in stored templates")
                self.assertNotRegex(body, r"\$\d+")
                self.assertIn("does not waive approvals or permissions", body)

    def test_skill_resource_links_resolve_within_package(self):
        checked = 0
        for file in (PACKAGE / "skills").glob("*/SKILL.md"):
            _, body = markdown(file)
            for target in re.findall(r"\]\(([^)]+)\)", body):
                path = (file.parent / target).resolve()
                with self.subTest(file=file, target=target):
                    self.assertTrue(path.is_relative_to(PACKAGE))
                    self.assertTrue(path.is_file())
                checked += 1
        self.assertGreaterEqual(checked, 10)

    def test_full_and_focused_presets_use_registered_reviewers_once(self):
        _, body = markdown(PACKAGE / "skills/egm-review/SKILL.md")
        rows = {}
        for line in body.splitlines():
            if line.startswith(("| focused |", "| full |")):
                _, preset, task, stages, _ = line.split("|")
                batches = [re.findall(r"goldfish-[a-z-]+", value) for value in re.findall(r"\[([^]]+)\]", stages)]
                rows[preset.strip(), task.strip()] = batches
        self.assertEqual(rows["focused", "concept"], [["goldfish-zoom-out", "goldfish-design", "goldfish-comprehension"]])
        self.assertEqual(rows["focused", "design"], [["goldfish-design", "goldfish-codebase", "goldfish-readiness"]])
        full = rows["full", "either"]
        self.assertEqual(len(full), 4)
        flattened = [reviewer for stage in full for reviewer in stage]
        self.assertEqual(len(flattened), 7)
        self.assertEqual(set(flattened), REVIEWERS)
        self.assertEqual(set(VALIDATOR_REVIEWERS), REVIEWERS)

    def test_review_has_failure_staleness_and_loop_boundaries(self):
        _, body = markdown(PACKAGE / "skills/egm-review/SKILL.md")
        text = " ".join(body.split())
        for phrase in (
            "Ask for readiness before dispatch and wait",
            "Never reuse a round number", "exact content snapshot",
            "mark the round stale", "Do not change the original target during the round",
            "at most once in a fresh child", "Keep both attempts",
            "No stage in these presets requires an earlier report",
            "The Python reference validator is operator-only",
            "do not automatically dispatch again",
            "two consecutive clean rounds of the same target content",
            "five rounds", "earlier round approval does not authorize the next round",
            "Do not mark old findings verified merely because a later reviewer omitted them",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase.lower(), text.lower())

    def test_drafting_and_resolution_preserve_approval(self):
        _, draft = markdown(PACKAGE / "skills/egm-draft/SKILL.md")
        _, resolve = markdown(PACKAGE / "skills/egm-resolve/SKILL.md")
        for phrase in (
            "obtain approval to start drafting", "Draft one section at a time",
            "End the turn and wait", "List contradictions",
            "do not self-certify independent review", "Do not implement",
        ):
            self.assertIn(phrase.lower(), " ".join(draft.split()).lower())
        for phrase in (
            "is not approval to edit the target", "Do not silently downgrade",
        ):
            # Severity preservation lives in review; edit approval in resolve.
            _, review = markdown(PACKAGE / "skills/egm-review/SKILL.md")
            self.assertIn(phrase.lower(), " ".join((review + resolve).split()).lower())
        for phrase in (
            "Only the user's explicit acceptance settles it",
            'Ambiguous "continue" means no target edits',
            "reread the target", "fixed-unverified, not verified",
            "Do not automatically loop",
        ):
            self.assertIn(phrase.lower(), " ".join(resolve.split()).lower())

    def test_skill_adaptations_record_provenance(self):
        notice = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        for skill, sources in SOURCES.items():
            file = PACKAGE / "skills" / skill / "SKILL.md"
            text = file.read_text(encoding="utf-8")
            self.assertIn("Copyright 2026 Google LLC", text)
            self.assertIn("Changes:", text)
            self.assertIn("464db031e7dd1b9a79803ac8ea45f55c7c20c5bc", text)
            self.assertIn(file.relative_to(ROOT).as_posix(), notice)
            for source in sources:
                self.assertIn(source, text)
                self.assertIn(source, notice)

    def test_result_checklist_and_templates_preserve_raw_evidence(self):
        checklist = (PACKAGE / "resources/standards/result-validation.md").read_text(encoding="utf-8")
        for phrase in ("duplicate keys", "unknown top-level fields", "entire file", "operator", "prompt-driven"):
            self.assertIn(phrase, checklist)
        report = (PACKAGE / "resources/templates/review-round.md").read_text(encoding="utf-8")
        for phrase in ("snapshot", "Native dispatch/completion evidence", "Comprehension paraphrase", "Raw finding IDs"):
            self.assertIn(phrase, report)
        resolution = (PACKAGE / "resources/templates/resolution.md").read_text(encoding="utf-8")
        self.assertIn("no target edits authorized", resolution)
        self.assertIn("outcome.md", resolution)

    def test_embedded_agent_examples_pass_reference_declaration_validation(self):
        for reviewer in REVIEWERS:
            _, body = markdown(PACKAGE / "agents" / f"{reviewer}.md")
            example = re.search(r"```json\n(.*?)\n```", body, flags=re.DOTALL).group(1)
            task = {
                "Target": "docs/designs/example/reviews/round-01-target.md",
                "Revision": "design-r1", "Scope": "full file", "Round": 1,
                "Task": "design", "ReadingList": [], "Standard": "none",
            }
            with self.subTest(reviewer=reviewer):
                result = validate_result(parse_json(example), task, reviewer)
                self.assertEqual(result["status"], "incomplete")


if __name__ == "__main__":
    unittest.main()
