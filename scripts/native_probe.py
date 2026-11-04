# SPDX-License-Identifier: Apache-2.0

"""Opt-in OpenCode V2.2.5 probes using disposable profiles and a scripted model.

No real provider credentials are inherited. Only the loopback fixture provider
is permitted. This is mechanical host verification, not a live EGM workflow test
or an OS/network sandbox. Raw evidence stays in a new private output directory.
"""

import argparse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import platform
import re
import secrets
import signal
import socket
import subprocess
import threading
import time

if __package__:
    from .install import AGENTS, SKILLS, MANIFEST, ROOT, apply_plan, digest, install_plan, json_bytes
else:
    from install import AGENTS, SKILLS, MANIFEST, ROOT, apply_plan, digest, install_plan, json_bytes


VERSION = "2.2.5"
HEADINGS = {
    "goldfish-zoom-out": "# Zoom-out Goldfish",
    "goldfish-comprehension": "# Comprehension Goldfish",
    "goldfish-design": "# Design Goldfish",
    "goldfish-structure": "# Structure Goldfish",
    "goldfish-style": "# Style Goldfish",
    "goldfish-codebase": "# Codebase Goldfish",
    "goldfish-readiness": "# Implementation-readiness Goldfish",
}
DISPATCH_ORDER = ["goldfish-design", "goldfish-design", *sorted(set(HEADINGS) - {"goldfish-design"})]
COMMAND_RESOURCES = {
    "egm-brainstorm": ["standards/workflow.md", "templates/concepts.md"],
    "egm-draft": ["standards/workflow.md", "templates/design.md"],
    "egm-review": ["standards/workflow.md", "standards/goldfish-report.md",
                   "standards/result-validation.md", "templates/review-round.md"],
    "egm-resolve": ["standards/workflow.md", "standards/goldfish-report.md", "templates/resolution.md"],
}


class ProbeError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ProbeError(message)


def save(path, value):
    path.write_bytes(json_bytes(value))


def clean_environment(root, password):
    """Allowlist, not subtraction: no credentials, proxies, or OpenCode overrides."""
    env = {"PATH": os.defpath, "LANG": "C.UTF-8", "NO_COLOR": "1",
           "HOME": str(root / "home"), "TMPDIR": str(root / "tmp"),
           "OPENCODE_PASSWORD": password, "OPENCODE_DISABLE_FREE_MODELS": "1"}
    for key, directory in (
        ("HOME", "home"), ("TMPDIR", "tmp"), ("XDG_CONFIG_HOME", "config"),
        ("XDG_DATA_HOME", "data"), ("XDG_STATE_HOME", "state"),
        ("XDG_CACHE_HOME", "cache"), ("XDG_RUNTIME_DIR", "runtime"),
    ):
        path = root / directory
        path.mkdir(mode=0o700)
        env[key] = str(path)
    return env


def tool_parts(context):
    require(isinstance(context, dict) and isinstance(context.get("data"), list), "Unsupported context schema")
    parts = []
    for message in context["data"]:
        require(isinstance(message, dict), "Malformed native message")
        if message.get("type") != "assistant":
            continue
        require(isinstance(message.get("content"), list), "Malformed assistant content")
        for part in message["content"]:
            require(isinstance(part, dict), "Malformed assistant part")
            if part.get("type") == "tool":
                require(isinstance(part.get("state"), dict) and isinstance(part["state"].get("input"), dict),
                        "Missing native tool input/state")
                parts.append(part)
    return parts


def is_denied(part):
    state = part.get("state", {})
    error = state.get("error", {})
    return (state.get("status") == "error" and isinstance(error, dict)
            and error.get("type") == "permission.rejected")


def require_call(context, name, argument, value, status):
    matches = [part for part in tool_parts(context) if part.get("name") == name
               and part.get("state", {}).get("input", {}).get(argument) == value]
    require(len(matches) == 1, f"Missing/duplicate native call: {name} {argument}")
    part = matches[0]
    require(part["state"].get("status") == status, f"Unexpected native outcome: {name} {argument}")
    if status == "error":
        require(is_denied(part), f"Failure is not permission-denial evidence: {name}")
    if status == "completed":
        require(part["state"].get("content"), f"Completed tool lacks output: {name}")
    return part


