"""Persistent work packets for a Codex-operated multi-agent credit pilot."""
import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def strings(value):
    return isinstance(value, list) and all(isinstance(x, str) and x.strip() for x in value)


def validate_case(case):
    require(isinstance(case, dict), "Case must be an object")
    require(isinstance(case.get("company"), str) and case["company"].strip(), "Company required")
    require(isinstance(case.get("deal_in_scope"), bool), "deal_in_scope must be boolean")
    evidence = case.get("evidence")
    require(isinstance(evidence, list) and evidence, "Evidence required")
    ids = []
    for item in evidence:
        require(isinstance(item, dict), "Evidence must be an object")
        for key in ("id", "source", "text"):
            require(isinstance(item.get(key), str) and item[key].strip(), f"Evidence {key} required")
        ids.append(item["id"])
    require(len(ids) == len(set(ids)), "Evidence IDs must be unique")


def prepare(source, runs):
    case = read(source)
    validate_case(case)
    run = Path(runs) / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8])
    run.mkdir(parents=True)
    write(run / "case.json", case)
    shutil.copytree(ROOT / "roles", run / "roles")
    shutil.copyfile(ROOT / "WORKFLOW.md", run / "WORKFLOW.md")
    roles = ["financial_analyst", "business_analyst"]
    if case["deal_in_scope"]:
        roles.append("deal_structure_analyst")
    write(run / "work_orders.json", [{"role": role, "instructions": f"roles/{role}.md",
          "input": "case.json", "output": f"{role}.json"} for role in roles])
    return run


def analysts(run):
    case = read(run / "case.json")
    validate_case(case)
    ids = {e["id"] for e in case["evidence"]}
    outputs = []
    orders = read(run / "work_orders.json")
    expected = ["financial_analyst", "business_analyst"]
    if case["deal_in_scope"]:
        expected.append("deal_structure_analyst")
    require(isinstance(orders, list) and all(isinstance(o, dict) for o in orders), "Invalid work orders")
    require(sorted(o.get("role", "") for o in orders) == sorted(expected), "Required specialist coverage missing or duplicated")
    for order in orders:
        require(order.get("output") == order["role"] + ".json", "Unexpected output path")
        data = read(run / order["output"])
        require(data.get("role") == order["role"], "Wrong analyst role")
        require(isinstance(data.get("findings"), list), "Findings must be a list")
        require(strings(data.get("missing_inputs")), "Missing inputs must be strings")
        require(data["findings"] or data["missing_inputs"], "Empty analysis")
        for finding in data["findings"]:
            require(isinstance(finding, dict), "Finding must be an object")
            require(isinstance(finding.get("claim"), str) and finding["claim"].strip(), "Claim required")
            refs = finding.get("evidence_ids")
            require(strings(refs) and refs, "Evidence references required")
            require(set(refs) <= ids, "Unknown evidence reference")
        outputs.append(data)
    return {"case": case, "analyses": outputs}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def packet(run):
    require(not (run / "review.json").exists(), "Review already exists; create a new run for revisions")
    value = analysts(run)
    write(run / "review_packet.json", {"packet_sha256": digest(value), "payload": value})
    return run / "review_packet.json"


def finalize(run):
    value = analysts(run)
    saved = read(run / "review_packet.json")
    require(digest(value) == digest(saved["payload"]) == saved["packet_sha256"], "Inputs changed after review packet; create a new run")
    review = read(run / "review.json")
    require(review.get("packet_sha256") == digest(value), "Review does not match packet digest")
    require(review.get("role") == "credit_reviewer", "Wrong reviewer role")
    require(review.get("status") in ("pass", "blocked"), "Invalid review status")
    require(strings(review.get("issues")), "Review issues must be strings")
    require(isinstance(review.get("summary"), str) and review["summary"].strip(), "Review summary required")
    require(review["status"] != "blocked" or review["issues"], "Blocked review must explain issues")
    result = {"company": value["case"]["company"], "status": "review_blocked" if review["status"] == "blocked" else "research_complete",
              "rating": None, "rating_status": "withheld_no_validated_methodology",
              "review": review, "packet_sha256": digest(value), "analyses": value["analyses"]}
    write(run / "result.json", result)
    lines = [f"# {result['company']}", "", f"Status: {result['status']}",
             "", "Rating withheld: no validated rating methodology is implemented.",
             "", "## Independent review", "", review["summary"]]
    lines += [f"- {issue}" for issue in review["issues"]]
    for analysis in value["analyses"]:
        lines += ["", f"## {analysis['role'].replace('_', ' ').title()}", ""]
        lines += [f"- {f['claim']} [{', '.join(f['evidence_ids'])}]" for f in analysis["findings"]]
        lines += ["", "Missing inputs:", ""] + [f"- {s}" for s in analysis["missing_inputs"]]
    lines += ["", "## Evidence", ""]
    lines += [f"- [{e['id']}] {e['source']}: {e['text']}" for e in value["case"]["evidence"]]
    (run / "memo.md").write_text("\n".join(lines) + "\n")
    return run / "memo.md"


def feedback(run, text):
    require((run / "case.json").exists(), "Unknown run")
    require(text.strip(), "Feedback must not be empty")
    with (run / "feedback.jsonl").open("a") as stream:
        stream.write(json.dumps({"at": datetime.now(timezone.utc).isoformat(), "text": text,
                                 "status": "pending_evaluation"}) + "\n")
    return run / "feedback.jsonl"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("case", type=Path)
    p.add_argument("--runs", type=Path, default=ROOT / "runs")
    for command in ("packet", "finalize", "feedback"):
        p = sub.add_parser(command)
        p.add_argument("run", type=Path)
        if command == "feedback":
            p.add_argument("--text", required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = prepare(args.case, args.runs)
        elif args.command == "feedback":
            result = feedback(args.run, args.text)
        else:
            result = {"packet": packet, "finalize": finalize}[args.command](args.run)
        print(result)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(1, f"Cannot complete {args.command}: {exc}\n")


if __name__ == "__main__":
    main()
