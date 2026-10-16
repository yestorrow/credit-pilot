import json
import tempfile
import unittest
from pathlib import Path

import pilot


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run = pilot.prepare(pilot.ROOT / "examples/abc.json", self.temp.name)
        for order in pilot.read(self.run / "work_orders.json"):
            pilot.write(self.run / order["output"], {
                "role": order["role"],
                "findings": [{"claim": "Debt is USD 54 million.", "evidence_ids": ["F1"]}],
                "missing_inputs": ["Cash flow statement"]})

    def review(self, status="pass"):
        pilot.packet(self.run)
        pilot.write(self.run / "review.json", {"role": "credit_reviewer", "status": status,
                    "summary": "Reviewed.", "packet_sha256": pilot.read(self.run / "review_packet.json")["packet_sha256"],
                    "issues": ["Material error"] if status == "blocked" else []})

    def test_stale_review_rejected(self):
        self.review()
        review = pilot.read(self.run / "review.json")
        review["packet_sha256"] = "stale"
        pilot.write(self.run / "review.json", review)
        with self.assertRaisesRegex(ValueError, "digest"):
            pilot.finalize(self.run)

    def test_missing_or_duplicate_work_orders_rejected(self):
        orders = pilot.read(self.run / "work_orders.json")
        for invalid in ([], orders[:-1], orders + [orders[0]]):
            pilot.write(self.run / "work_orders.json", invalid)
            with self.assertRaisesRegex(ValueError, "coverage"):
                pilot.packet(self.run)

    def test_complete_research_still_withholds_rating(self):
        self.review()
        pilot.finalize(self.run)
        result = pilot.read(self.run / "result.json")
        self.assertEqual(result["status"], "research_complete")
        self.assertIsNone(result["rating"])

    def test_blocked_review_survives_synthesis(self):
        self.review("blocked")
        pilot.finalize(self.run)
        self.assertEqual(pilot.read(self.run / "result.json")["status"], "review_blocked")
        self.assertIn("Material error", (self.run / "memo.md").read_text())

    def test_unknown_evidence_rejected(self):
        path = self.run / "financial_analyst.json"
        data = pilot.read(path)
        data["findings"][0]["evidence_ids"] = ["nonexistent"]
        pilot.write(path, data)
        with self.assertRaisesRegex(ValueError, "Unknown evidence"):
            pilot.packet(self.run)

    def test_changed_analysis_invalidates_review(self):
        self.review()
        path = self.run / "financial_analyst.json"
        data = pilot.read(path)
        data["findings"][0]["claim"] = "Changed after review"
        pilot.write(path, data)
        with self.assertRaisesRegex(ValueError, "Inputs changed"):
            pilot.finalize(self.run)
        with self.assertRaisesRegex(ValueError, "Review already exists"):
            pilot.packet(self.run)

    def test_missing_specialist_blocks_packet(self):
        (self.run / "financial_analyst.json").unlink()
        with self.assertRaises(FileNotFoundError):
            pilot.packet(self.run)

    def test_no_deal_skips_deal_agent(self):
        case = pilot.read(self.run / "case.json")
        case["deal_in_scope"] = False
        source = Path(self.temp.name) / "no-deal.json"
        pilot.write(source, case)
        run = pilot.prepare(source, self.temp.name)
        self.assertEqual(len(pilot.read(run / "work_orders.json")), 2)

    def test_feedback_appends_without_changing_instructions(self):
        path = self.run / "roles/financial_analyst.md"
        before = path.read_text()
        pilot.feedback(self.run, "First observation")
        pilot.feedback(self.run, "Second observation")
        rows = [json.loads(s) for s in (self.run / "feedback.jsonl").read_text().splitlines()]
        self.assertEqual(len(rows), 2)
        self.assertEqual(path.read_text(), before)

    def test_duplicate_evidence_rejected(self):
        case = pilot.read(self.run / "case.json")
        case["evidence"].append(case["evidence"][0])
        with self.assertRaisesRegex(ValueError, "unique"):
            pilot.validate_case(case)


if __name__ == "__main__":
    unittest.main()