def verify_children(parent, context, children):
    require(isinstance(children, list) and all(isinstance(c, dict) for c in children), "Unsupported children schema")
    require(all(isinstance(c.get("id"), str) and re.fullmatch(r"ses_[A-Za-z0-9]+", c["id"]) for c in children),
            "Missing/invalid child identity")
    require(len(children) == len(DISPATCH_ORDER) and len({c.get("id") for c in children}) == len(DISPATCH_ORDER),
            "Expected distinct native children")
    require(sorted(c.get("agent", "") for c in children) == sorted(DISPATCH_ORDER), "Unexpected native child agents")
    require(all(c.get("parentID") == parent and c.get("outcome") == "succeeded" for c in children),
            "Child linkage/completion mismatch")
    by_id = {c["id"]: c for c in children}
    dispatches = [p for p in tool_parts(context) if p.get("name") == "subagent"
                  and p.get("state", {}).get("status") == "completed"]
    require(len(dispatches) == len(DISPATCH_ORDER), "Missing native child completion results")
    require({p["state"].get("metadata", {}).get("sessionID") for p in dispatches} == set(by_id),
            "Parent dispatch results do not match child identities")
    for part in dispatches:
        state = part["state"]
        require(isinstance(state.get("input"), dict) and "sessionID" not in state["input"]
                and not state["input"].get("background"), "Reviewer session reuse/background dispatch requested")
        metadata = state["metadata"]
        require(metadata.get("status") == "completed" and metadata.get("truncated") is False,
                "Incomplete/truncated native child result")
        require(state["input"].get("agent") == by_id[metadata["sessionID"]]["agent"], "Child agent differs from dispatch")
        require(part.get("id") and state.get("content"), "Missing native tool identity/result")
        times = part.get("time", {})
        require(all(isinstance(times.get(k), (int, float)) for k in ("created", "ran", "completed"))
                and times["created"] <= times["ran"] <= times["completed"], "Missing/invalid native completion timing")


