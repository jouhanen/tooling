# SPDX-License-Identifier: Apache-2.0

"""Read-only operator validator for declared Goldfish results, not host evidence.

No model calls, filesystem traversal, writes, or permission changes. Elephant
cannot execute this helper under its default policy; the runtime skills use the
corresponding Markdown checklist. This module has no third-party dependencies.
"""

import argparse
import json
from pathlib import Path, PurePosixPath


REVIEWERS = frozenset({
    "goldfish-zoom-out", "goldfish-comprehension", "goldfish-design",
    "goldfish-structure", "goldfish-style", "goldfish-codebase",
    "goldfish-readiness",
})
ASSIGNMENT_REQUIRED = {
    "Target", "Revision", "Scope", "Round", "Task", "ReadingList", "Standard",
}
ASSIGNMENT_OPTIONAL = {"DiscoveryRoots", "OriginalTarget", "Objective"}
RESULT_KEYS = {
    "reviewer", "status", "target", "revision", "round", "scope", "reads",
    "missing_inputs", "summary", "findings",
}
FINDING_KEYS = {
    "id", "severity", "scope", "evidence", "rationale", "recommendation", "certainty",
}
SEVERITIES = {"Blocker": 0, "Major": 1, "Nit": 2}


class ContractError(ValueError):
    """The declaration does not satisfy the assignment/result contract."""


def require(condition, message):
    if not condition:
        raise ContractError(message)


def nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def normalized_path(value):
    """Lexical POSIX check only: no realpath, symlink, or access verification."""
    require(nonempty_string(value), "Paths must be nonempty strings")
    require(not any(c in value for c in ("\x00", "\n", "\r", "\\")), "Unsupported path characters")
    require(value == "/" or not value.endswith("/"), "Paths must not have a trailing slash except /")
    path = PurePosixPath(value)
    require(".." not in path.parts and path.as_posix() == value, "Paths must be normalized POSIX paths")
    return path


def path_list(value, name):
    require(isinstance(value, list), f"{name} must be an array")
    for item in value:
        normalized_path(item)
    require(len(value) == len(set(value)), f"{name} must not contain duplicates")


def parse_json(text):
    """Reject duplicate keys, wrappers, and non-JSON NaN/Infinity constants."""
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result

    def constant(_):
        raise ContractError("Non-JSON constant")

    try:
        return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    except ContractError:
        raise
    except (ValueError, RecursionError) as error:
        raise ContractError("Invalid JSON document") from error


def validate_assignment(assignment, reviewer):
    require(isinstance(reviewer, str) and reviewer in REVIEWERS, "Unknown reviewer")
    require(isinstance(assignment, dict), "Assignment must be an object")
    require(ASSIGNMENT_REQUIRED <= set(assignment), "Missing required assignment fields")
    require(set(assignment) <= ASSIGNMENT_REQUIRED | ASSIGNMENT_OPTIONAL, "Unknown assignment fields")
    normalized_path(assignment["Target"])
    for key in ("Revision", "Scope"):
        require(nonempty_string(assignment[key]), f"{key} must be a nonempty string")
    require(type(assignment["Round"]) is int and assignment["Round"] > 0, "Round must be a positive integer")
    require(assignment["Task"] in ("concept", "design"), "Task must be concept or design")
    path_list(assignment["ReadingList"], "ReadingList")
    path_list(assignment.get("DiscoveryRoots", []), "DiscoveryRoots")
    if assignment["Standard"] != "none":
        normalized_path(assignment["Standard"])
    if "OriginalTarget" in assignment:
        normalized_path(assignment["OriginalTarget"])
    if "Objective" in assignment:
        require(nonempty_string(assignment["Objective"]), "Objective must be a nonempty string")
    if reviewer == "goldfish-comprehension":
        require(assignment["ReadingList"] == [], "Comprehension ReadingList must be empty")
        require(assignment["Standard"] == "none", "Comprehension Standard must be none")
        require(assignment.get("DiscoveryRoots", []) == [], "Comprehension DiscoveryRoots must be empty")


