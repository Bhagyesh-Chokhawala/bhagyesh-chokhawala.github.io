import io
import json
import unittest
import zipfile

from app import _BAR_HDAE_STAGES, _HDAE_PHASES, create_app
import wsgi


class AppTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.client.post("/login", data={"username": "admin", "password": "hdae-admin"})

    def test_dashboard_exposes_bar_hdae_model(self):
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn("BAR-HDAE Control Plane", page)
        self.assertIn("BAR-B", page)
        self.assertIn("G0", page)

        framework = self.client.get("/framework")
        self.assertEqual(framework.status_code, 200)
        self.assertIn("whether, where, and to what extent", framework.get_data(as_text=True))
        gates_page = self.client.get("/governance").get_data(as_text=True)
        self.assertIn("<td>G0</td>", gates_page)
        self.assertIn("Business legitimacy", gates_page)
        evidence_page = self.client.get("/evidence").get_data(as_text=True)
        self.assertIn("No episode or lifecycle events", evidence_page)

    def test_paper_model_has_twelve_artifacts_seven_phases_four_gates(self):
        steps = self.client.get("/api/architecture").get_json()["steps"]
        self.assertEqual(len(steps), 12)
        self.assertEqual([item["title"] for item in steps], [item["title"] for item in _BAR_HDAE_STAGES])
        self.assertEqual(len(_HDAE_PHASES), 7)

        gates = self.client.get("/api/pipeline").get_json()["gate_details"]
        self.assertEqual(set(gates), {"G0", "G1", "G2", "G3"})

        toolkit = self.client.get("/api/toolkit").get_json()
        self.assertEqual(toolkit["framework_status"], "conceptual; not empirically validated")
        self.assertEqual(len(toolkit["artifacts"]), 12)
        self.assertEqual(len(toolkit["bar_gates"]), 4)
        with open("12_Maturity/HDAE_Maturity_Model.csv", encoding="utf-8") as maturity_file:
            maturity = maturity_file.read()
        self.assertIn("L4,Adaptive enterprise agents", maturity)
        self.assertNotIn("L5,", maturity)
        with open("14_Architecture/HDAE_Reference_Architecture.md", encoding="utf-8") as architecture_file:
            reference_architecture = architecture_file.read()
        self.assertIn("Outer loop: BAR capability lifecycle", reference_architecture)
        self.assertIn("Inner loop: HDAE outcome episode", reference_architecture)

    def test_subscription_demo_prefills_all_artifacts_and_only_g0_g1(self):
        loaded = self.client.post("/wizard/demo/subscription")
        self.assertEqual(loaded.status_code, 302)
        state = self.client.get("/api/wizard").get_json()
        pipeline = self.client.get("/api/pipeline").get_json()
        self.assertTrue(state["sample_loaded"])
        self.assertEqual(state["total_steps"], 12)
        self.assertEqual(state["completed_steps"], 12)
        self.assertEqual(pipeline["status"], "ready")
        self.assertEqual(pipeline["gates"]["completed"], 2)
        self.assertEqual(pipeline["gates"]["missing"], ["G2", "G3"])

        charter = self.client.get("/process/artifact/outcome-charter.json?format=json").get_json()
        self.assertEqual(charter["artifact_type"], "outcome_charter")
        self.assertIn("subscription sales", charter["configuration"]["operator_input"]["problem"].lower())

    def test_onboarding_demo_prefills_all_artifacts(self):
        self.client.post("/wizard/demo")
        state = self.client.get("/api/wizard").get_json()
        self.assertEqual(state["completed_steps"], 12)
        self.assertEqual(state["process"]["name"], "Governed Customer Onboarding")
        page = self.client.get("/wizard").get_data(as_text=True)
        self.assertIn("12 toolkit artifacts are prefilled", page)

    def test_wizard_captures_machine_valid_intent_envelope(self):
        self.client.post("/wizard", data={"action": "next", "answer": "Outcome charter draft"})
        self.client.post("/wizard", data={"action": "next", "answer": "Human intent canvas draft"})
        page = self.client.get("/wizard").get_data(as_text=True)
        self.assertIn("Intent Envelope Schema", page)
        self.assertIn("Maximum allowed autonomy", page)

        incomplete = self.client.post("/wizard", data={"action": "next", "field_intent_id": "intent-v1"})
        self.assertEqual(incomplete.status_code, 200)
        self.assertIn("Complete required fields", incomplete.get_data(as_text=True))

        values = {
            "action": "next",
            "field_intent_id": "intent-v1",
            "field_constraints": "No unauthorized state changes.",
            "field_success_evidence": "Verified postconditions and complete trace.",
            "field_expiry": "30 days.",
            "field_autonomy_ceiling": "Agent may prepare; human approves.",
            "field_recovery_criteria": "Pause and escalate unresolved failures.",
        }
        saved = self.client.post("/wizard", data=values)
        self.assertEqual(saved.status_code, 302)
        artifact = self.client.get("/wizard/artifact/3").get_json()
        self.assertEqual(artifact["status"], "configured")
        self.assertEqual(artifact["configuration"]["operator_input"]["intent_id"], "intent-v1")

    def test_bar_gate_sequence_build_and_scale_status(self):
        blocked = self.client.post("/api/pipeline/build")
        self.assertEqual(blocked.status_code, 409)
        self.assertEqual(blocked.get_json()["missing_steps"], list(range(1, 13)))
        early_pilot = self.client.post("/pipeline/gates/G2", data={"status": "complete", "owner": "Pilot board", "evidence": "Not yet"})
        self.assertEqual(early_pilot.status_code, 409)
        missing_g0_evidence = self.client.post("/pipeline/gates/G0", data={"status": "complete", "owner": "Business owner"})
        self.assertEqual(missing_g0_evidence.status_code, 400)

        self.client.post("/wizard/demo/subscription")
        before_pilot = self.client.get("/api/pipeline").get_json()
        self.assertEqual(before_pilot["status"], "ready")
        self.assertEqual(before_pilot["prebuild_gates_missing"], [])
        self.assertEqual(before_pilot["gates"]["missing"], ["G2", "G3"])

        build = self.client.post("/api/pipeline/build")
        self.assertEqual(build.status_code, 200)
        self.assertEqual(build.get_json()["status"], "built")
        self.assertEqual(build.get_json()["build"]["artifact_count"], 12)

        self.client.post("/pipeline/gates/G2", data={
            "status": "complete",
            "owner": "Pilot review board",
            "evidence": "Restricted pilot results, traces, recovery tests, adoption and KPI evidence",
        })
        self.client.post("/pipeline/gates/G3", data={
            "status": "complete",
            "owner": "Enterprise architecture board",
            "evidence": "Sustained value, readiness and risk review approved",
        })
        self.assertEqual(self.client.get("/api/pipeline").get_json()["status"], "scaled")

    def test_generated_artifacts_include_paper_sections_and_package(self):
        self.client.post("/wizard/demo/subscription")
        names = [item["file"] for item in self.client.get("/api/wizard").get_json()["artifacts"]]
        self.assertEqual(len(names), 12)
        for filename in names:
            response = self.client.get(f"/process/artifact/{filename}")
            self.assertEqual(response.status_code, 200)
            page = response.get_data(as_text=True)
            for section in ("Architecture Deliverables", "Deployment Decisions", "Validation Checks", "Risk Considerations"):
                self.assertIn(section, page)

        envelope = self.client.get("/process/artifact/intent-envelope.json?format=json").get_json()
        docs = envelope["architecture"]["documentation"]
        self.assertEqual(len(docs["Architecture Deliverables"]), 4)
        self.assertIn("process_context", docs["Validation Checks"][0])

        response = self.client.get("/wizard/download")
        self.assertEqual(response.status_code, 200)
        with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
            names_in_package = set(archive.namelist())
            manifest = json.loads(archive.read("hdae-wizard-manifest.json"))
        self.assertIn("outcome-charter.json", names_in_package)
        self.assertIn("intent-envelope.json", names_in_package)
        self.assertEqual(len(manifest["artifacts"]), 12)

    def test_architecture_and_plan_reports_are_bar_hdae_ui(self):
        self.client.post("/wizard/demo/subscription")
        architecture = self.client.get("/process/enterprise-solution-architecture.json")
        plan = self.client.get("/process/implementation-plan.json")
        self.assertEqual(architecture.mimetype, "text/html")
        self.assertIn("Outer BAR lifecycle", architecture.get_data(as_text=True))
        self.assertIn("G0", architecture.get_data(as_text=True))
        context_diagram = self.client.get("/process/deliverable/c4-system-context?download=1").get_data(as_text=True)
        container_diagram = self.client.get("/process/deliverable/c4-container-view?download=1").get_data(as_text=True)
        self.assertIn("barLifecycle", context_diagram)
        self.assertIn("barReview", container_diagram)
        self.assertEqual(plan.mimetype, "text/html")
        self.assertIn("HDAE Phase", plan.get_data(as_text=True))
        plan_page = plan.get_data(as_text=True)
        for detail in ("Architecture Deliverables", "Deployment Decisions", "Validation Checks", "Risk Considerations", "<strong>Evidence:</strong>"):
            self.assertIn(detail, plan_page)
        self.assertNotIn("&#x27;implementation_guidance&#x27;", plan_page)
        self.assertEqual(self.client.get("/process/implementation-plan.json?format=json").get_json()["document_type"], "implementation_plan")

    def test_measurement_and_maturity_match_manuscript(self):
        page = self.client.get("/measurement")
        self.assertEqual(page.status_code, 200)
        text = page.get_data(as_text=True)
        for metric in ("Intent Coverage", "Policy Mediation Rate", "Trace Completeness", "Realized benefit"):
            self.assertIn(metric, text)
        for level in ("L0", "L1", "L2", "L3", "L4"):
            self.assertIn(level, text)
        self.assertIn("not empirically validated", text)

    def test_custom_process_creation_and_health(self):
        created = self.client.post("/process/new", data={
            "name": "Vendor invoice reconciliation",
            "description": "Match invoices to purchase orders and payments.",
            "domain": "Procurement and finance",
            "business_outcome": "Accurate invoice approvals and payments.",
        })
        self.assertEqual(created.status_code, 302)
        process = self.client.get("/api/process").get_json()["process"]
        self.assertEqual(process["name"], "Vendor invoice reconciliation")
        health = self.client.get("/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.get_json()["status"], "ok")

    def test_governed_runtime_and_wsgi_entry(self):
        payload = {
            "intent_id": "demo-001",
            "action": "create_record",
            "authority": {"allowed_actions": ["create_record"], "prohibited_actions": [], "approval_required_for": []},
            "context": {"state_changing": False, "correlation_id": "corr-123"},
        }
        response = self.client.post("/api/execute", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "COMPLETED")
        self.assertTrue(wsgi.app)

    def test_runtime_complete_mediation_trace_and_hash_chain(self):
        payload = {
            "intent_id": "episode-123",
            "intent_version": "v1",
            "action": "create_record",
            "authority": {"allowed_actions": ["create_record"], "prohibited_actions": [], "approval_required_for": []},
            "plan": {"plan_id": "plan-1", "action": "create_record"},
            "success_criteria": ["record exists"],
            "context": {
                "state_changing": True,
                "recovery_plan": {"plan_id": "recovery-1"},
                "correlation_id": "corr-episode-123",
                "identity": {"human_principal_authenticated": True, "agent_workload_authenticated": True, "target_tool_authenticated": True},
            },
        }
        result = self.client.post("/api/execute", json=payload).get_json()
        self.assertEqual(result["status"], "COMPLETED")
        event_types = [entry["event_type"] for entry in result["evidence"]]
        self.assertEqual(event_types[0], "intent_loaded")
        self.assertIn("independent_policy_decision", event_types)
        self.assertIn("durable_workflow_handoff", event_types)
        self.assertEqual(event_types[-1], "episode_closed")
        for previous, current in zip(result["evidence"], result["evidence"][1:]):
            self.assertEqual(current["previous_hash"], previous["record_hash"])

    def test_runtime_requires_identity_and_records_human_approval_wait(self):
        denied = self.client.post("/api/execute", json={
            "intent_id": "episode-no-identity",
            "action": "create_record",
            "authority": {"allowed_actions": ["create_record"], "prohibited_actions": [], "approval_required_for": []},
            "context": {"identity": {"human_principal_authenticated": False, "agent_workload_authenticated": True, "target_tool_authenticated": True}},
        }).get_json()
        self.assertEqual(denied["status"], "DENIED")
        self.assertEqual(denied["evidence"][-1]["event_type"], "identity_rejected")

        pending = self.client.post("/api/execute", json={
            "intent_id": "episode-approval",
            "action": "capture_payment",
            "authority": {"allowed_actions": ["capture_payment"], "prohibited_actions": [], "approval_required_for": ["capture_payment"]},
            "context": {"state_changing": True, "recovery_plan": {"plan_id": "payment-recovery"}},
        }).get_json()
        self.assertEqual(pending["status"], "PENDING_HUMAN_APPROVAL")
        self.assertEqual(pending["approval"]["status"], "waiting_for_approval")

    def test_runtime_fail_closed_and_postcondition_recovery(self):
        policy_denial = self.client.post("/api/execute", json={
            "intent_id": "episode-policy-down",
            "action": "create_record",
            "authority": {"allowed_actions": ["create_record"], "prohibited_actions": [], "approval_required_for": []},
            "context": {"policy_available": False},
        }).get_json()
        self.assertEqual(policy_denial["status"], "DENIED")
        self.assertTrue(any(event["event_type"] == "policy_denied" for event in policy_denial["evidence"]))

        recovery = self.client.post("/api/execute", json={
            "intent_id": "episode-postcondition-failed",
            "action": "create_record",
            "authority": {"allowed_actions": ["create_record"], "prohibited_actions": [], "approval_required_for": []},
            "context": {"postconditions_met": False, "recovery_result": {"status": "reconciled", "owner": "Domain Operations"}},
        }).get_json()
        self.assertEqual(recovery["status"], "RECOVERY_REQUIRED")
        self.assertEqual(recovery["recovery"]["status"], "reconciled")


if __name__ == "__main__":
    unittest.main()