class ScriptedModel:
    def __init__(self, project, resources, outside, evidence=None):
        self.project, self.resources, self.outside = project, resources, outside
        self.evidence = evidence
        self.requests, self.errors = [], []
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_POST(self):
                try:
                    require(self.path == "/v1/chat/completions", "Unexpected model endpoint")
                    body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                    delta, finish, role = owner.response(body)
                    owner.requests.append({"role": role, "body": body})
                    chunks = [
                        {"choices": [{"index": 0, "delta": {"role": "assistant", **delta}, "finish_reason": None}]},
                        {"choices": [{"index": 0, "delta": {}, "finish_reason": finish}]},
                    ]
                    payload = "".join("data: " + json.dumps({"id": "chatcmpl-egm-probe", "object": "chat.completion.chunk",
                                                           "created": 1, "model": "scripted", **chunk}) + "\n\n"
                                      for chunk in chunks) + "data: [DONE]\n\n"
                    encoded = payload.encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Content-Length", str(len(encoded)))
                    self.end_headers()
                    self.wfile.write(encoded)
                except Exception as error:
                    owner.errors.append(str(error))
                    self.send_error(500, "Scripted fixture rejected request")

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        if self.evidence is not None:
            save(self.evidence / "scripted-requests.json", self.requests)
            save(self.evidence / "scripted-errors.json", self.errors)

    def configuration(self):
        return {
            "$schema": "https://opencode.ai/config.json", "snapshots": False,
            "model": "probe/scripted", "providers": {"probe": {
                "package": "@opencode/ai/providers/openai-compatible",
                "settings": {"baseURL": f"http://127.0.0.1:{self.server.server_port}/v1",
                             "apiKey": "synthetic-probe-not-a-credential", "encoding": "none"},
                "models": {"scripted": {"capabilities": {"tools": True, "input": ["text"], "output": ["text"]},
                                          "limit": {"context": 128000, "output": 4096}}},
            }},
            "policies": [{"action": "provider.use", "resource": "*", "effect": "deny"},
                         {"action": "provider.use", "resource": "probe", "effect": "allow"}],
        }

    def response(self, body):
        require(len(self.requests) < 150, "Scripted request cap reached")
        require(body.get("model") == "scripted", "Unexpected model reached loopback fixture")
        messages = body.get("messages", [])
        system = "\n".join(str(m.get("content", "")) for m in messages if m.get("role") == "system")
        user = "\n".join(str(m.get("content", "")) for m in messages if m.get("role") == "user")
        step = sum(m.get("role") == "tool" for m in messages)
        if not body.get("tools"):
            return {"content": "Synthetic native probe"}, "stop", "maintenance"
        if "# Elephant" in system:
            command = re.search(r"EGM_PROBE_COMMAND:(egm-[a-z]+)", user)
            if command:
                name = command[1]
                require(name in SKILLS, "Unexpected command skill")
                calls = [("skill", {"id": name})] + [
                    ("read", {"path": str(self.resources / path)}) for path in COMMAND_RESOURCES[name]]
                role = f"command:{name}"
            else:
                require("EGM_PROBE_PARENT" in user, "Unrecognized Elephant request")
                calls = [
                    ("write", {"path": "docs/designs/probe/allowed.md", "content": "Synthetic documentation write\n"}),
                    ("write", {"path": "src/guard.txt", "content": "MUST NOT BE WRITTEN\n"}),
                ]
                calls += [("subagent", {"agent": agent, "description": "Synthetic native boundary probe",
                                       "prompt": self.assignment(number, comprehension=agent == "goldfish-comprehension")})
                          for number, agent in enumerate(DISPATCH_ORDER, 1)]
                calls += [("subagent", {"agent": "general", "description": "Denied synthetic dispatch probe",
                                        "prompt": "No work; this must be denied."})]
                role = "parent"
        else:
            reviewers = [name for name, heading in HEADINGS.items() if heading in system]
            require(len(reviewers) == 1, "Unrecognized agent reached scripted provider")
            role = f"child:{reviewers[0]}"
            calls = [("read", {"path": "docs/designs/probe/target.md"})]
            if reviewers[0] != "goldfish-comprehension":
                calls += [("read", {"path": ".env"}), ("read", {"path": "src/guard.txt"}),
                          ("read", {"path": str(self.resources / "standards/workflow.md")})]
            elif not self.resources.is_relative_to(self.project):
                calls += [("read", {"path": str(self.resources / "standards/workflow.md")})]
            calls += [("read", {"path": str(self.outside)}), ("skill", {"id": "egm-review"})]
        if step >= len(calls):
            return {"content": "SCRIPTED_PROBE_DONE_NOT_A_REVIEW"}, "stop", role
        name, arguments = calls[step]
        return {"tool_calls": [{"index": 0, "id": f"probe_call_{step}", "type": "function",
                                 "function": {"name": name, "arguments": json.dumps(arguments)}}]}, "tool_calls", role

    def assignment(self, number, comprehension=False):
        return json.dumps({
            "Target": str(self.project / "docs/designs/probe/target.md"), "Revision": "design-r1",
            "Scope": "full file", "Round": number, "Task": "design",
            "ReadingList": [] if comprehension else [str(self.project / "src/guard.txt")],
            "Standard": "none" if comprehension else str(self.resources / "standards/workflow.md"),
            "Objective": "Mechanical scripted native probe, not a real review. Forced forbidden calls test host enforcement.",
        })


