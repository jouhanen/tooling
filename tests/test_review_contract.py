"""Negative/positive declaration fixtures; never native execution evidence."""

import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path

from scripts.review_contract import (
    ContractError, FINDING_KEYS, RESULT_KEYS, main, parse_json,
    validate_assignment, validate_result,
)
from test_elephant import REVIEWERS


def assignment():
    return {
        "Target": "docs/designs/example/reviews/round-01-target.md",
        "Revision": "design-r2", "Scope": "full file", "Round": 1,
        "Task": "design", "ReadingList": ["src/service.py"],
        "Standard": "opencode/resources/templates/design.md",
        "DiscoveryRoots": ["src"], "OriginalTarget": "docs/designs/example/design.md",
    }


def result(reviewer="goldfish-design"):
    task = assignment()
    return {
        "reviewer": reviewer, "status": "completed", "target": task["Target"],
        "revision": task["Revision"], "round": task["Round"], "scope": task["Scope"],
        "reads": [{"path": path, "coverage": "entire file"} for path in (
            task["Target"], task["ReadingList"][0], task["Standard"],
        )],
        "missing_inputs": [], "summary": "Assigned scope audited; no issues found.",
        "findings": [],
    }


def finding(reviewer="goldfish-design", number=1, severity="Major"):
    return {
        "id": f"{reviewer}-1-{number}", "severity": severity,
        "scope": "Failures and security", "evidence": "Target leaves retry ownership unspecified.",
        "rationale": "If both components retry, duplicate processing may occur.",
        "recommendation": "Specify retry ownership and idempotency behavior.",
        "certainty": "risk",
    }


