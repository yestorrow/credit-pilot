import tempfile
import unittest

import desk
import pilot


class DeskTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.desk = desk.Desk(self.temp.name)
        self.case = pilot.read(pilot.ROOT / "examples/abc.json")
        self.job = self.desk.submit({"case": self.case, "mode": "light",
                                     "message": "Do a very light fictional analysis."})

    def fill(self, blocked=False):
        claimed = self.desk.prepare(self.job["id"])
        run = self.desk.run_path(claimed)
        for order in pilot.read(run / "work_orders.json"):
            pilot.write(run / order["output"], {"role": order["role"],
                "findings": [{"claim": "Synthetic debt is USD 54m.", "evidence_ids": ["F1"]}],
                "missing_inputs": ["Cash flow statement"]})
        pilot.packet(run)
        digest = pilot.read(run / "review_packet.json")["packet_sha256"]
        pilot.write(run / "review.json", {"role": "credit_reviewer", "packet_sha256": digest,
            "status": "blocked" if blocked else "pass", "issues": ["Check debt"] if blocked else [],
            "summary": "Fixture review"})
        return run, {"role": "credit_lead", "packet_sha256": digest,
                     "summary": "Fixture synthesis", "open_questions": ["Cash flow?"]}

    def test_submission_persists_and_snapshots_instructions(self):
        fresh = desk.Desk(self.temp.name)
        self.assertEqual(fresh.read(self.job["id"])["status"], "queued")
        claimed = fresh.prepare(self.job["id"])
        source = pilot.read(fresh.run_path(claimed) / "case.json")
        self.assertEqual(source["analysis_mode"], "light")
        self.assertEqual(source["request"], self.job["message"])
        self.assertEqual(len(pilot.read(fresh.run_path(claimed) / "work_orders.json")), 3)
        with self.assertRaisesRegex(ValueError, "already claimed"):
            fresh.prepare(self.job["id"])

    def test_results_visible_separately_before_publication(self):
        self.fill()
        value = self.desk.detail(self.job["id"])
        self.assertEqual(len(value["analyses"]), 3)
        self.assertEqual(value["review"]["role"], "credit_reviewer")
        self.assertIsNone(value["result"])
        self.assertIsNone(value["lead"])

    def test_publication_requires_review_and_matching_synthesis(self):
        run, summary = self.fill()
        changed = {**summary, "packet_sha256": "wrong"}
        with self.assertRaisesRegex(ValueError, "must match"):
            self.desk.publish(self.job["id"], changed)
        (run / "review.json").unlink()
        with self.assertRaises(FileNotFoundError):
            self.desk.publish(self.job["id"], summary)

    def test_blocked_review_is_retained(self):
        _, summary = self.fill(blocked=True)
        self.desk.publish(self.job["id"], summary)
        value = self.desk.detail(self.job["id"])
        self.assertEqual(value["status"], "review_blocked")
        self.assertEqual(value["review"]["issues"], ["Check debt"])
        self.assertIsNone(value["result"]["rating"])

    def test_mutation_invalidates_published_verdict(self):
        run, summary = self.fill()
        self.desk.publish(self.job["id"], summary)
        data = pilot.read(run / "financial_analyst.json")
        data["findings"][0]["claim"] = "Changed after review"
        pilot.write(run / "financial_analyst.json", data)
        value = self.desk.detail(self.job["id"])
        self.assertEqual(value["status"], "invalidated")
        self.assertIsNone(value["result"])
        self.assertIsNone(value["lead"])

    def test_question_and_follow_up_preserve_original_run(self):
        original, summary = self.fill()
        self.desk.publish(self.job["id"], summary)
        before = (original / "case.json").read_text()
        question = self.desk.submit({"kind": "question", "parent_id": self.job["id"],
                                     "message": "Why no rating?"})
        self.desk.prepare(question["id"])
        self.desk.respond(question["id"], "No validated methodology is implemented.")
        self.assertEqual(self.desk.read(question["id"])["status"], "answered")
        self.assertIsNone(self.desk.read(question["id"])["run_id"])
        followup = self.desk.submit({"kind": "analysis", "parent_id": self.job["id"],
                                    "message": "Check maturity risk again."})
        claimed = self.desk.prepare(followup["id"])
        self.assertNotEqual(self.desk.run_path(claimed), original)
        self.assertEqual(before, (original / "case.json").read_text())

    def test_invalid_input_and_paths_rejected(self):
        for value in ({}, {"message": "x", "case": {}},
                      {"kind": "question", "message": "x"}):
            with self.assertRaises((ValueError, TypeError)):
                self.desk.submit(value)
        with self.assertRaisesRegex(ValueError, "Invalid ID"):
            self.desk.read("../../outside")

    def test_malformed_partial_artifact_does_not_break_case(self):
        claimed = self.desk.prepare(self.job["id"])
        run = self.desk.run_path(claimed)
        (run / "financial_analyst.json").write_text('{"unfinished":')
        self.assertEqual(len(self.desk.detail(self.job["id"])["artifact_errors"]), 1)


if __name__ == "__main__":
    unittest.main()