class PrivateServer:
    def __init__(self, binary, project, env, root):
        self.binary, self.project, self.env, self.root = binary, project, env, root
        self.process = None

    def __enter__(self):
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]
        self.url = f"http://127.0.0.1:{port}"
        self.log = (self.root / "server.log").open("wb")
        self.process = subprocess.Popen([self.binary, "serve", "--hostname", "127.0.0.1", "--port", str(port)],
                                        cwd=self.project, env=self.env, stdout=self.log, stderr=self.log, start_new_session=True)
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                require(self.process.poll() is None, "Private server exited at startup; inspect private server.log")
                try:
                    info = self.api("get", "/api/info", timeout=5)
                    require(info.get("pid") == self.process.pid, "Connected server PID differs from owned private process")
                    require(info.get("version") == VERSION, "Unexpected native server version")
                    return self
                except (ProbeError, subprocess.TimeoutExpired):
                    threading.Event().wait(0.1)
            raise ProbeError("Private server readiness timed out")
        except Exception:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *_):
        if self.process is not None:
            try:
                os.killpg(self.process.pid, signal.SIGTERM)
                self.process.wait(timeout=10)
            except ProcessLookupError:
                pass
            except subprocess.TimeoutExpired:
                os.killpg(self.process.pid, signal.SIGKILL)
                self.process.wait(timeout=10)
        self.log.close()

    def api(self, method, path, body=None, timeout=30):
        command = [self.binary, "api", method, path, "--server", self.url]
        if body is not None:
            command += ["--data", json.dumps(body)]
        response = subprocess.run(command, cwd=self.project, env=self.env, capture_output=True, text=True, timeout=timeout)
        require(response.returncode == 0, f"Private API failed: {method} {path}; private logs retained")
        try:
            return json.loads(response.stdout) if response.stdout.strip() else None
        except ValueError as error:
            raise ProbeError(f"Private API returned non-JSON: {method} {path}") from error

    def session(self, agent, title):
        data = self.api("post", "/api/session", {"agent": agent, "title": title,
                        "model": {"providerID": "probe", "id": "scripted"},
                        "location": {"directory": str(self.project)}})
        return data["data"]["id"]

    def wait(self, session):
        self.api("post", f"/api/experimental/session/{session}/wait", timeout=90)