class ReviewDeclarationTests(unittest.TestCase):
    def test_completed_declaration_with_or_without_findings(self):
        for findings in ([], [finding()]):
            value = result()
            value["findings"] = findings
            before = copy.deepcopy(value)
            self.assertIs(validate_result(value, assignment(), "goldfish-design"), value)
            self.assertEqual(value, before, "Validation must not repair a result")

    def test_incomplete_is_valid_but_not_a_completed_review(self):
        value = result()
        value.update(status="incomplete", missing_inputs=["source read denied"], reads=[])
        self.assertEqual(validate_result(value, assignment(), "goldfish-design")["status"], "incomplete")
        for key in ("target", "revision", "round", "scope"):
            value[key] = None
        validate_result(value, assignment(), "goldfish-design")

    def test_missing_or_unknown_result_fields(self):
        for key in RESULT_KEYS:
            value = result()
            del value[key]
            with self.subTest(missing=key), self.assertRaises(ContractError):
                validate_result(value, assignment(), "goldfish-design")
        value = result()
        value["approved"] = True
        with self.assertRaises(ContractError):
            validate_result(value, assignment(), "goldfish-design")

    def test_identity_mismatches_even_when_incomplete(self):
        for key, wrong in (
            ("reviewer", "goldfish-style"), ("target", "other.md"),
            ("revision", "design-r1"), ("scope", "other section"),
            ("round", 2), ("round", True), ("round", "1"),
        ):
            for status in ("completed", "incomplete"):
                value = result()
                value[key] = wrong
                value["status"] = status
                value["missing_inputs"] = [] if status == "completed" else ["failed"]
                with self.subTest(key=key, wrong=wrong, status=status), self.assertRaises(ContractError):
                    validate_result(value, assignment(), "goldfish-design")

    def test_wrong_types_and_conflicting_status(self):
        for key, wrong in (
            ("status", "passed"), ("status", []), ("summary", " "),
            ("reads", {}), ("missing_inputs", "none"), ("missing_inputs", [""]),
            ("missing_inputs", ["unread required file"]), ("findings", {}),
            ("round", None), ("target", None), ("revision", None), ("scope", None),
        ):
            value = result()
            value[key] = wrong
            with self.subTest(key=key, wrong=wrong), self.assertRaises(ContractError):
                validate_result(value, assignment(), "goldfish-design")
        value = result()
        value["status"] = "incomplete"
        with self.assertRaises(ContractError):
            validate_result(value, assignment(), "goldfish-design")

    def test_required_whole_file_read_coverage(self):
        for index in range(3):
            value = result()
            value["reads"][index]["coverage"] = "lines 1-10"
            with self.subTest(partial=index), self.assertRaises(ContractError):
                validate_result(value, assignment(), "goldfish-design")
            value["reads"].pop(index)
            with self.subTest(missing=index), self.assertRaises(ContractError):
                validate_result(value, assignment(), "goldfish-design")

    def test_extra_source_reads_bounded_by_directory_not_prefix(self):
        value = result()
        value["reads"].append({"path": "src/extra.py", "coverage": "lines 1-10"})
        validate_result(value, assignment(), "goldfish-design")
        for path in ("src-other/secret.py", "src/../private.md", "reviews/old.md", "/outside/file.md"):
            value["reads"][-1]["path"] = path
            with self.subTest(path=path), self.assertRaises(ContractError):
                validate_result(value, assignment(), "goldfish-design")

    def test_invalid_read_entries(self):
        for entry in (None, {}, {"path": "src/service.py"},
                      {"path": "src/service.py", "coverage": ""},
                      {"path": "src/service.py", "coverage": "entire file", "verified": True}):
            value = result()
            value["reads"].append(entry)
            with self.subTest(entry=entry), self.assertRaises(ContractError):
                validate_result(value, assignment(), "goldfish-design")

    def test_finding_fields_and_enums(self):
        for key in FINDING_KEYS:
            for operation in ("remove", "empty"):
                item = finding()
                if operation == "remove":
                    del item[key]
                else:
                    item[key] = ""
                value = result()
                value["findings"] = [item]
                with self.subTest(key=key, operation=operation), self.assertRaises(ContractError):
                    validate_result(value, assignment(), "goldfish-design")
        for key, wrong in (("severity", "Critical"), ("certainty", "maybe"), ("id", "wrong-1")):
            value = result()
            value["findings"] = [finding() | {key: wrong}]
            with self.subTest(key=key), self.assertRaises(ContractError):
                validate_result(value, assignment(), "goldfish-design")

    def test_finding_ids_order_and_severity_order(self):
        value = result()
        value["findings"] = [finding(number=1, severity="Blocker"), finding(number=2, severity="Nit")]
        validate_result(value, assignment(), "goldfish-design")
        for second in (finding(number=1), finding(number=3)):
            value["findings"] = [finding(), second]
            with self.assertRaises(ContractError):
                validate_result(value, assignment(), "goldfish-design")
        value["findings"] = [finding(severity="Nit"), finding(number=2, severity="Major")]
        with self.assertRaises(ContractError):
            validate_result(value, assignment(), "goldfish-design")

    def test_live_regression_missing_certainty_is_rejected_without_repair(self):
        # Round 02 readiness completed natively, but omitted certainty on both
        # findings. Completion and plausible prose must not make this valid.
        task = assignment() | {"Round": 2}
        reviewer = "goldfish-readiness"
        value = result(reviewer) | {"round": 2}
        value["findings"] = [
            finding(reviewer, number=n) | {"id": f"{reviewer}-2-{n}"}
            for n in (1, 2)
        ]
        for item in value["findings"]:
            del item["certainty"]
        before = copy.deepcopy(value)
        with self.assertRaisesRegex(ContractError, "Finding 1 missing required fields: certainty"):
            validate_result(value, task, reviewer)
        self.assertEqual(value, before)
        # Even a valid first finding cannot mask a malformed second finding.
        value["findings"][0]["certainty"] = "risk"
        before = copy.deepcopy(value)
        with self.assertRaisesRegex(ContractError, "Finding 2 missing required fields: certainty"):
            validate_result(value, task, reviewer)
        self.assertEqual(value, before)

    def test_unknown_finding_field_is_identified_without_repair(self):
        value = result() | {"findings": [finding() | {"approved": True}]}
        before = copy.deepcopy(value)
        with self.assertRaisesRegex(ContractError, "Finding 1 unknown fields: approved"):
            validate_result(value, assignment(), "goldfish-design")
        self.assertEqual(value, before)

    def test_directory_spelling_is_strict_in_all_assignment_paths(self):
        for field in ("Target", "ReadingList", "Standard", "DiscoveryRoots", "OriginalTarget"):
            for path in ("/work/project/", "/work//project", "/work/./project", "/work/../project"):
                task = assignment() | {field: [path] if field in ("ReadingList", "DiscoveryRoots") else path}
                before = copy.deepcopy(task)
                with self.subTest(field=field, path=path), self.assertRaises(ContractError):
                    validate_assignment(task, "goldfish-codebase")
                self.assertEqual(task, before, "Do not normalize sent assignments")
        for root in ("/", "/work/project", "src"):
            with self.subTest(valid_root=root):
                validate_assignment(assignment() | {"DiscoveryRoots": [root]}, "goldfish-codebase")
        value = result()
        value["reads"][0]["path"] += "/"
        with self.assertRaisesRegex(ContractError, "trailing slash"):
            validate_result(value, assignment(), "goldfish-design")

    def test_comprehension_requires_paraphrase_and_only_target(self):
        task = assignment()
        task.update(ReadingList=[], Standard="none", DiscoveryRoots=[])
        value = result("goldfish-comprehension")
        value["reads"] = value["reads"][:1]
        value["summary"] = "What this proposes: A queue. How the existing system works, per this document: Not explained."
        validate_result(value, task, "goldfish-comprehension")
        value["reads"].append({"path": "src/service.py", "coverage": "entire file"})
        with self.assertRaises(ContractError):
            validate_result(value, task, "goldfish-comprehension")
        value["reads"] = value["reads"][:1]
        value["summary"] = "No issues found."
        with self.assertRaises(ContractError):
            validate_result(value, task, "goldfish-comprehension")
        for key, extra in (("ReadingList", ["src/service.py"]), ("Standard", "standard.md"), ("DiscoveryRoots", ["src"])):
            invalid = task | {key: extra}
            with self.subTest(key=key), self.assertRaises(ContractError):
                validate_assignment(invalid, "goldfish-comprehension")

    def test_assignment_validation(self):
        for key in ("Target", "Revision", "Scope", "Round", "Task", "ReadingList", "Standard"):
            task = assignment()
            del task[key]
            with self.subTest(missing=key), self.assertRaises(ContractError):
                validate_assignment(task, "goldfish-design")
        for key, wrong in (
            ("Round", True), ("Round", 0), ("Task", "implementation"),
            ("ReadingList", None), ("ReadingList", ["src/service.py", "src/service.py"]),
            ("Target", "docs/../secret.md"), ("Standard", None),
            ("DiscoveryRoots", "src"), ("Objective", ""), ("unknown", True),
        ):
            with self.subTest(key=key, wrong=wrong), self.assertRaises(ContractError):
                validate_assignment(assignment() | {key: wrong}, "goldfish-design")
        for reviewer in REVIEWERS - {"goldfish-comprehension"}:
            validate_assignment(assignment(), reviewer)

    def test_strict_json_rejects_wrappers_duplicate_keys_and_constants(self):
        self.assertEqual(parse_json('{"status":"completed"}'), {"status": "completed"})
        for text in ('```json\n{}\n```', '{} extra', '{"status":1,"status":2}',
                     '{"nested":{"key":1,"key":2}}', '{"n":NaN}', '{"n":Infinity}'):
            with self.subTest(text=text), self.assertRaises(ContractError):
                parse_json(text)

    def test_cli_is_read_only_and_labels_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task_path, result_path = root / "assignment.json", root / "result.json"
            task_path.write_text(json.dumps(assignment()), encoding="utf-8")
            result_path.write_text(json.dumps(result()), encoding="utf-8")
            before = {p.name: p.read_bytes() for p in root.iterdir()}
            output = io.StringIO()
            args = ["--assignment", str(task_path), "--result", str(result_path), "--reviewer", "goldfish-design"]
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(args), 0)
            self.assertIn("does not verify native completion", output.getvalue())
            self.assertEqual(before, {p.name: p.read_bytes() for p in root.iterdir()})
            incomplete = result() | {"status": "incomplete", "missing_inputs": ["source inaccessible"], "reads": []}
            result_path.write_text(json.dumps(incomplete), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(args), 2)
            result_path.write_text("not JSON", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(args), 1)

    def test_cli_preserves_malformed_live_style_payload_verbatim(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            task_path, result_path = root / "assignment.json", root / "result.json"
            value = result() | {"findings": [finding()]}
            del value["findings"][0]["certainty"]
            task_path.write_text(json.dumps(assignment(), indent=2), encoding="utf-8")
            result_path.write_text(json.dumps(value, indent=4) + "\n", encoding="utf-8")
            before = {p.name: p.read_bytes() for p in root.iterdir()}
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["--assignment", str(task_path), "--result", str(result_path),
                             "--reviewer", "goldfish-design"])
            self.assertEqual(code, 1)
            self.assertIn("missing required fields: certainty", output.getvalue())
            self.assertEqual(before, {p.name: p.read_bytes() for p in root.iterdir()})


if __name__ == "__main__":
    unittest.main()
