"""Local web inbox and result bridge for the Codex-operated Credit Lead.

This process never calls a model. The Credit Lead in chat claims inbox jobs,
delegates the work orders, and publishes reviewed results using this CLI.
"""
import argparse
import fcntl
import json
import re
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from uuid import uuid4

import pilot

WEB = pilot.ROOT.parent / "web"
DEFAULT_DATA = pilot.ROOT / "desk-data"
ROLES = ("financial_analyst", "business_analyst", "deal_structure_analyst", "credit_reviewer")
LOCK = threading.RLock()


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    """Readers see either the old or the new complete artifact."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def checked_id(value):
    pilot.require(isinstance(value, str) and re.fullmatch(r"[a-zA-Z0-9-]{1,80}", value), "Invalid ID")
    return value


class Desk:
    def __init__(self, root=DEFAULT_DATA):
        self.root = Path(root).resolve()
        self.jobs = self.root / "jobs"
        self.jobs.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def locked(self):
        # Coordinate both HTTP threads and separate operator CLI processes.
        with LOCK, (self.root / "desk.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def path(self, job_id):
        return self.jobs / (checked_id(job_id) + ".json")

    def read(self, job_id):
        return pilot.read(self.path(job_id))

    def submit(self, value):
        pilot.require(isinstance(value, dict), "Request must be an object")
        text = value.get("message", "")
        pilot.require(isinstance(text, str) and 0 < len(text.strip()) <= 12000, "A message of 1–12000 characters is required")
        kind = value.get("kind", "analysis")
        pilot.require(kind in ("analysis", "question"), "Unknown request kind")
        parent_id = value.get("parent_id")
        parent = self.read(parent_id) if parent_id else None
        pilot.require(parent is not None or kind == "analysis", "Questions need a case")
        if parent:
            pilot.require(parent["kind"] == "analysis", "Select an analysis case")
            case = parent["case"]
        else:
            case = value.get("case")
            pilot.validate_case(case)
        mode = value.get("mode", parent["mode"] if parent else "light")
        pilot.require(mode in ("light", "standard"), "Unknown analysis mode")
        job = {"id": uuid4().hex, "kind": kind, "parent_id": parent_id,
               "case": case, "mode": mode, "message": text.strip(),
               "status": "queued", "created_at": now(), "run_id": None,
               "reply": None, "error": None}
        with self.locked():
            save(self.path(job["id"]), job)
        return job

    def run_path(self, job):
        return self.root / "runs" / checked_id(job["run_id"])

    def prepare(self, job_id):
        with self.locked():
            job = self.read(job_id)
            pilot.require(job["status"] == "queued", "Job is already claimed; resume its existing run")
            if job["kind"] == "analysis":
                # Include the user's actual instruction in the immutable input snapshot.
                source = self.root / "inputs" / (job_id + ".json")
                case = {**job["case"], "request": job["message"], "analysis_mode": job["mode"]}
                if job["parent_id"]:
                    case["prior_job_id"] = job["parent_id"]
                save(source, case)
                run = pilot.prepare(source, self.root / "runs")
                job["run_id"] = run.name
                # These are routing defaults, not claims that a model has run.
                save(run / "execution.json", {"mode": "codex_chat", "agents": [],
                     "depth": job["mode"], "note": "Record actual model choices as agents are delegated."})
            job["status"] = "working"
            save(self.path(job_id), job)
        return job

    def respond(self, job_id, text):
        pilot.require(isinstance(text, str) and text.strip(), "Reply is required")
        with self.locked():
            job = self.read(job_id)
            pilot.require(job["kind"] == "question" and job["status"] == "working", "Claim a question before replying")
            job.update(status="answered", reply=text.strip(), completed_at=now())
            save(self.path(job_id), job)
        return job

    def publish(self, job_id, summary):
        pilot.require(isinstance(summary, dict), "Lead summary must be an object")
        pilot.require(summary.get("role") == "credit_lead", "Credit Lead summary required")
        pilot.require(isinstance(summary.get("summary"), str) and summary["summary"].strip(), "Summary text required")
        pilot.require(pilot.strings(summary.get("open_questions")), "Open questions must be strings")
        with self.locked():
            job = self.read(job_id)
            pilot.require(job["kind"] == "analysis" and job["status"] == "working", "Analysis is not in progress")
            run = self.run_path(job)
            # Revalidate the specialists and review digest, even if result.json exists.
            pilot.finalize(run)
            result = pilot.read(run / "result.json")
            pilot.require(summary.get("packet_sha256") == result["packet_sha256"], "Lead summary must match the reviewed packet")
            save(run / "lead_summary.json", summary)
            job.update(status=result["status"], completed_at=now())
            save(self.path(job_id), job)
        return job

    def fail(self, job_id, message):
        pilot.require(isinstance(message, str) and message.strip(), "Explain the failure")
        with self.locked():
            job = self.read(job_id)
            pilot.require(job["status"] in ("queued", "working"), "Job is already finished")
            job.update(status="failed", error=message.strip())
            save(self.path(job_id), job)
        return job

    def detail(self, job_id):
        job = self.read(job_id)
        data = {**job, "analyses": {}, "review": None, "lead": None, "result": None,
                "artifact_errors": [], "work_orders": []}
        if not job["run_id"]:
            return data
        run = self.run_path(job)
        data["work_orders"] = pilot.read(run / "work_orders.json")
        for role in ROLES:
            path = run / ("review.json" if role == "credit_reviewer" else role + ".json")
            if path.exists():
                try:
                    artifact = pilot.read(path)
                    pilot.require(isinstance(artifact, dict) and artifact.get("role") == role, "Invalid role artifact")
                    if role == "credit_reviewer":
                        data["review"] = artifact
                    else:
                        data["analyses"][role] = artifact
                except (ValueError, TypeError) as exc:
                    data["artifact_errors"].append(f"{role}: {exc}")
        # Never display a previously published verdict after its evidence has changed.
        if job["status"] in ("research_complete", "review_blocked"):
            try:
                value = pilot.analysts(run)
                result = pilot.read(run / "result.json")
                review = pilot.read(run / "review.json")
                lead = pilot.read(run / "lead_summary.json")
                saved = pilot.read(run / "review_packet.json")
                digest = pilot.digest(value)
                pilot.require(digest == result["packet_sha256"] == review["packet_sha256"] == lead["packet_sha256"] == saved["packet_sha256"] == pilot.digest(saved["payload"]), "Artifacts changed after review; create a new run")
                pilot.require(result["review"] == review, "Review changed after publication; create a new run")
                data.update(result=result, lead=lead)
            except (ValueError, OSError, KeyError, TypeError) as exc:
                data["status"] = "invalidated"
                data["artifact_errors"].append(str(exc))
        return data

    def list(self):
        rows = [pilot.read(path) for path in self.jobs.glob("*.json")]
        return sorted(rows, key=lambda row: row["created_at"], reverse=True)


def handler(desk):
    class Handler(BaseHTTPRequestHandler):
        def send(self, status, value, content_type="application/json; charset=utf-8"):
            data = json.dumps(value).encode() if content_type.startswith("application/json") else value
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            try:
                if path == "/api/status":
                    return self.send(200, {"mode": "codex_chat", "automatic_dispatch": False,
                        "roles": list(ROLES), "rating_available": False})
                if path == "/api/jobs":
                    return self.send(200, desk.list())
                if path.startswith("/api/jobs/"):
                    return self.send(200, desk.detail(path.removeprefix("/api/jobs/")))
                assets = {"/": ("index.html", "text/html; charset=utf-8"),
                          "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                          "/styles.css": ("styles.css", "text/css; charset=utf-8")}
                if path in assets:
                    name, mime = assets[path]
                    return self.send(200, (WEB / name).read_bytes(), mime)
                self.send(404, {"error": "Not found"})
            except (ValueError, KeyError, TypeError) as exc:
                self.send(400, {"error": str(exc)})
            except FileNotFoundError:
                self.send(404, {"error": "Unknown job or missing artifact"})

        def do_POST(self):
            # Only same-origin JSON writes; no arbitrary files or paths are accepted.
            if self.path != "/api/jobs":
                return self.send(404, {"error": "Not found"})
            if not self.headers.get("Content-Type", "").startswith("application/json"):
                return self.send(415, {"error": "JSON required"})
            origin = self.headers.get("Origin")
            if origin and origin not in ("http://" + self.headers.get("Host", ""), "https://" + self.headers.get("Host", "")):
                return self.send(403, {"error": "Cross-origin writes are not allowed"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                pilot.require(0 < length <= 1000000, "Request must be between 1 byte and 1 MB")
                value = json.loads(self.rfile.read(length))
                self.send(201, desk.submit(value))
            except (ValueError, KeyError, TypeError, FileNotFoundError) as exc:
                self.send(400, {"error": str(exc)})

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    sub = parser.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--host", default="127.0.0.1")
    sub.add_parser("inbox")
    submit = sub.add_parser("submit")
    submit.add_argument("file", type=Path)
    for name in ("prepare", "show", "respond", "publish", "fail"):
        command = sub.add_parser(name)
        command.add_argument("job_id")
        if name in ("respond", "publish"):
            command.add_argument("file", type=Path)
        if name == "fail":
            command.add_argument("message")
    args = parser.parse_args()
    desk = Desk(args.data)
    try:
        if args.command == "serve":
            server = ThreadingHTTPServer((args.host, args.port), handler(desk))
            print(f"Credit Pilot: http://{args.host}:{args.port} — Codex chat operates the inbox", flush=True)
            server.serve_forever()
        elif args.command == "submit":
            print(json.dumps(desk.submit(pilot.read(args.file)), indent=2))
        elif args.command == "inbox":
            print(json.dumps([j for j in desk.list() if j["status"] in ("queued", "working")], indent=2))
        elif args.command == "prepare":
            print(json.dumps(desk.prepare(args.job_id), indent=2))
        elif args.command == "show":
            print(json.dumps(desk.detail(args.job_id), indent=2))
        elif args.command == "respond":
            print(json.dumps(desk.respond(args.job_id, args.file.read_text()), indent=2))
        elif args.command == "publish":
            print(json.dumps(desk.publish(args.job_id, pilot.read(args.file)), indent=2))
        else:
            print(json.dumps(desk.fail(args.job_id, args.message), indent=2))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(1, f"Cannot complete {args.command}: {exc}\n")


if __name__ == "__main__":
    main()