def run_scope(binary, root, scope):
    project = root / "project"
    project.mkdir()
    env = clean_environment(root, secrets.token_urlsafe(24))
    target = project / ".opencode" if scope == "project" else Path(env["XDG_CONFIG_HOME"]) / "opencode"
    apply_plan(install_plan(target, scope=scope))
    (project / "src").mkdir()
    (project / "src/guard.txt").write_text("UNCHANGED_GUARD\n")
    (project / "docs/designs/probe").mkdir(parents=True)
    (project / "docs/designs/probe/target.md").write_text("# Synthetic design\n\nRevision: design-r1\n\nA private mechanical probe fixture.\nNATIVE_PROBE_TARGET_END\n")
    parent_marker, project_marker, secret_marker = (secrets.token_hex(20) for _ in range(3))
    (project / "AGENTS.md").write_text(f"Project instruction marker: {project_marker}\n")
    (project / ".env").write_text(f"SYNTHETIC_SECRET={secret_marker}\n")
    outside = root / "outside-reference.md"
    outside.write_text("Synthetic external reference; read must be denied.\n")
    with ScriptedModel(project, target / "resources", outside, evidence=root) as model:
        save(project / "opencode.json", model.configuration())
        with PrivateServer(binary, project, env, root) as server:
            agents = server.api("get", "/api/agent")["data"]
            commands = server.api("get", "/api/command")["data"]
            skills = server.api("get", "/api/skill")["data"]
            models = server.api("get", "/api/model")["data"]
            configs = server.api("get", "/api/config")
            require({(m.get("providerID"), m.get("id")) for m in models if m.get("enabled")} == {("probe", "scripted")},
                    "Unexpected enabled provider/model; refuse model calls")
            require(AGENTS <= {a["id"] for a in agents}, "Native agent discovery incomplete")
            require({"build", "plan"} <= {a["id"] for a in agents}, "Built-in Build/Plan discovery changed")
            for agent in agents:
                if agent["id"] in AGENTS:
                    require(agent.get("mode") == ("primary" if agent["id"] == "elephant" else "subagent")
                            and agent.get("hidden") is False, "Native custom-agent mode/visibility mismatch")
            require(SKILLS <= {c["name"] for c in commands}, "Native command discovery incomplete")
            require(SKILLS <= {s["id"] for s in skills}, "Native skill discovery incomplete")
            require(all(Path(s["path"]).is_relative_to(target) and s.get("autoinvoke") is False
                        for s in skills if s["id"] in SKILLS), "Wrong skill source or autoinvoke setting")
            require(all(not c.get("path") or Path(c["path"]).is_relative_to(root)
                        for c in configs if c.get("type") == "document"), "Ambient configuration document found; refuse model calls")
            save(root / "discovery.json", {"agents": agents, "commands": commands, "skills": skills,
                                          "enabled_models": [{"providerID": m["providerID"], "id": m["id"]} for m in models if m.get("enabled")],
                                          "config_sources": [{"type": c["type"], "path": c.get("path")} for c in configs]})
            parent = server.session("elephant", "Synthetic delegation probe")
            server.api("post", f"/api/session/{parent}/prompt", {"text": f"EGM_PROBE_PARENT. Parent-only marker: {parent_marker}"})
            server.wait(parent)
            parent_info = server.api("get", f"/api/session/{parent}")["data"]
            save(root / "parent.json", parent_info)
            require(parent_info.get("agent") == "elephant" and parent_info.get("outcome") == "succeeded", "Parent execution did not complete")
            context = server.api("get", f"/api/session/{parent}/context")
            save(root / "parent-context.json", context)
            children = server.api("get", f"/api/session?parentID={parent}")["data"]
            save(root / "children.json", children)
            verify_children(parent, context, children)
            require_call(context, "write", "path", "docs/designs/probe/allowed.md", "completed")
            require_call(context, "write", "path", "src/guard.txt", "error")
            require_call(context, "subagent", "agent", "general", "error")
            for child in children:
                require(child.get("parentID") == parent and child.get("outcome") == "succeeded", "Child linkage/completion mismatch")
                child_context = server.api("get", f"/api/session/{child['id']}/context")
                save(root / f"{child['id']}-context.json", child_context)
                read = require_call(child_context, "read", "path", "docs/designs/probe/target.md", "completed")
                require(read["state"].get("metadata", {}).get("truncated") is False
                        and "NATIVE_PROBE_TARGET_END" in json.dumps(read["state"]["content"]), "Target read truncated or incomplete")
                require_call(child_context, "read", "path", str(outside), "error")
                require_call(child_context, "skill", "id", "egm-review", "error")
                if child["agent"] != "goldfish-comprehension":
                    require_call(child_context, "read", "path", ".env", "error")
                    require_call(child_context, "read", "path", "src/guard.txt", "completed")
                    require_call(child_context, "read", "path", str(target / "resources/standards/workflow.md"), "completed")
                elif scope == "global":
                    require_call(child_context, "read", "path", str(target / "resources/standards/workflow.md"), "error")
            for skill in sorted(SKILLS):
                session = server.session("build", f"Synthetic command probe {skill}")
                server.api("post", f"/api/session/{session}/command", {"name": skill, "text": f"EGM_PROBE_COMMAND:{skill}"})
                server.wait(session)
                command_context = server.api("get", f"/api/session/{session}/context")
                save(root / f"{skill}-context.json", command_context)
                info = server.api("get", f"/api/session/{session}")["data"]
                require(info.get("agent") == "elephant" and info.get("outcome") == "succeeded", "Command did not select/complete as Elephant")
                loaded = require_call(command_context, "skill", "id", skill, "completed")
                require(str(target / "skills" / skill) in json.dumps(loaded["state"]["content"]), "Loaded skill base directory mismatch")
                for relative in COMMAND_RESOURCES[skill]:
                    require_call(command_context, "read", "path", str(target / "resources" / relative), "completed")
        require(not model.errors, "Scripted model rejected requests")
        child_requests = [r["body"] for r in model.requests if r["role"].startswith("child:")]
        require(child_requests, "No captured child model requests")
        require(all(parent_marker not in json.dumps(b) for b in child_requests), "Parent marker leaked into child request")
        require(all(project_marker in json.dumps(b) for b in child_requests), "Expected inherited project instruction marker absent")
        require(all(secret_marker not in json.dumps(r["body"]) for r in model.requests), "Denied .env contents reached model")
        require(all({t["function"]["name"] for t in b.get("tools", [])} <= {"read", "glob", "skill"} for b in child_requests),
                "Goldfish model received unexpected tools")
        require((project / "src/guard.txt").read_text() == "UNCHANGED_GUARD\n", "Forbidden source write occurred")
        require((project / "docs/designs/probe/allowed.md").read_text() == "Synthetic documentation write\n", "Allowed documentation write missing")
    manifest = json.loads((target / MANIFEST).read_text())
    require(all(digest((target / p).read_bytes()) == sha for p, sha in manifest["files"].items()), "Installed package mutated during probe")
    return {"scope": scope, "installation_discovery": "passed", "scripted_dispatch_permissions": "passed",
            "parent_marker_absent_from_captured_child_requests": True, "project_instructions_inherited": True,
            "general_context_isolation": "unverified", "live_workflow": "not run",
            "paid_model_calls": 0, "scripted_requests": len(model.requests), "native_children": len(DISPATCH_ORDER),
            "tested_reviewers": sorted(HEADINGS), "source_digest": manifest["source_digest"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--opencode", type=Path, required=True, help="Installed V2.2.5 executable")
    parser.add_argument("--output", type=Path, required=True, help="New private evidence directory, preferably under /tmp/opencode")
    parser.add_argument("--scope", choices=("project", "global", "both"), default="both")
    args = parser.parse_args(argv)
    output = args.output.expanduser().absolute()
    require(not output.exists() and not output.is_symlink(), "Output must not already exist")
    require(args.opencode.is_file() and os.access(args.opencode, os.X_OK), "OpenCode executable is unavailable")
    binary = str(args.opencode.resolve())
    version = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=10)
    require(version.returncode == 0 and version.stdout.strip() == f"opencode v{VERSION}", "Probe requires exact OpenCode V2.2.5")
    output.mkdir(mode=0o700, parents=True)
    summary = {"date_utc": datetime.now(timezone.utc).isoformat(), "host_version": VERSION,
               "probe_sha256": digest(Path(__file__).read_bytes()), "scopes": [], "status": "incomplete",
               "platform": {"system": platform.system(), "release": platform.release(), "machine": platform.machine()},
               "live_workflow": "not run", "human_approval_pause": "not tested by scripted probe",
               "network_sandbox": "not provided", "requested_scope": args.scope}
    git_env = {"PATH": os.defpath, "HOME": str(output), "LANG": "C.UTF-8"}
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], env=git_env,
                            capture_output=True, text=True, timeout=10)
    dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"], env=git_env,
                           capture_output=True, text=True, timeout=10)
    summary["base_commit"] = commit.stdout.strip() if commit.returncode == 0 else None
    summary["worktree_dirty"] = bool(dirty.stdout) if dirty.returncode == 0 else None
    try:
        for scope in (("project", "global") if args.scope == "both" else (args.scope,)):
            root = output / scope
            root.mkdir(mode=0o700)
            summary["scopes"].append(run_scope(binary, root, scope))
        summary["status"] = "passed"
    except (ProbeError, OSError, subprocess.TimeoutExpired, ValueError, KeyError) as error:
        summary["error"] = str(error)
    save(output / "summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    try:
        code = main()
    except (ProbeError, OSError, subprocess.TimeoutExpired) as error:
        print(f"REFUSED: {error}")
        code = 1
    raise SystemExit(code)