def validate_result(result, assignment, reviewer):
    """Validate declarations only. Success never proves completion or consent.

    Completed results must declare whole-file coverage for required inputs.
    Extra reads must be within lexically approved DiscoveryRoots. These checks
    cannot detect false declarations, path aliases, symlinks, or missing tool calls.
    """
    validate_assignment(assignment, reviewer)
    require(isinstance(result, dict), "Result must be an object")
    require(set(result) == RESULT_KEYS, "Result fields do not match the contract")
    require(result["reviewer"] == reviewer, "Reviewer identity mismatch")
    require(result["status"] in ("completed", "incomplete"), "Invalid result status")
    completed = result["status"] == "completed"
    for field, source in (("target", "Target"), ("revision", "Revision"), ("scope", "Scope"), ("round", "Round")):
        value = result[field]
        require(value is not None or not completed, f"Completed result needs {field}")
        if value is not None:
            require(type(value) is type(assignment[source]) and value == assignment[source], f"Assignment mismatch: {field}")

    require(nonempty_string(result["summary"]), "Summary must be a nonempty string")
    require(isinstance(result["missing_inputs"], list), "missing_inputs must be an array")
    require(all(nonempty_string(item) for item in result["missing_inputs"]), "Missing-input descriptions must be nonempty strings")
    require(not result["missing_inputs"] if completed else bool(result["missing_inputs"]), "Status and missing_inputs conflict")
    require(isinstance(result["reads"], list), "reads must be an array")
    required_paths = {assignment["Target"], *assignment["ReadingList"]}
    if assignment["Standard"] != "none":
        required_paths.add(assignment["Standard"])
    roots = [PurePosixPath(path) for path in assignment.get("DiscoveryRoots", [])]
    full_reads = set()
    for read in result["reads"]:
        require(isinstance(read, dict) and set(read) == {"path", "coverage"}, "Invalid read entry")
        path = normalized_path(read["path"])
        require(nonempty_string(read["coverage"]), "Read coverage must be a nonempty string")
        require(read["path"] in required_paths or any(path.is_relative_to(root) for root in roots), "Read outside assignment boundary")
        if read["coverage"] == "entire file":
            full_reads.add(read["path"])
    if completed:
        require(required_paths <= full_reads, "Missing entire-file coverage for required inputs")

    require(isinstance(result["findings"], list), "findings must be an array")
    previous_severity = -1
    for number, finding in enumerate(result["findings"], 1):
        require(isinstance(finding, dict), f"Finding {number} must be an object")
        missing = FINDING_KEYS - set(finding)
        unknown = set(finding) - FINDING_KEYS
        require(not missing, f"Finding {number} missing required fields: {', '.join(sorted(missing))}")
        require(not unknown, f"Finding {number} unknown fields: {', '.join(sorted(unknown))}")
        require(all(nonempty_string(value) for value in finding.values()), "Finding fields must be nonempty strings")
        require(finding["id"] == f"{reviewer}-{assignment['Round']}-{number}", "Invalid finding ID sequence")
        require(finding["severity"] in SEVERITIES, "Invalid severity")
        severity = SEVERITIES[finding["severity"]]
        require(severity >= previous_severity, "Findings must be sorted by severity")
        previous_severity = severity
        require(finding["certainty"] in ("confirmed", "risk"), "Invalid certainty")

    if completed and reviewer == "goldfish-comprehension":
        for label in ("What this proposes:", "How the existing system works, per this document:"):
            require(label in result["summary"], "Missing comprehension paraphrase label")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assignment", type=Path, required=True, help="Expected assignment as JSON")
    parser.add_argument("--result", type=Path, required=True, help="Unmodified reviewer result as JSON")
    parser.add_argument("--reviewer", choices=sorted(REVIEWERS), required=True)
    args = parser.parse_args(argv)
    try:
        assignment = parse_json(args.assignment.read_text(encoding="utf-8"))
        result = parse_json(args.result.read_text(encoding="utf-8"))
        validate_result(result, assignment, args.reviewer)
    except (ContractError, OSError, UnicodeError) as error:
        print(f"INVALID: {error}")
        return 1
    print(f"VALID DECLARATION: {args.reviewer}, status={result['status']}")
    print("This does not verify native completion, actual reads, consent, or isolation.")
    return 0 if result["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
