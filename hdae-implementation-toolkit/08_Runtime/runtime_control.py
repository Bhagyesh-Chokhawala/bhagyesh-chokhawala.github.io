from datetime import datetime, timezone
import hashlib
import json
import uuid


def evidence(event_type, payload, previous_hash="GENESIS"):
    record = {
        "evidence_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "payload": payload,
        "previous_hash": previous_hash,
    }
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")
    record["record_hash"] = hashlib.sha256(canonical).hexdigest()
    return record


def authorize(action, authority):
    if action in authority.get("prohibited_actions", []):
        return False, "explicitly prohibited"
    if action not in authority.get("allowed_actions", []):
        return False, "outside delegated authority"
    return True, "authorized"


def governed_episode(
    intent,
    authority,
    action,
    context,
    adapter,
    plan=None,
    policy_decision=None,
    human_approval=False,
):
    """Execute one bounded outcome episode with ordered mediation and hash-linked evidence.

    This in-process POC records the durable-workflow handoff point; production must
    persist the episode and approval wait state in a durable orchestration service.
    """
    chain = []
    previous_hash = "GENESIS"

    def record(event_type, payload):
        nonlocal previous_hash
        item = evidence(event_type, payload, previous_hash)
        previous_hash = item["record_hash"]
        chain.append(item)

    episode_id = context.get("episode_id") or str(uuid.uuid4())
    correlation_id = context.get("correlation_id") or episode_id

    def deny(reason, event_type="episode_denied", extra=None):
        record(event_type, {"reason": reason, **(extra or {})})
        return {"status": "DENIED", "reason": reason, "episode_id": episode_id, "evidence": chain}

    if not intent.get("intent_id") or not intent.get("version"):
        return deny("versioned intent envelope is required", "intent_rejected")
    record("intent_loaded", {
        "intent_id": intent["intent_id"],
        "version": intent["version"],
        "success_criteria": intent.get("success_criteria", []),
    })

    identity = context.get("identity", {})
    identity_checks = {
        "human_principal": identity.get("human_principal_authenticated", False),
        "agent_workload": identity.get("agent_workload_authenticated", False),
        "target_tool": identity.get("target_tool_authenticated", False),
    }
    record("identity_authenticated", identity_checks)
    if not all(identity_checks.values()):
        return deny("human, agent, and target-tool identity must all authenticate", "identity_rejected")

    record("approved_context_retrieved", {
        "capability_id": context.get("capability_id"),
        "contract_version": context.get("contract_version"),
        "policy_version": context.get("policy_version"),
        "context_reference": context.get("context_reference"),
    })

    plan = plan or {"action": action, "plan_id": str(uuid.uuid4())}
    if plan.get("action") != action:
        return deny("planned action does not match submitted action", "plan_rejected")
    if action not in intent.get("permitted_actions", authority.get("allowed_actions", [])):
        return deny("action is outside the intent envelope", "intent_scope_denied", {"action": action})
    record("plan_constrained", {"plan": plan, "action": action})

    schema_valid = bool(context.get("schema_valid", True))
    preconditions_valid = bool(context.get("preconditions_valid", True))
    record("action_validated", {"schema_valid": schema_valid, "preconditions_valid": preconditions_valid})
    if not schema_valid or not preconditions_valid:
        return deny("action schema or domain preconditions failed", "action_validation_denied")

    authority_allowed, authority_reason = authorize(action, authority)
    record("authority_decision", {"allow": authority_allowed, "reason": authority_reason})
    if not authority_allowed:
        return deny(authority_reason, "authority_denied", {"action": action})

    decision = policy_decision or {
        "allow": True,
        "policy_id": context.get("policy_id", "local-poc-policy"),
        "policy_version": context.get("policy_version", "unversioned-demo"),
        "reason": "local policy rules passed",
    }
    if context.get("policy_available") is False:
        decision = {**decision, "allow": False, "reason": "policy decision point unavailable"}
    if context.get("evidence_available") is False:
        decision = {**decision, "allow": False, "reason": "evidence capture unavailable"}
    if context.get("state_changing") and not context.get("recovery_plan"):
        decision = {**decision, "allow": False, "reason": "recovery plan required for state-changing action"}
    record("independent_policy_decision", {**decision, "action": action})
    if not decision.get("allow"):
        return deny(decision.get("reason", "policy denied action"), "policy_denied")

    if action in authority.get("approval_required_for", []) and not human_approval:
        wait_state = {
            "approval_id": str(uuid.uuid4()),
            "status": "waiting_for_approval",
            "approver_role": context.get("approver_role", "authorized_human_approver"),
            "action": action,
        }
        record("human_approval_wait_state_created", wait_state)
        return {"status": "PENDING_HUMAN_APPROVAL", "episode_id": episode_id, "approval": wait_state, "evidence": chain}
    if action in authority.get("approval_required_for", []):
        record("human_approval_recorded", {"action": action, "approver": context.get("approver_identity", "demo-approver")})

    workflow_id = str(uuid.uuid4())
    record("durable_workflow_handoff", {"workflow_id": workflow_id, "note": "POC handoff marker; production requires durable orchestration persistence."})
    record("execution_started", {"correlation_id": correlation_id, "action": action})
    try:
        result = adapter({**context, "episode_id": episode_id, "correlation_id": correlation_id})
    except Exception as exc:
        record("execution_failed", {"error": str(exc), "workflow_id": workflow_id})
        recovery = context.get("recovery_result", {"status": "human_intervention_required"})
        record("recovery_outcome", recovery)
        return {"status": "FAILED", "episode_id": episode_id, "error": str(exc), "recovery": recovery, "evidence": chain}

    postconditions_met = bool(context.get("postconditions_met", result.get("ok", True) if isinstance(result, dict) else True))
    record("domain_result_observed", {"result": result, "postconditions_met": postconditions_met})
    if not postconditions_met:
        recovery = context.get("recovery_result", {"status": "reconciliation_required"})
        record("recovery_outcome", recovery)
        return {"status": "RECOVERY_REQUIRED", "episode_id": episode_id, "result": result, "recovery": recovery, "evidence": chain}

    outcome_verified = bool(context.get("success_criteria_met", True))
    record("outcome_verified", {
        "success_criteria_met": outcome_verified,
        "success_criteria": intent.get("success_criteria", []),
        "benefit_reference": context.get("benefit_reference"),
    })
    if not outcome_verified:
        return {"status": "OUTCOME_NOT_VERIFIED", "episode_id": episode_id, "result": result, "evidence": chain}
    record("episode_closed", {"status": "COMPLETED", "workflow_id": workflow_id})
    return {"status": "COMPLETED", "episode_id": episode_id, "result": result, "evidence": chain}


def governed_execute(intent, authority, action, context, adapter, human_approval=False):
    """Backward-compatible entry point that supplies explicit local demo identities."""
    context = {
        **context,
        "identity": context.get("identity", {
            "human_principal_authenticated": True,
            "agent_workload_authenticated": True,
            "target_tool_authenticated": True,
        }),
        "recovery_plan": context.get("recovery_plan", {"plan_id": "legacy-wrapper-demo-recovery"}),
    }
    intent = {"version": intent.get("version", "legacy-wrapper-v1"), **intent}
    intent.setdefault("permitted_actions", authority.get("allowed_actions", []))
    return governed_episode(intent, authority, action, context, adapter, human_approval=human_approval)
