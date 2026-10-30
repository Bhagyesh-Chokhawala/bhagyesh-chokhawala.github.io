import importlib.util
import html
import io
import json
import os
import re
import uuid
import zipfile
from datetime import datetime, timezone

from flask import Flask, current_app, jsonify, redirect, render_template_string, request, send_file, session, url_for


def _load_runtime_module():
    runtime_path = os.path.join(os.path.dirname(__file__), "08_Runtime", "runtime_control.py")
    spec = importlib.util.spec_from_file_location("runtime_control", runtime_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runtime_control = _load_runtime_module()
governed_execute = runtime_control.governed_execute
governed_episode = runtime_control.governed_episode


_HDAE_PHASES = [
    {"id": "scope", "name": "Scope outcome episode", "bar": "BAR-B"},
    {"id": "intent", "name": "Model Intent Envelope", "bar": "BAR-B + HDAE"},
    {"id": "capabilities", "name": "Map capabilities and contracts", "bar": "BAR-A + HDAE"},
    {"id": "delegation", "name": "Design delegation and autonomy", "bar": "BAR-R + HDAE"},
    {"id": "toolchain", "name": "Assemble agent toolchain", "bar": "BAR-A + HDAE"},
    {"id": "integrity", "name": "Engineer integrity and evidence", "bar": "BAR-A/R + HDAE"},
    {"id": "evaluation", "name": "Validate, learn, and scale", "bar": "BAR-B/R + HDAE"},
]


_BAR_HDAE_STAGES = [
    {"id": "outcome_charter", "title": "Outcome Charter", "description": "Establish the business problem, accountable owner, baseline, target benefit, affected stakeholders, risk class, and rationale for using AI.", "phase": 1},
    {"id": "intent_canvas", "title": "Enterprise Intent Canvas", "description": "Capture human purpose and accountability across why, what, who, when, where, which, authority, and stakeholders.", "phase": 2},
    {"id": "intent_envelope", "title": "Intent Envelope Schema", "description": "Define machine-validatable intent, constraints, success evidence, expiry, autonomy ceiling, and recovery criteria.", "phase": 2},
    {"id": "capability_readiness", "title": "Capability-Readiness Map", "description": "Assess capability owners, authoritative data, applications, events, dependencies, non-functional requirements, and readiness gaps.", "phase": 3},
    {"id": "outcome_contract", "title": "Outcome Contract Template", "description": "Specify requestor, preconditions, applicable policies, state model, completion, failure, retry, and compensation semantics.", "phase": 3},
    {"id": "authority_profile", "title": "Agent Authority Profile", "description": "Bound represented principal, workload identity, scopes, tools, permissions, prohibitions, thresholds, expiry, and revocation.", "phase": 4},
    {"id": "autonomy_risk", "title": "Autonomy-Risk Matrix", "description": "Align autonomy to impact, uncertainty, reversibility, data sensitivity, legal or ethical exposure, observability, and recovery strength.", "phase": 4},
    {"id": "tool_registry", "title": "Tool and Action Registry", "description": "Register trusted tools with capability mapping, schemas, side effects, owner, version, and risk classification.", "phase": 5},
    {"id": "policy_control", "title": "Policy and Control Pack", "description": "Define machine-enforceable policies, independent decision points, tests, exceptions, approvals, and logs.", "phase": 5},
    {"id": "transaction_recovery", "title": "Transaction and Recovery Map", "description": "Specify state transitions, idempotency, retries, compensation, reconciliation, and terminal states.", "phase": 6},
    {"id": "traceability_evaluation", "title": "Traceability and Evaluation Schema", "description": "Link intent, plan, policy, tool, transaction, intervention, outcome, and benefit evidence.", "phase": 6},
    {"id": "realization_playbook", "title": "Governance, Incident, and Realization Playbook", "description": "Define release gates, monitoring, pause or kill, incident roles, rollback, benefit review, and retirement decisions.", "phase": 7},
]


def _wizard_state():
    state_id = session.get("hdae_state_id")
    if not state_id:
        state_id = uuid.uuid4().hex
        session["hdae_state_id"] = state_id
    store = current_app.extensions.setdefault("hdae_state_store", {})
    return store.setdefault(state_id, {})


def _wizard_state_get(key, default=None):
    return _wizard_state().get(key, default)


def _wizard_state_set(key, value):
    _wizard_state()[key] = value


def _wizard_state_pop(key, default=None):
    return _wizard_state().pop(key, default)


def _parse_architecture_steps():
    return [{**stage, "number": index} for index, stage in enumerate(_BAR_HDAE_STAGES, start=1)]


def _wizard_prompt(step):
    return step.get("description", f"Define {step['title']} for this capability.")


_BAR_METRICS = {
    "BAR-B · Business value": [
        ("Baseline-to-target improvement", "Measured benefit against the approved baseline", "Higher"),
        ("Benefit ownership", "Share of target benefits with named accountable owners", "100%"),
    ],
    "BAR-A · Architecture readiness": [
        ("Data readiness", "Authoritative data quality and access readiness", "Higher"),
        ("Contract/dependency coverage", "Critical dependencies with owned, tested contracts", "Higher"),
        ("Availability / resilience", "Service availability and tested failure recovery", "Higher"),
        ("Lifecycle cost", "Total run, integration, assurance, and change cost", "Within approved case"),
    ],
    "HDAE · Episode controls": [
        ("Intent Coverage", "Episodes with complete validated intent", "100%"),
        ("Policy Mediation Rate", "Material actions evaluated by independent policy controls", "100%"),
        ("Trace Completeness", "Material actions linked across intent, plan, policy, tool, transaction, intervention, outcome", "100%"),
        ("Unauthorized-action rate", "Unauthorized actions executed", "0"),
        ("Approval latency", "Time waiting for required human decisions", "Measured"),
        ("Intervention / compensation rate", "Episodes requiring intervention or compensation", "Measured"),
        ("Recovery time", "Time to restore or reconcile after failure", "Within SLO"),
    ],
    "BAR-R · Responsible realization": [
        ("Adoption and user trust", "Use, acceptance, overrides, and escalation patterns", "Measured"),
        ("Incident and residual risk trend", "Incidents and risk remaining after controls", "Within appetite"),
        ("Realized benefit", "Sustained benefit after adoption and lifecycle cost", "Positive"),
    ],
}


_MATURITY_LEVELS = [
    ("L0", "Isolated assistance", "Informal intent, authority, and evidence; no delegated state-changing authority."),
    ("L1", "Registered agents", "Agent identity, ownership, inventory, and basic logs are established."),
    ("L2", "Bounded delegation", "Intent Envelopes, authority profiles, autonomy classification, policy decisions, and approvals are used."),
    ("L3", "Governed execution", "Durable orchestration, complete traces, tested recovery, proportional autonomy, and BAR realization reviews."),
    ("L4", "Adaptive enterprise agents", "Reusable capabilities, contracts, controls, evaluations, and adaptive autonomy inside governed limits."),
]


_DEMO_STEP_ANSWERS = {
    "Humans: Why What Who When Where Which": {
        "why": "Reduce onboarding cycle time while preserving compliance review.",
        "what": "Prepare complete customer onboarding cases for human decision.",
        "who": "Operations owns the workflow; Compliance owns approval.",
        "when": "Business-day processing with a four-hour target.",
        "where": "CRM, document store, screening service, and case-management platform.",
        "which": "New business-customer onboarding cases in the pilot region.",
    },
    "Intent Envelope": {
        "purpose": "Automate governed preparation of onboarding cases.",
        "outcome": "A complete, traceable case ready for compliance review.",
        "success_criteria": "95% document completeness; zero unauthorized approvals; full evidence coverage.",
        "scope": "Intake, document checklist, validation, draft case creation, and escalation.",
        "constraints": "No final approval, account activation, risk-rating changes, or sanctions override.",
        "timing": "Pilot for 30 days; four-hour service objective during business hours.",
        "accountability": "Operations Director owns the outcome; Compliance Director approves policy decisions.",
        "context": "Existing CRM, case platform, document repository, and screening API.",
    },
    "AI Agent: Delegated Operational How": {
        "agent_id": "customer-onboarding-preparer",
        "responsibilities": "Collect documents, validate completeness, prepare a draft case, and escalate exceptions.",
        "allowed_actions": "Read approved records; create draft cases; request missing documents; call screening API.",
        "prohibited_actions": "Approve customers, activate accounts, change risk ratings, or override sanctions results.",
        "escalation": "Route policy ambiguity, failed screening, or missing approval to Compliance.",
    },
    "Runtime Control Gateway": {
        "controls": "Authorize every operation, enforce policy before state changes, and record post-action evidence.",
        "authorization": "Allow only actions listed in the agent authority profile and current intent envelope.",
        "approvals": "Require Compliance approval before any case moves from draft to decision.",
        "execution": "Use idempotency keys, bounded retries, 30-second API timeouts, pause, and cancel controls.",
    },
    "Identity / Authority / Policy / Approval": {
        "principals": "Agent service identity, Operations role, and Compliance approver role.",
        "authority": "Least privilege; draft-case creation only; no activation or approval authority.",
        "policies": "KYC policy, sanctions policy, data classification policy, and retention policy.",
        "risk": "Human approval required for state changes, exceptions, and any high-risk screening result.",
    },
    "Business Capabilities": {
        "capabilities": "Customer Onboarding, KYC Operations, Compliance Review, Case Management, and Document Management.",
        "owners": "Operations Director, Compliance Director, and Platform Engineering owner.",
        "dependencies": "CRM availability, screening service SLA, document storage, and case-management workflow.",
    },
    "Outcome Contracts": {
        "inputs": "Customer application, identity documents, company records, and screening request.",
        "outputs": "Complete draft onboarding case with validation results and evidence references.",
        "acceptance": "Compliance can review the case and trace every agent decision and source document.",
        "service_levels": "95% document completeness and four-hour business-day preparation objective.",
        "failure_conditions": "Incomplete evidence, failed screening, duplicate case, unavailable system, or policy exception.",
    },
    "Domain APIs / Applications / Systems of Record": {
        "systems": "CRM, case-management platform, document repository, and sanctions screening service.",
        "apis": "Customer lookup, document upload, case draft creation, and screening request APIs.",
        "data_mapping": "Map customer ID, case ID, document ID, screening result, and correlation ID across systems.",
        "credentials": "Use workload identity and secret-manager references; no credentials in artifacts.",
        "idempotency": "Use customer ID plus intent ID for deduplication; retry only safe operations.",
    },
    "Data & Knowledge": {
        "sources": "Approved KYC policy, document checklist, customer records, and screening guidance.",
        "access": "Read-only retrieval with customer-case scoping and Compliance-only restricted content.",
        "quality": "Refresh policy content daily and reject stale or incomplete customer records.",
        "classification": "Restricted customer data; encrypt, retain per policy, and redact from non-authorized logs.",
    },
    "Evidence / Observability": {
        "events": "Intent accepted, policy evaluated, document read, API called, draft created, approval requested, and exception raised.",
        "correlation": "Propagate intent ID, case ID, customer ID, agent ID, and correlation ID.",
        "metrics": "Cycle time, completeness rate, policy denials, human interventions, API errors, and duplicate rate.",
        "retention": "Immutable audit records retained for the regulatory period and accessible to Audit and Compliance.",
    },
    "Recovery / Compensation / Intervention": {
        "failure_modes": "Duplicate case, screening timeout, partial upload, policy outage, and inconsistent source data.",
        "compensation": "Remove duplicate draft, reconcile partial uploads, and mark incomplete cases for review.",
        "escalation": "Escalate failed screening and policy ambiguity to Compliance; platform outages to Engineering.",
        "retry": "Retry safe reads three times, pause on policy outage, and require human takeover after threshold.",
    },
}


_SUBSCRIPTION_DEMO_ANSWERS = {
    "Humans: Why What Who When Where Which": {
        "why": "Create a predictable, auditable subscription revenue stream.",
        "what": "Sell subscriptions, activate service after payment, renew customers, and collect recurring revenue.",
        "who": "Sales owns conversion; Billing owns payment collection; Customer Success owns retention.",
        "when": "Self-service signup at any time, with monthly and annual billing cycles.",
        "where": "Web storefront, subscription billing platform, payment processor, CRM, and general ledger.",
        "which": "Plans, discounts, customer eligibility, payment methods, renewals, cancellations, refunds, and dunning.",
    },
    "Intent Envelope": {
        "purpose": "Establish an end-to-end, governed subscription-to-cash process.",
        "outcome": "A customer can purchase a plan, receive entitled service, and be billed and collected accurately.",
        "success_criteria": "Checkout conversion above 8%; payment success above 97%; invoices reconcile daily; duplicate charges below 0.01%.",
        "scope": "Plan selection, checkout, payment authorization, subscription activation, invoicing, renewal, collection, cancellation, and refund.",
        "constraints": "Never store raw card data; require consent; honor tax and pricing rules; do not activate on failed payment.",
        "timing": "MVP in 12 weeks; launch with monthly plans before annual billing and international markets.",
        "accountability": "VP of Revenue owns the process; Finance Controller approves revenue controls; Product owns plan configuration.",
        "context": "Existing storefront, CRM, payment provider, subscription ledger, and finance close process.",
    },
    "AI Agent: Delegated Operational How": {
        "agent_id": "subscription-operations-agent",
        "responsibilities": "Explain plans, assist checkout, detect billing exceptions, notify customers, and prepare refund or cancellation requests.",
        "allowed_actions": "Read plan catalog; create checkout session; read payment status; send approved notices; draft billing adjustments.",
        "prohibited_actions": "Change published prices, access raw card data, issue high-value refunds, waive debt, or alter accounting entries.",
        "escalation": "Escalate disputes, failed collections, tax exceptions, fraud flags, and adjustments above policy limits to a human.",
    },
    "Runtime Control Gateway": {
        "controls": "Validate intent, customer consent, plan version, price, currency, payment state, and idempotency before writes.",
        "authorization": "Permit only catalog, checkout, billing, and notification actions assigned to the agent role.",
        "approvals": "Require Finance approval for refunds above threshold, credits, write-offs, and manual revenue adjustments.",
        "execution": "Use tokenized payment APIs, idempotency keys, bounded retries, webhook verification, and immutable post-action evidence.",
    },
    "Identity / Authority / Policy / Approval": {
        "principals": "Customer, subscription agent workload identity, Billing Operations, Finance Controller, and support roles.",
        "authority": "Agent may create checkout and draft adjustments; payment capture and high-value refunds follow delegated limits.",
        "policies": "Pricing, consent, PCI scope, refund, tax, revenue recognition, collections, privacy, and retention policies.",
        "risk": "Step-up approval for refunds above $250, payment-method changes on flagged accounts, and write-offs.",
    },
    "Business Capabilities": {
        "capabilities": "Product Catalog, Digital Commerce, Subscription Management, Payment Processing, Billing, Collections, and Revenue Accounting.",
        "owners": "Product, Revenue Operations, Billing Operations, Finance, and Customer Success leaders.",
        "dependencies": "Payment provider uptime, catalog correctness, tax calculation, entitlement service, and ledger reconciliation.",
    },
    "Outcome Contracts": {
        "inputs": "Customer identity and consent, selected plan/version, price, tax jurisdiction, payment token, and billing cadence.",
        "outputs": "Confirmed order, active subscription, entitlement, invoice, payment reference, and revenue evidence.",
        "acceptance": "One authorized charge per order; service entitlement matches paid plan; invoice and ledger reconcile.",
        "service_levels": "Checkout response under 3 seconds at p95; payment status within 60 seconds; daily reconciliation by 06:00 UTC.",
        "failure_conditions": "Payment decline, duplicate webhook, price mismatch, tax failure, entitlement delay, refund dispute, or ledger variance.",
    },
    "Domain APIs / Applications / Systems of Record": {
        "systems": "Storefront, product catalog, CRM, subscription billing platform, payment processor, tax service, entitlement service, and general ledger.",
        "apis": "Create checkout, authorize/capture payment, create subscription, issue invoice, cancel/renew, refund, and reconcile.",
        "data_mapping": "Propagate customer ID, order ID, subscription ID, invoice ID, payment reference, plan version, and correlation ID.",
        "credentials": "Use workload identity and provider-managed tokenization; store secrets only in the enterprise secrets manager.",
        "idempotency": "Use order ID for checkout/capture and provider event ID for webhook processing; reconcile before retrying ambiguous writes.",
    },
    "Data & Knowledge": {
        "sources": "Approved plan catalog, terms of service, pricing rules, tax rules, billing FAQ, and customer subscription history.",
        "access": "Customer-scoped read access; payment tokens only; prohibit retrieval of raw card data and unrelated customer records.",
        "quality": "Use versioned catalog and pricing; validate tax and currency data at checkout; reconcile provider events against ledger.",
        "classification": "Customer and financial data are restricted; tokenize payment data; apply finance retention and privacy deletion rules.",
    },
    "Evidence / Observability": {
        "events": "Consent, plan presented, checkout started, payment authorized/captured/declined, subscription activated, invoice issued, refund, cancellation, and reconciliation.",
        "correlation": "Carry customer, order, subscription, invoice, provider event, intent, and trace identifiers across all systems.",
        "metrics": "Conversion, payment success, churn, involuntary churn, recovery rate, refund rate, duplicate charge rate, and reconciliation variance.",
        "retention": "Retain financial transaction evidence under finance policy; prevent cardholder data in logs; grant Finance/Audit read access.",
    },
    "Recovery / Compensation / Intervention": {
        "failure_modes": "Payment timeout with unknown result, duplicate webhook, charge without entitlement, entitlement without charge, and ledger variance.",
        "compensation": "Query provider before retry; revoke unpaid entitlement; issue approved refund for duplicate capture; queue ledger variance for reconciliation.",
        "escalation": "Route fraud and disputes to Risk; payment incidents to Billing Operations; accounting variances to Finance.",
        "retry": "Retry idempotent reads and webhook processing; pause on uncertain capture; require human review for unresolved money movement.",
    },
}


_STEP_FIELDS = {
    "Outcome Charter": [
        ("problem", "Business problem and baseline", True), ("owner", "Accountable value owner", True),
        ("target_benefit", "Target benefit and measure", True), ("stakeholders", "Affected stakeholders", True),
        ("ai_rationale", "Why AI rather than a simpler alternative", True), ("risk_class", "Initial risk class", True),
    ],
    "Enterprise Intent Canvas": [
        ("why", "Why: purpose and legitimacy", True), ("what", "What: authorized outcome", True),
        ("who", "Who: principal, participants, accountable owner", True), ("when", "When: timing and validity", True),
        ("where", "Where: organizational and system scope", True), ("which", "Which: priorities, policies, and constraints", True),
    ],
    "Intent Envelope Schema": [
        ("intent_id", "Intent identifier and version", True), ("constraints", "Scope, constraints, and prohibited outcomes", True),
        ("success_evidence", "Success criteria and evidence", True), ("expiry", "Expiry and renewal condition", True),
        ("autonomy_ceiling", "Maximum allowed autonomy", True), ("recovery_criteria", "Recovery and closure criteria", True),
    ],
    "Capability-Readiness Map": [
        ("capabilities", "Capabilities and accountable owners", True), ("data", "Authoritative data and data owners", True),
        ("systems", "Applications, APIs, and systems of record", True), ("dependencies", "Events, dependencies, and integrations", True),
        ("nfrs", "Availability, latency, scale, and resilience NFRs", True), ("readiness_gaps", "Identity, security, observability, cost readiness gaps", True),
    ],
    "Outcome Contract Template": [
        ("requestor", "Requestor and receiving capability", True), ("preconditions", "Preconditions and required context", True),
        ("policies", "Applicable policies and contract version", True), ("state_model", "Domain states and permitted transitions", True),
        ("completion", "Completion and postcondition criteria", True), ("failure_recovery", "Failure, retry, and compensation semantics", True),
    ],
    "Agent Authority Profile": [
        ("principal", "Represented human principal and agent workload identity", True), ("scopes", "Authorized scopes and capabilities", True),
        ("tools", "Allowed tools and permissions", True), ("prohibitions", "Prohibited actions", True),
        ("thresholds", "Thresholds, approval rules, expiry, and revocation", True),
    ],
    "Autonomy-Risk Matrix": [
        ("impact", "Impact and consequence classification", True), ("uncertainty", "Execution uncertainty", True),
        ("reversibility", "Reversibility and compensation strength", True), ("sensitivity", "Data, legal, and ethical sensitivity", True),
        ("observability", "Observability and intervention readiness", True), ("autonomy_level", "Recommended autonomy ceiling and rationale", True),
    ],
    "Tool and Action Registry": [
        ("registry", "Trusted tools and actions", True), ("capability_mapping", "Capability and contract mapping", True),
        ("schemas", "Input/output schemas and preconditions", True), ("side_effects", "Side effects and state-change classification", True),
        ("ownership_version", "Tool owner, version, and lifecycle", True), ("risk", "Tool risk classification", True),
    ],
    "Policy and Control Pack": [
        ("rules", "Machine-enforceable policy rules", True), ("decision_point", "Independent policy decision point", True),
        ("tests", "Policy test cases and expected decisions", True), ("exceptions", "Exception and escalation handling", True),
        ("approvals", "Approval thresholds and approver identity", True), ("logs", "Decision logs and policy version evidence", True),
    ],
    "Transaction and Recovery Map": [
        ("states", "Transaction states and allowed transitions", True), ("idempotency", "Idempotency keys and duplicate handling", True),
        ("retries", "Retry budgets and timeout rules", True), ("compensation", "Compensation and rollback actions", True),
        ("reconciliation", "Reconciliation and human intervention", True), ("terminal_states", "Success, rejection, suspension, and recovery terminal states", True),
    ],
    "Traceability and Evaluation Schema": [
        ("provenance_links", "Intent-plan-policy-tool-transaction-intervention-outcome-benefit links", True),
        ("metrics", "Business, architecture, control, operational, and human metrics", True),
        ("completeness", "Trace completeness and attribution rules", True), ("evaluation", "Baseline, target, observation window, and evaluation method", True),
        ("review", "Evidence reviewer and BAR realization review cadence", True),
    ],
    "Governance, Incident, and Realization Playbook": [
        ("release_gates", "Release gates and decision rights", True), ("monitoring", "Monitoring, alerting, and adoption signals", True),
        ("intervention", "Pause, kill, override, and escalation paths", True), ("incident_roles", "Incident roles, communications, and rollback owner", True),
        ("realization", "Benefit review and scale/hold/remediate/stop criteria", True), ("retirement", "Retirement, revocation, and data closure", True),
    ],
}


_IMPLEMENTATION_GATES = [
    ("G0", "Business legitimacy", "BAR-B: problem, accountable owner, baseline, benefit target, affected parties, and AI rationale"),
    ("G1", "Architecture readiness", "BAR-A: authoritative data, integration, identity, NFRs, resilience, observability, and lifecycle cost"),
    ("G2", "Controlled pilot", "BAR-R: restricted authority, policy compliance, trace completeness, tested recovery, adoption, and KPI evidence"),
    ("G3", "Enterprise scale", "BAR-B/A/R: sustained value, readiness, responsible adoption, reusable controls, and continuous assurance"),
]


_BAR_HDAE_DEMO_ANSWERS = {
    "customer_onboarding": {
        "Outcome Charter": {"problem": "Onboarding cases are slow and often incomplete, delaying compliant customer activation.", "owner": "Operations Director", "target_benefit": "Reduce cycle time to four hours and reach 95% document completeness.", "stakeholders": "Applicants, Operations, Compliance, Risk, Customer Support.", "ai_rationale": "AI can coordinate document checks and draft cases; rules-based automation remains preferable for deterministic policy decisions.", "risk_class": "High-impact financial-services workflow; agent restricted to read and draft operations."},
        "Enterprise Intent Canvas": {"why": "Reduce onboarding cycle time while preserving compliance review.", "what": "Prepare complete, traceable customer cases for human decision.", "who": "Operations owns the outcome; Compliance approves policy exceptions; customer is the represented party.", "when": "Business-day processing; intent valid for the 30-day pilot.", "where": "Pilot region across CRM, document repository, screening, and case management.", "which": "New business-customer onboarding; KYC and sanctions policies; no final approval or account activation."},
        "Intent Envelope Schema": {"intent_id": "onboarding-pilot-v1", "constraints": "Collect and validate documents, create draft case, escalate exceptions; never approve, activate, change risk score, or override screening.", "success_evidence": "95% document completeness, zero unauthorized approvals, complete trace for every case.", "expiry": "30-day pilot; renew only after BAR-R evidence review.", "autonomy_ceiling": "Agent may read, validate, request documents, and draft; human approval required for decisions and state changes.", "recovery_criteria": "Pause on policy or screening uncertainty; route to Compliance; close only after human disposition and evidence capture."},
        "Capability-Readiness Map": {"capabilities": "Customer Onboarding—Operations Director; KYC and Compliance Review—Compliance Director.", "data": "Customer records, identity documents, approved KYC policy, and screening results; owners are Customer Operations and Compliance.", "systems": "CRM, document repository, sanctions screening API, and case-management system of record.", "dependencies": "Customer lookup, document upload, screening request/result, draft-case creation, Compliance review event.", "nfrs": "Four-hour business-day objective; bounded API timeouts; retry-safe reads; recoverable writes; access audit.", "readiness_gaps": "Confirm non-production API contracts, workload identity, policy decision availability, evidence retention, and support coverage before pilot."},
        "Outcome Contract Template": {"requestor": "Operations intake; receiving capability is Compliance Review.", "preconditions": "Valid customer consent, unique customer/case identifiers, approved document checklist, current intent, and screening service availability.", "policies": "KYC, sanctions, customer-data classification, retention; contract version onboarding-case-v1.", "state_model": "received → collecting → validated → draft_ready → human_review → accepted/rejected/escalated.", "completion": "Draft includes required documents, validation results, source references, and trace; Compliance records final disposition.", "failure_recovery": "Idempotent case creation; pause on uncertain screening; reconcile partial uploads; escalate exceptions to Compliance."},
        "Agent Authority Profile": {"principal": "Represented principal is the authorized Operations requester; workload identity is customer-onboarding-preparer.", "scopes": "Pilot region and new business-customer onboarding cases only.", "tools": "Read approved customer records, validate documents, request missing documents, create draft cases, call screening API.", "prohibitions": "No approval, activation, risk-rating changes, sanctions override, deletion, or unrestricted export.", "thresholds": "Human approval for all decisions/state changes; expire after 30 days; revoke on incident or policy change."},
        "Autonomy-Risk Matrix": {"impact": "High: customer eligibility and regulated KYC decision context.", "uncertainty": "Medium: document interpretation and incomplete data require uncertainty detection.", "reversibility": "Draft creation is compensatable; approval and activation are restricted to humans.", "sensitivity": "Restricted identity and financial data; minimize and redact.", "observability": "Correlated evidence required; Compliance intervention available; recovery plan tested before pilot.", "autonomy_level": "Agent-executed read/prepare; human-approved decision; no autonomous activation."},
        "Tool and Action Registry": {"registry": "customer.lookup, document.validate, document.request, screening.check, case.create_draft.", "capability_mapping": "Mapped to Customer Onboarding and KYC Review outcome contract onboarding-case-v1.", "schemas": "Validate customer_id, document_type, screening_request, correlation_id; enforce required preconditions and typed responses.", "side_effects": "Read-only lookup/check; document request sends communication; draft creation changes case state.", "ownership_version": "Operations owns workflow; Platform Engineering owns adapter; pin tool schemas and versions per release.", "risk": "Low for reads; medium for communication and draft creation; human gate for any decision action."},
        "Policy and Control Pack": {"rules": "Deny actions outside profile; require current unexpired intent; require approval for decision/state change; deny if evidence or recovery unavailable.", "decision_point": "Independent enterprise policy decision point evaluated before each tool call.", "tests": "Allow permitted read/draft; deny approve/activate/override; deny expired intent; deny missing consent or missing evidence.", "exceptions": "Screening ambiguity, policy outage, or incomplete documents pause and escalate to Compliance.", "approvals": "Authenticated Compliance approver; record approval ID and scope before transition.", "logs": "Record policy ID/version, input hash, decision, reason, principal, agent, tool, and correlation ID."},
        "Transaction and Recovery Map": {"states": "received → collecting → validated → draft_ready → human_review → accepted/rejected/escalated.", "idempotency": "Customer ID plus intent ID for case creation; deduplicate document and screening events.", "retries": "Retry safe reads up to three times with bounded backoff; no blind retry of ambiguous writes.", "compensation": "Remove duplicate draft, reconcile partial upload, and mark incomplete case for human review.", "reconciliation": "Compare CRM, document repository, screening, and case states; Compliance owns unresolved exceptions.", "terminal_states": "accepted, rejected, escalated, suspended, or recovered; never treat technical completion as business acceptance."},
        "Traceability and Evaluation Schema": {"provenance_links": "intent → plan → policy decision → tool call → case transaction → human intervention → final disposition → benefit.", "metrics": "Cycle time, document completeness, unauthorized-action rate, approval latency, intervention rate, recovery time, adoption, and cost.", "completeness": "100% material actions attributed to intent, principal, agent, policy version, tool, transaction, and outcome.", "evaluation": "Baseline current onboarding cycle time; compare pilot cohort over 30 days against 95% completeness target.", "review": "Weekly pilot review by Operations, Compliance, Architecture, and Risk; BAR-R decision at pilot end."},
        "Governance, Incident, and Realization Playbook": {"release_gates": "G0 owner/value approval; G1 readiness sign-off; G2 restricted pilot; G3 reuse/scale approval.", "monitoring": "Policy denials, trace gaps, cycle time, completeness, overrides, incidents, and user adoption.", "intervention": "Operations can pause; Compliance can revoke decision authority; platform on-call can disable adapters.", "incident_roles": "Operations incident lead, Compliance decision owner, Platform Engineering recovery owner, Risk liaison.", "realization": "Scale only if value target, adoption, reliability, trust, and residual risk justify lifecycle cost.", "retirement": "Revoke workload identity, disable tools, close active cases, retain evidence per policy, and review benefit realization."},
    },
    "subscription_revenue": {
        "Outcome Charter": {"problem": "Subscription sales, entitlement, billing, and cash collection can fragment across systems and create revenue leakage.", "owner": "VP of Revenue; Finance Controller owns financial-control approval.", "target_benefit": "Checkout conversion >8%, payment success >97%, duplicate charges <0.01%, daily reconciliation by 06:00 UTC.", "stakeholders": "Customers, Product, Sales, Billing Operations, Finance, Customer Success, Risk, Support.", "ai_rationale": "AI can guide plan selection and orchestrate exception handling; deterministic pricing, tax, payment, and ledger invariants remain in domain services.", "risk_class": "High impact because money movement, entitlements, privacy, and revenue reporting are involved."},
        "Enterprise Intent Canvas": {"why": "Create a predictable, auditable subscription revenue stream.", "what": "Sell subscriptions, activate service after confirmed payment, renew, invoice, collect, and reconcile recurring revenue.", "who": "VP Revenue owns value; customer is represented principal; Billing and Finance own money movement and accounting controls.", "when": "Self-service at any time; monthly and annual billing; intent scoped to the MVP launch.", "where": "Storefront, subscription platform, payment provider, CRM, tax service, entitlement service, and general ledger.", "which": "Plans, discounts, consent, payment method, renewal, dunning, cancellation, refunds, and reconciliation under pricing/PCI/tax policy."},
        "Intent Envelope Schema": {"intent_id": "subscription-to-cash-mvp-v1", "constraints": "No raw card data; require customer consent; honor versioned price/tax; do not activate without confirmed payment; no unapproved price changes or write-offs.", "success_evidence": "Conversion >8%, payment success >97%, reconciliation by 06:00 UTC, duplicate charges <0.01%.", "expiry": "MVP authorization expires at release boundary; reapprove for new markets, pricing models, or autonomy changes.", "autonomy_ceiling": "Agent may explain plans, create checkout, read payment status, notify, and draft adjustments; thresholds gate money movement.", "recovery_criteria": "Resolve payment/entitlement/ledger states, reconcile provider events, and verify the customer outcome before episode closure."},
        "Capability-Readiness Map": {"capabilities": "Digital Commerce, Product Catalog, Subscription Management, Payment Processing, Billing, Collections, Revenue Accounting.", "data": "Versioned catalog/prices, customer consent, payment token, tax jurisdiction, invoice and ledger events; owners Product and Finance.", "systems": "Storefront, catalog, CRM, subscription billing, payment processor, tax service, entitlement service, general ledger.", "dependencies": "Checkout, authorization/capture, subscription create, invoice, webhook, entitlement, refund, cancellation, reconciliation APIs/events.", "nfrs": "Checkout p95 <3s; payment outcome within 60s; daily close/reconciliation by 06:00 UTC; idempotent event processing.", "readiness_gaps": "Verify provider sandbox, tokenization/PCI boundary, webhook signature verification, finance mapping, outage behavior, and observability."},
        "Outcome Contract Template": {"requestor": "Customer checkout; receiving capabilities are Subscription Management and Revenue Accounting.", "preconditions": "Consent, customer identity, selected plan/version, price/currency, tax jurisdiction, payment token, and idempotency key are valid.", "policies": "Pricing, consent, PCI scope, tax, refund, collections, privacy, revenue recognition; contract subscription-to-cash-v1.", "state_model": "selected → checkout_pending → payment_authorized → captured → subscription_active → invoiced → renewed/cancelled/refunded/reconciled.", "completion": "One authorized charge, matching entitlement and invoice, provider reference recorded, and ledger reconciliation evidence available.", "failure_recovery": "Query provider before retry; handle duplicate webhooks idempotently; compensate duplicate charge; reconcile ledger/entitlement mismatch."},
        "Agent Authority Profile": {"principal": "Represented principal is authenticated customer; workload is subscription-operations-agent.", "scopes": "Customer-scoped subscription and support context; approved product/region only.", "tools": "Read catalog/status, create checkout session, send approved notices, draft cancellation/refund/adjustment request.", "prohibitions": "No raw card access, published-price changes, high-value refund, debt waiver, accounting entry, or unapproved activation.", "thresholds": "Finance approval above $250 refund, write-off, or manual adjustment; revoke on fraud/control incident."},
        "Autonomy-Risk Matrix": {"impact": "High for payment capture/refund and customer entitlement; lower for plan explanation and read-only status.", "uncertainty": "Medium for customer intent and exception classification; payment provider state can be temporarily ambiguous.", "reversibility": "Reads are reversible; captures need refund compensation; ledger entries require controlled reversal.", "sensitivity": "Restricted customer/financial information; payment token only; no raw card data.", "observability": "Provider event, order, subscription, invoice, intent, and trace IDs required; reconciliation detects drift.", "autonomy_level": "Autonomous read/assist and checkout preparation; bounded execution for confirmed low-risk operations; human approval for high-impact money movement."},
        "Tool and Action Registry": {"registry": "catalog.read, checkout.create, payment.authorize, payment.capture, subscription.activate, invoice.issue, subscription.cancel, refund.create, ledger.reconcile.", "capability_mapping": "Each operation maps to commerce/billing capability and subscription-to-cash-v1 contract.", "schemas": "Typed customer/order/plan/version/currency/consent/payment-token/idempotency inputs; signed provider webhook schemas.", "side_effects": "Reads catalog/status; checkout creates session; capture moves money; activation grants entitlement; refund and ledger actions are high impact.", "ownership_version": "Product owns catalog; Billing owns billing adapters; Finance owns ledger mapping; pin provider/API versions.", "risk": "Classify read, customer communication, entitlement change, money movement, and accounting separately; gate by risk."},
        "Policy and Control Pack": {"rules": "Deny absent consent, stale plan version, invalid price/tax, unauthorized scope, unconfirmed payment activation, raw card access, and missing evidence.", "decision_point": "Independent PDP evaluates intent, customer consent, authority, transaction state, and policy version before each side effect.", "tests": "Test duplicate capture, invalid price, missing consent, unverified webhook, refund threshold, and payment/entitlement mismatch.", "exceptions": "Fraud, disputes, tax exceptions, provider uncertainty, and ledger variance pause and route to Risk/Billing/Finance.", "approvals": "Authenticated Finance approval above $250 and for write-off/manual revenue adjustments; maintain durable approval wait state.", "logs": "Persist rule/version, decision, order/subscription/payment references, principal, agent, tool, and trace IDs without card data."},
        "Transaction and Recovery Map": {"states": "checkout_pending → authorized → captured → active → invoiced → renewed/cancelled/refunded/reconciled; failed, suspended, and review states explicit.", "idempotency": "Order ID for checkout/capture; provider event ID for webhook; unique subscription/invoice references.", "retries": "Retry idempotent reads/events; query provider on ambiguous capture before retry; bounded exponential backoff.", "compensation": "Refund duplicate capture with approval; revoke unpaid entitlement; reverse/reconcile ledger entry through Finance workflow.", "reconciliation": "Compare provider, subscription platform, entitlement, invoice, and general ledger; queue variances for owner review.", "terminal_states": "Verified active, cancelled, refunded, rejected, suspended, or reconciled; never close on provider acknowledgment alone."},
        "Traceability and Evaluation Schema": {"provenance_links": "intent → plan/price → policy → checkout/tool → provider transaction → subscription/entitlement → invoice/ledger → intervention → benefit.", "metrics": "Conversion, payment success, churn, involuntary churn, recovery rate, refunds, duplicate charge rate, variance, policy denials, intervention, trust, and cost.", "completeness": "Every material money/state event maps to customer/order/subscription/invoice/provider event, principal, agent, policy, and outcome.", "evaluation": "Compare MVP cohort with baseline; track financial and human measures through launch and review windows.", "review": "Weekly pilot evidence review; BAR-R decision after controlled pilot and at each material scope/autonomy change."},
        "Governance, Incident, and Realization Playbook": {"release_gates": "G0 legitimacy; G1 architecture readiness; G2 restricted pilot with provider sandbox evidence; G3 scale after sustained value and assurance.", "monitoring": "Conversion, payment outcomes, charge/entitlement mismatch, duplicate events, reconciliation variance, complaints, overrides, and adoption.", "intervention": "Pause money-moving tools; revoke agent identity; route unresolved charge/refund to Billing and Finance; retain customer service continuity.", "incident_roles": "Billing incident lead, Finance Controller, Product owner, Platform on-call, Risk/Privacy liaison.", "realization": "Scale only if benefit, adoption, reliability, trust, reconciliation, residual risk, and lifecycle cost remain acceptable.", "retirement": "Disable agent/tools, settle or reconcile in-flight transactions, revoke credentials, retain financial evidence, and review realized benefit."},
    },
}

_DEMO_STEP_ANSWERS = _BAR_HDAE_DEMO_ANSWERS["customer_onboarding"]
_SUBSCRIPTION_DEMO_ANSWERS = _BAR_HDAE_DEMO_ANSWERS["subscription_revenue"]


def _implementation_gates():
    gates = _wizard_state_get("hdae_gates", {})
    changed = False
    for gate_id, _title, _dependency in _IMPLEMENTATION_GATES:
        if gate_id not in gates:
            gates[gate_id] = {"status": "pending", "owner": "", "evidence": ""}
            changed = True
    if changed:
        _wizard_state_set("hdae_gates", gates)
    return gates


def _gate_summary(gates):
    complete = sum(gate.get("status") == "complete" for gate in gates.values())
    return {
        "completed": complete,
        "total": len(_IMPLEMENTATION_GATES),
        "missing": [gate_id for gate_id, _title, _dependency in _IMPLEMENTATION_GATES if gates[gate_id].get("status") != "complete"],
    }


def _load_demo_scenario(steps, scenario="customer_onboarding"):
    if scenario == "subscription_revenue":
        answer_template = _SUBSCRIPTION_DEMO_ANSWERS
        process = {
            "process_id": "subscription-to-cash",
            "name": "Subscription Sales and Revenue Collection",
            "description": "Sell subscriptions, activate service, bill recurring revenue, collect payments, and manage renewals and exceptions.",
            "domain": "Subscription commerce and finance",
            "business_outcome": "Accurate, governed subscription-to-cash operations.",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "scenario": scenario,
        }
    else:
        answer_template = _DEMO_STEP_ANSWERS
        process = {
            "process_id": "governed-customer-onboarding",
            "name": "Governed Customer Onboarding",
            "description": "Prepare customer onboarding cases for human compliance decisions.",
            "domain": "Financial services operations",
            "business_outcome": "Complete, traceable onboarding cases for compliant human review.",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "scenario": "customer_onboarding",
        }
    answers = {step["id"]: answer_template.get(step["title"], {}) for step in steps}
    gates = {}
    for gate_id, title, _dependency in _IMPLEMENTATION_GATES:
        gates[gate_id] = {
            "status": "complete" if gate_id in {"G0", "G1"} else "pending",
            "owner": "Enterprise delivery owner",
            "evidence": f"Demo design evidence: {title}" if gate_id in {"G0", "G1"} else "",
        }
    _wizard_state_set("wizard_answers", answers)
    _wizard_state_set("process_definition", process)
    _wizard_state_set("wizard_step", 0)
    _wizard_state_set("hdae_gates", gates)
    pipeline = {
        "run_id": f"hdae-{uuid.uuid4().hex[:12]}",
        "process_id": process["process_id"],
        "status": "ready",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "events": [],
        "build": None,
    }
    _record_pipeline_event(pipeline, "demo_scenario_loaded", detail={"scenario": process["scenario"], "process_id": process["process_id"]})
    _wizard_state_set("hdae_pipeline", pipeline)


def _step_fields(step):
    return _STEP_FIELDS.get(step["title"], [("configuration", _wizard_prompt(step), True)])


def _answer_complete(step, answer):
    if isinstance(answer, dict):
        return all(str(answer.get(key, "")).strip() for key, _label, required in _step_fields(step) if required)
    return bool(str(answer or "").strip())


def _answer_text(answer):
    if isinstance(answer, dict):
        return "\n".join(f"{key}: {value}" for key, value in answer.items() if str(value).strip())
    return str(answer or "")


def _load_step_guide(step_number):
    steps = _parse_architecture_steps()
    if step_number < 1 or step_number > len(steps):
        return {"file": "", "content": "No guide is available for this stage."}
    step = steps[step_number - 1]
    fields = _step_fields(step)
    blueprint = _ARCHITECTURE_BLUEPRINTS.get(step["title"], {})
    phase = _HDAE_PHASES[step["phase"] - 1]
    content = f"""# Stage {step_number}: {step['title']}

## BAR-HDAE placement
HDAE Phase {step['phase']}: {phase['name']} ({phase['bar']}).

## Purpose
{step['description']}

## Required inputs
{chr(10).join(f'- {label}' for _key, label, _required in fields)}

## Architecture deliverables
{chr(10).join(f'- {item}' for item in blueprint.get('deliverables', []))}

## Exit evidence
{chr(10).join(f'- {item}' for item in blueprint.get('validation_checks', []))}

## Risks to review
{chr(10).join(f'- {item}' for item in blueprint.get('risk_considerations', []))}
"""
    filename = f"step-{step_number:02d}-{step['id'].replace('_', '-')}.md"
    return {"file": f"generated-guides/{filename}", "content": content}


def _guide_html(content):
    rendered = []
    for line in content.splitlines():
        escaped = html.escape(line)
        if escaped.startswith("### "):
            rendered.append(f"<h4>{escaped[4:]}</h4>")
        elif escaped.startswith("## "):
            rendered.append(f"<h3>{escaped[3:]}</h3>")
        elif escaped.startswith("# "):
            rendered.append(f"<h2>{escaped[2:]}</h2>")
        elif escaped.startswith("- "):
            rendered.append(f"<li>{escaped[2:]}</li>")
        elif escaped:
            rendered.append(f"<p>{escaped}</p>")
    return "".join(rendered)


def _markdown_inline(text):
    escaped = html.escape(text, quote=True)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!_)_([^_]+)_(?!_)", r"<em>\1</em>", escaped)

    def render_link(match):
        label, target = match.group(1), html.unescape(match.group(2)).strip()
        if target.startswith(("http://", "https://", "/", "#")) or re.fullmatch(r"[A-Za-z0-9._/-]+", target):
            safe_target = html.escape(target, quote=True)
            return f'<a href="{safe_target}">{label}</a>'
        return label

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", render_link, escaped)


def _markdown_cells(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _markdown_html(content):
    lines = content.splitlines()
    output = []
    paragraph = []
    list_kind = None
    list_items = []

    def flush_paragraph():
        if paragraph:
            output.append(f'<p>{_markdown_inline(" ".join(paragraph))}</p>')
            paragraph.clear()

    def flush_list():
        nonlocal list_kind
        if list_items:
            output.append(f"<{list_kind}>" + "".join(f"<li>{_markdown_inline(item)}</li>" for item in list_items) + f"</{list_kind}>")
            list_items.clear()
        list_kind = None

    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            flush_paragraph()
            flush_list()
            index += 1
            continue

        if line.startswith("|") and index + 1 < len(lines):
            separator = _markdown_cells(lines[index + 1])
            if separator and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in separator):
                flush_paragraph()
                flush_list()
                headers = _markdown_cells(line)
                output.append("<div class=\"brief-table-wrap\"><table><thead><tr>")
                output.append("".join(f"<th>{_markdown_inline(cell)}</th>" for cell in headers))
                output.append("</tr></thead><tbody>")
                index += 2
                while index < len(lines) and lines[index].strip().startswith("|"):
                    cells = _markdown_cells(lines[index])
                    output.append("<tr>" + "".join(f"<td>{_markdown_inline(cell)}</td>" for cell in cells) + "</tr>")
                    index += 1
                output.append("</tbody></table></div>")
                continue

        heading = re.match(r"^(#{1,4})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            flush_list()
            level = len(heading.group(1))
            output.append(f"<h{level}>{_markdown_inline(heading.group(2))}</h{level}>")
            index += 1
            continue

        list_match = re.match(r"^([-*+]\s+|\d+\.\s+)(.+)$", line)
        if list_match:
            flush_paragraph()
            item_kind = "ol" if list_match.group(1)[0].isdigit() else "ul"
            if list_kind and list_kind != item_kind:
                flush_list()
            list_kind = item_kind
            list_items.append(list_match.group(2))
            index += 1
            continue

        flush_list()
        paragraph.append(line)
        index += 1

    flush_paragraph()
    flush_list()
    return "".join(output)


_ARTIFACT_DEFINITIONS = {
    "Humans: Why What Who When Where Which": ("human-intent.json", "human_intent"),
    "Intent Envelope": ("intent-envelope.json", "intent_envelope"),
    "AI Agent: Delegated Operational How": ("agent-profile.json", "agent_profile"),
    "Runtime Control Gateway": ("runtime-control.json", "runtime_control"),
    "Identity / Authority / Policy / Approval": ("authority-policy.json", "authority_policy"),
    "Business Capabilities": ("business-capability.json", "business_capability"),
    "Outcome Contracts": ("outcome-contract.json", "outcome_contract"),
    "Domain APIs / Applications / Systems of Record": ("domain-integration.json", "domain_integration"),
    "Data & Knowledge": ("data-knowledge.json", "data_knowledge"),
    "Evidence / Observability": ("evidence-observability.json", "evidence_observability"),
    "Recovery / Compensation / Intervention": ("recovery-plan.json", "recovery_plan"),
}


_ARCHITECTURE_BLUEPRINTS = {
    "Humans: Why What Who When Where Which": {
        "architecture_view": "Business context and bounded process scope",
        "deliverables": ["stakeholder map", "process boundary", "business outcome measures", "accountability model"],
        "deployment_decisions": ["pilot population", "operating geography", "business-hours and volume assumptions", "process owner"],
        "validation_checks": ["named accountable owner", "measurable outcome", "in-scope and out-of-scope activities", "affected stakeholders reviewed"],
        "risk_considerations": ["ambiguous ownership", "unbounded scope", "unmeasurable value", "unidentified impacted users"],
    },
    "Intent Envelope": {
        "architecture_view": "Versioned business intent contract passed to agents and runtime controls",
        "deliverables": ["intent schema mapping", "scope and constraint record", "success criteria", "accountability reference"],
        "deployment_decisions": ["intent identifier and versioning", "expiry and renewal", "source-of-truth location", "approval lifecycle"],
        "validation_checks": ["required intent fields populated", "success criteria are measurable", "scope and constraints are machine-checkable where possible", "owner approval recorded"],
        "risk_considerations": ["stale or replayed intent", "conflicting constraints", "missing expiry", "unreviewed changes"],
    },
    "AI Agent: Delegated Operational How": {
        "architecture_view": "Agent role and least-privilege action boundary",
        "deliverables": ["agent manifest", "tool allowlist", "prohibited-action list", "handoff and escalation policy"],
        "deployment_decisions": ["model and agent version pinning", "tool execution isolation", "prompt/config release controls", "human escalation channel"],
        "validation_checks": ["deny tests for every prohibited action", "tool input/output validation", "agent identity bound to approved profile", "fallback to human on uncertainty"],
        "risk_considerations": ["prompt injection", "tool overreach", "model drift", "unsafe autonomous retries"],
    },
    "Runtime Control Gateway": {
        "architecture_view": "Synchronous policy enforcement and evidence boundary around tool execution",
        "deliverables": ["pre-action authorization flow", "policy decision point", "approval workflow", "post-action evidence hook"],
        "deployment_decisions": ["gateway placement", "fail-open or fail-closed behavior", "timeouts and concurrency", "idempotency and replay protection"],
        "validation_checks": ["deny-by-default behavior", "policy outage behavior", "approval timeout behavior", "correlation propagation"],
        "risk_considerations": ["control bypass", "gateway outage", "duplicate state changes", "unrecorded action result"],
    },
    "Identity / Authority / Policy / Approval": {
        "architecture_view": "Identity federation, delegated authority, policy decision, and human approval model",
        "deliverables": ["principal/role mapping", "authority matrix", "policy pack binding", "approval and separation-of-duty rules"],
        "deployment_decisions": ["enterprise IdP integration", "workload identity", "policy engine", "approval system and evidence reference"],
        "validation_checks": ["least privilege verified", "prohibited actions denied", "approval thresholds tested", "identity lifecycle and revocation tested"],
        "risk_considerations": ["privilege escalation", "stale identity", "conflicting duties", "policy drift"],
    },
    "Business Capabilities": {
        "architecture_view": "Capability-to-process ownership and service dependency map",
        "deliverables": ["capability map", "capability owner register", "dependency map", "business service objectives"],
        "deployment_decisions": ["system/team ownership", "service boundaries", "support model", "capacity and availability assumptions"],
        "validation_checks": ["each critical capability has an owner", "dependencies are accepted", "service objectives are measurable", "operational support assigned"],
        "risk_considerations": ["unowned dependency", "hidden manual handoff", "capacity bottleneck", "unclear service responsibility"],
    },
    "Outcome Contracts": {
        "architecture_view": "Versioned producer/consumer contract for process outcomes and service levels",
        "deliverables": ["input/output contract", "acceptance criteria", "SLO and measurement plan", "failure and remedy definitions"],
        "deployment_decisions": ["contract versioning", "compatibility policy", "acceptance owner", "SLO alert thresholds"],
        "validation_checks": ["outputs are testable", "acceptance owner named", "failure conditions mapped to recovery", "SLOs measurable from telemetry"],
        "risk_considerations": ["unverifiable completion", "contract drift", "unowned exception", "metrics not tied to business outcome"],
    },
    "Domain APIs / Applications / Systems of Record": {
        "architecture_view": "Trust-bounded integration topology to authoritative systems",
        "deliverables": ["system context and interface inventory", "API/data mapping", "identity and secret references", "integration error contract"],
        "deployment_decisions": ["network zones", "API gateway and service identities", "secret manager paths", "idempotency and webhook verification"],
        "validation_checks": ["non-production endpoint connectivity", "schema and contract tests", "least-privilege credentials", "duplicate and timeout behavior tested"],
        "risk_considerations": ["credential exposure", "schema drift", "ambiguous write outcome", "inconsistent system-of-record state"],
    },
    "Data & Knowledge": {
        "architecture_view": "Governed data and knowledge access plane for agent context",
        "deliverables": ["source catalog", "classification and owner map", "retrieval/access rules", "freshness and retention controls"],
        "deployment_decisions": ["approved indexes and stores", "tenant/customer boundary", "redaction strategy", "data residency and retention"],
        "validation_checks": ["authorization enforced at retrieval", "sensitive data redacted", "source freshness measured", "deletion and retention workflows tested"],
        "risk_considerations": ["cross-tenant leakage", "stale knowledge", "sensitive data in prompts/logs", "unlicensed or unauthorized source"],
    },
    "Evidence / Observability": {
        "architecture_view": "Correlated business, control, and technical evidence plane",
        "deliverables": ["event taxonomy", "correlation model", "metrics/logs/traces", "audit retention and access policy"],
        "deployment_decisions": ["telemetry backend", "immutable evidence storage", "retention schedules", "alert routing and audit access"],
        "validation_checks": ["end-to-end trace reconstruction", "hash or immutability verification", "sensitive-field redaction", "retention and access tests"],
        "risk_considerations": ["missing evidence", "tampering", "PII/card data leakage", "unbounded telemetry cost"],
    },
    "Recovery / Compensation / Intervention": {
        "architecture_view": "Failure containment, compensation, and human takeover design",
        "deliverables": ["failure-mode map", "compensation runbooks", "retry/timeout policy", "human intervention and emergency-stop paths"],
        "deployment_decisions": ["retry budgets", "dead-letter handling", "pause/cancel authority", "incident ownership and escalation targets"],
        "validation_checks": ["partial failure drills", "duplicate request drills", "human takeover tested", "recovery evidence captured"],
        "risk_considerations": ["retry storm", "irreversible state change", "orphaned transaction", "unavailable intervention owner"],
    },
}


_ARTIFACT_DEFINITIONS = {
    "Outcome Charter": ("outcome-charter.json", "outcome_charter"),
    "Enterprise Intent Canvas": ("enterprise-intent-canvas.json", "enterprise_intent_canvas"),
    "Intent Envelope Schema": ("intent-envelope.json", "intent_envelope"),
    "Capability-Readiness Map": ("capability-readiness-map.json", "capability_readiness_map"),
    "Outcome Contract Template": ("outcome-contract.json", "outcome_contract"),
    "Agent Authority Profile": ("agent-authority-profile.json", "agent_authority_profile"),
    "Autonomy-Risk Matrix": ("autonomy-risk-matrix.json", "autonomy_risk_matrix"),
    "Tool and Action Registry": ("tool-action-registry.json", "tool_action_registry"),
    "Policy and Control Pack": ("policy-control-pack.json", "policy_control_pack"),
    "Transaction and Recovery Map": ("transaction-recovery-map.json", "transaction_recovery_map"),
    "Traceability and Evaluation Schema": ("traceability-evaluation-schema.json", "traceability_evaluation_schema"),
    "Governance, Incident, and Realization Playbook": ("governance-realization-playbook.json", "governance_incident_realization_playbook"),
}


_ARCHITECTURE_BLUEPRINTS = {
    "Outcome Charter": {
        "architecture_view": "BAR-B capability legitimacy and value hypothesis",
        "deliverables": ["problem and baseline statement", "benefit hypothesis and KPI owner", "stakeholder/accountability map", "AI-versus-alternative rationale"],
        "deployment_decisions": ["capability owner", "baseline data source", "pilot boundary", "risk class"],
        "validation_checks": ["baseline is evidenced", "benefit has a named owner", "stakeholders and affected parties identified", "simpler alternatives assessed"],
        "risk_considerations": ["automating low-value work", "unowned benefit", "unmeasured displacement", "unbounded stakeholder impact"],
    },
    "Enterprise Intent Canvas": {
        "architecture_view": "Human authority and responsibility allocation across why/what/who/when/where/which",
        "deliverables": ["human-readable intent record", "accountability and participant map", "scope and priority statement"],
        "deployment_decisions": ["requestor identity", "intent approver", "applicable organization/domain", "validity window"],
        "validation_checks": ["all six intent dimensions populated", "owner and affected parties identified", "purpose maps to approved outcome"],
        "risk_considerations": ["ambiguous purpose", "conflicting principals", "scope leakage", "intent interpreted beyond authority"],
    },
    "Intent Envelope Schema": {
        "architecture_view": "Machine-validatable, versioned contract that constrains one outcome episode",
        "deliverables": ["JSON Schema", "versioned intent example", "expiry and autonomy ceiling", "success and recovery criteria"],
        "deployment_decisions": ["schema registry", "signature/version trust", "expiry and renewal mechanism", "replay protection"],
        "validation_checks": ["schema validation", "expired intent denied", "constraints are enforced", "closure verifies success evidence"],
        "risk_considerations": ["stale or replayed intent", "schema drift", "missing constraints", "success criteria not observable"],
    },
    "Capability-Readiness Map": {
        "architecture_view": "BAR-A readiness across capabilities, authoritative data, systems, dependencies, and NFRs",
        "deliverables": ["capability and owner map", "data/system dependency map", "readiness gap register", "NFR and lifecycle-cost assessment"],
        "deployment_decisions": ["systems of record", "data owners and quality thresholds", "integration patterns", "availability and support targets"],
        "validation_checks": ["authoritative source confirmed", "dependencies have owners", "identity/security/observability available", "readiness gaps dispositioned"],
        "risk_considerations": ["fragmented architecture", "poor data quality", "unowned dependency", "cost or resilience constraint discovered late"],
    },
    "Outcome Contract Template": {
        "architecture_view": "Business-semantic contract that preserves domain invariants above APIs",
        "deliverables": ["request/response schema", "preconditions and policies", "state-transition model", "failure/retry/compensation clauses"],
        "deployment_decisions": ["contract versioning", "consumer/provider ownership", "compatibility policy", "SLO and acceptance owner"],
        "validation_checks": ["preconditions enforced", "postconditions measurable", "invalid transitions rejected", "failure behavior contract-tested"],
        "risk_considerations": ["semantic fragmentation", "contract drift", "hidden side effects", "retry violating domain invariants"],
    },
    "Agent Authority Profile": {
        "architecture_view": "Authenticated and revocable delegation from represented principal to agent workload",
        "deliverables": ["principal/workload identity binding", "permission and prohibition matrix", "scope/threshold/expiry", "revocation procedure"],
        "deployment_decisions": ["enterprise IdP/workload identity", "credential issuance", "tool scopes", "revocation and audit ownership"],
        "validation_checks": ["least privilege", "prohibited actions denied", "expiry and revocation work", "attribution maps action to principal and agent"],
        "risk_considerations": ["identity confusion", "excessive permissions", "stale delegation", "unattributed action"],
    },
    "Autonomy-Risk Matrix": {
        "architecture_view": "Risk-proportional decision authority based on impact, uncertainty, reversibility, sensitivity, and recoverability",
        "deliverables": ["risk classification", "autonomy ceiling", "approval thresholds", "risk acceptance record"],
        "deployment_decisions": ["human-only versus recommend/execute levels", "impact thresholds", "uncertainty escalation", "review cadence"],
        "validation_checks": ["high-impact actions escalated", "reversible actions have tested compensation", "uncertainty path tested", "authority ceiling enforced"],
        "risk_considerations": ["autonomy exceeds recovery strength", "irreversible action", "sensitive data exposure", "risk rating hides ethical/legal impact"],
    },
    "Tool and Action Registry": {
        "architecture_view": "Versioned inventory of trusted actions bound to capabilities, contracts, owners, and side effects",
        "deliverables": ["tool/action schemas", "side-effect and risk metadata", "owner/version registry", "capability and contract links"],
        "deployment_decisions": ["MCP/OpenAPI/event interfaces", "tool allowlist", "sandbox/network boundary", "version/deprecation policy"],
        "validation_checks": ["schema and precondition validation", "tool owner and version verified", "side effects declared", "unauthorized tool invocation denied"],
        "risk_considerations": ["excessive functionality", "schema drift", "unsafe tool composition", "gateway mistaken for domain authorization"],
    },
    "Policy and Control Pack": {
        "architecture_view": "Independent, complete-mediation policy evaluation with approval, exception, and evidence paths",
        "deliverables": ["policy rules and decision inputs", "PDP/P​​EP integration contract", "approval wait-state design", "negative and exception test suite"],
        "deployment_decisions": ["policy engine", "fail-closed behavior", "authenticated approver", "policy version distribution and rollback"],
        "validation_checks": ["every material action mediated", "policy outage denies state change", "approval cannot be bypassed", "decision/version recorded"],
        "risk_considerations": ["policy bypass", "stale policy", "approval spoofing", "central gateway replacing domain controls"],
    },
    "Transaction and Recovery Map": {
        "architecture_view": "Durable state-machine semantics that preserve transaction integrity through failure",
        "deliverables": ["state machine", "idempotency and retry rules", "compensation/reconciliation procedures", "pause/kill and terminal states"],
        "deployment_decisions": ["durable workflow engine", "transaction boundaries", "dead-letter/reconciliation queue", "intervention ownership"],
        "validation_checks": ["duplicate requests safe", "ambiguous writes reconciled", "partial failure compensated", "pause and human takeover tested"],
        "risk_considerations": ["double execution", "orphaned state", "retry storm", "irreversible partial completion"],
    },
    "Traceability and Evaluation Schema": {
        "architecture_view": "Evidence bridge from episode-level execution to BAR-R capability realization decisions",
        "deliverables": ["provenance/event schema", "correlation identifiers", "metric definitions and baseline", "review and retention rules"],
        "deployment_decisions": ["OpenTelemetry/provenance backend", "evidence immutability", "metric owners", "review cadence"],
        "validation_checks": ["intent-to-outcome trace reconstructable", "all actions attributable", "metrics have baselines/targets", "privacy and retention controls tested"],
        "risk_considerations": ["incomplete trace", "unverifiable benefits", "sensitive data in telemetry", "metrics incentivizing unsafe autonomy"],
    },
    "Governance, Incident, and Realization Playbook": {
        "architecture_view": "BAR lifecycle decisions informed by HDAE runtime evidence and human realization outcomes",
        "deliverables": ["G0-G3 gate procedures", "release/incident roles", "scale/hold/remediate/stop criteria", "retirement and revocation plan"],
        "deployment_decisions": ["review board/decision rights", "pilot limits", "incident commander and kill authority", "benefit review cadence"],
        "validation_checks": ["gates have evidence and accountable approvers", "pause/kill drills pass", "pilot adoption and trust measured", "retirement/revocation tested"],
        "risk_considerations": ["paper approval without operational evidence", "unsafe scale-up", "unreviewed incidents", "capability continues after value or trust erodes"],
    },
}


def _wizard_artifact(step, answer):
    filename, artifact_type = _ARTIFACT_DEFINITIONS.get(
        step["title"],
        (f"step-{step['number']:02d}.json", "architecture_step"),
    )
    process = _wizard_state_get("process_definition", {})
    architecture = _ARCHITECTURE_BLUEPRINTS.get(step["title"], {})
    decisions = answer if isinstance(answer, dict) else {"operator_input": _answer_text(answer)}
    architecture_documentation = _architecture_documentation(architecture, process, decisions, step["title"])
    return {
        "artifact_version": "1.0",
        "artifact_type": artifact_type,
        "artifact_file": filename,
        "step": step["number"],
        "architecture_node": step["id"],
        "title": step["title"],
        "description": step["description"],
        "guide_file": _load_step_guide(step["number"])["file"],
        "status": "configured" if _answer_complete(step, answer) else "draft",
        "source": "14_Architecture/HDAE_Reference_Architecture.md",
        "process": process,
        "architecture": {
            **architecture,
            "process_specific_design": {
                "business_domain": process.get("domain", ""),
                "process_name": process.get("name", ""),
                "process_description": process.get("description", ""),
                "target_business_outcome": process.get("business_outcome", ""),
            },
            "decisions_from_inputs": decisions,
            "documentation": architecture_documentation,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "configuration": {
            "prompt": _wizard_prompt(step),
            "operator_input": answer if isinstance(answer, dict) else _answer_text(answer),
        },
    }


def _solution_architecture(steps, artifacts):
    process = _wizard_state_get("process_definition", {})
    gates = _wizard_state_get("hdae_gates", {})
    return {
        "document_type": "enterprise_solution_architecture",
        "document_version": "1.0",
        "framework": "BAR-HDAE",
        "theory_status": "conceptual framework; not empirically validated",
        "status": "design_baseline_not_deployed",
        "process": process,
        "architecture_source": "14_Architecture/HDAE_Reference_Architecture.md",
        "governance_loops": {
            "outer_BAR_capability_lifecycle": ["G0_business_legitimacy", "G1_architecture_readiness", "G2_controlled_pilot", "G3_enterprise_scale"],
            "inner_HDAE_outcome_episode": ["human_intent", "bounded_agent_plan", "technology_mediation", "domain_execution", "evidence_and_recovery", "verified_outcome"],
            "evidence_bridge": "Episode evidence links intent, plan, policy, tool, transaction, intervention, outcome, and benefit to BAR-R scale/remediation/stop decisions.",
        },
        "hdae_implementation_phases": _HDAE_PHASES,
        "toolkit_artifacts": [artifact["artifact_file"] for artifact in artifacts],
        "architecture_views": {
            "c4_diagrams": ["c4-system-context.mmd", "c4-container-view.mmd"],
            "executive_brief": "executive-brief.md",
            "metrics_catalog": "11_Evaluation/Metrics_Catalog.csv",
            "maturity_model": "12_Maturity/HDAE_Maturity_Model.csv",
            "business": {
                "domain": process.get("domain", ""),
                "process_name": process.get("name", ""),
                "target_outcome": process.get("business_outcome", ""),
                "outcome_charter_artifact": "outcome-charter.json",
                "capability_artifact": "capability-readiness-map.json",
                "outcome_contract_artifact": "outcome-contract.json",
            },
            "application_and_integration": {
                "capability_readiness_artifact": "capability-readiness-map.json",
                "tool_registry_artifact": "tool-action-registry.json",
                "system_context": "Bind approved enterprise APIs and systems of record in each target environment; endpoint names and credentials are intentionally supplied during deployment configuration.",
            },
            "security_and_control": {
                "identity_authority_artifact": "agent-authority-profile.json",
                "autonomy_risk_artifact": "autonomy-risk-matrix.json",
                "policy_artifact": "policy-control-pack.json",
                "principles": ["deny by default", "least privilege", "human approval for governed high-impact actions", "no secrets in generated artifacts"],
            },
            "data_and_evidence": {
                "evidence_artifact": "traceability-evaluation-schema.json",
                "data_artifact": "capability-readiness-map.json",
                "principles": ["purpose-bound access", "data classification at source", "redaction of sensitive values", "correlated and retained evidence"],
            },
            "resilience": {
                "recovery_artifact": "transaction-recovery-map.json",
                "principles": ["idempotent state changes", "bounded retries", "explicit compensation", "human pause and intervention"],
            },
        },
        "implementation_sequence": [
            {"stage": step["number"], "name": step["title"], "artifact": artifact["artifact_file"], "status": artifact["status"]}
            for step, artifact in zip(steps, artifacts)
        ],
        "environment_promotion": [
            {"environment": "development", "entry_criteria": ["architecture reviewed", "integration sandbox configured"], "exit_criteria": ["development validation passed", "test evidence attached"]},
            {"environment": "test", "entry_criteria": ["development exit criteria met"], "exit_criteria": ["security, policy, failure, and recovery tests passed"]},
            {"environment": "staging", "entry_criteria": ["test evidence approved", "restricted authority enabled"], "exit_criteria": ["pilot acceptance and operational readiness approved"]},
            {"environment": "production", "entry_criteria": ["change approval recorded", "rollback and intervention owners assigned"], "exit_criteria": ["post-deployment checks and monitoring active"]},
        ],
        "implementation_gate_status": gates,
        "deployment_boundary": "This package describes target architecture and configuration intent. It does not provision infrastructure, create IAM identities, or connect external systems.",
    }


def _implementation_plan(steps, artifacts):
    process = _wizard_state_get("process_definition", {})
    return {
        "document_type": "implementation_plan",
        "framework": "BAR-HDAE",
        "theory_status": "conceptual framework; not empirically validated",
        "process_id": process.get("process_id", ""),
        "process_name": process.get("name", ""),
        "work_items": [
            {
                "sequence": step["number"],
                "work_item": step["title"],
                "artifact": artifact["artifact_file"],
                "status": artifact["status"],
                "hdae_phase_number": step["phase"],
                "hdae_phase": _HDAE_PHASES[step["phase"] - 1],
                "architecture_deliverables": artifact["architecture"]["documentation"].get("Architecture Deliverables", []),
                "deployment_decisions": artifact["architecture"]["documentation"].get("Deployment Decisions", []),
                "validation_checks": artifact["architecture"]["documentation"].get("Validation Checks", []),
                "risk_considerations": artifact["architecture"]["documentation"].get("Risk Considerations", []),
            }
            for step, artifact in zip(steps, artifacts)
        ],
        "bar_evidence_gates": [
            {
                "gate": gate_id,
                "decision": title,
                "evidence_required": criteria,
                "status": _wizard_state_get("hdae_gates", {}).get(gate_id, {}).get("status", "pending"),
                "owner": _wizard_state_get("hdae_gates", {}).get(gate_id, {}).get("owner", ""),
                "evidence_reference": _wizard_state_get("hdae_gates", {}).get(gate_id, {}).get("evidence", ""),
            }
            for gate_id, title, criteria in _IMPLEMENTATION_GATES
        ],
        "required_environment_path": ["development", "test", "staging", "production"],
        "hdae_phases": _HDAE_PHASES,
        "current_gate_state": _wizard_state_get("hdae_gates", {}),
        "change_control": "Require named owner, review evidence, approval reference, and rollback plan before production promotion.",
    }


def _artifact_href(filename):
    return f"/process/artifact/{filename}"


def _artifact_link(filename, label=None):
    safe_filename = html.escape(filename, quote=True)
    safe_label = html.escape(label or filename)
    return f'<a href="{_artifact_href(filename)}">{safe_label}</a>'


def _architecture_documentation(architecture, process, configured, stage_title):
    if not isinstance(configured, dict):
        configured = {"operator_input": configured}
    input_summary = "; ".join(
        f"{str(key).replace('_', ' ').title()}: {value}"
        for key, value in configured.items()
        if str(value).strip()
    ) or str(process.get("business_outcome", "Process-specific input is not yet configured."))
    process_name = process.get("name", "the process")
    policies = configured.get("policies") or configured.get("constraints") or "Use the approved enterprise policies and constraints captured for this process."
    recovery = configured.get("compensation") or configured.get("retry") or "Use the process recovery plan and route unresolved cases to the accountable human owner."

    sections = {
        "deliverables": {
            "name": "Architecture Deliverables",
            "purpose": "Defines the concrete design output required to implement and review this stage.",
            "action": f"Create or update this deliverable for {process_name}. Include its owner, version, interfaces, dependencies, and how it connects to the {stage_title.lower()} stage.",
            "evidence": "Keep the approved version, reviewer, approval reference, and repository location with the implementation record.",
        },
        "deployment_decisions": {
            "name": "Deployment Decisions",
            "purpose": "Turns the design into explicit configuration choices for target environments.",
            "action": f"Record the selected option, target environment, accountable team, dependency, configuration or secret reference, and fallback. Apply the choice to {process_name}; never put secret values in this document.",
            "evidence": "Link an approved architecture decision record or environment configuration, with development/test values and production owner identified.",
        },
        "validation_checks": {
            "name": "Validation Checks",
            "purpose": "Defines objective acceptance checks so completion is demonstrated, not assumed.",
            "action": "For each check, specify the test case, preconditions, expected result, environment, owner, and pass/fail rule. A check without a recorded result is incomplete.",
            "evidence": "Retain test/run ID, timestamp, outcome, trace or evidence reference, defect link if applicable, and reviewer sign-off.",
        },
        "risk_considerations": {
            "name": "Risk Considerations",
            "purpose": "Explains how this stage can fail or cause security, operational, financial, or business harm.",
            "action": f"For each risk, assign likelihood and impact, preventive control, detection signal, response owner, and residual-risk decision. Coordinate mitigation with this process recovery guidance: {recovery} Relevant policy/constraints: {policies}",
            "evidence": "Maintain a risk-register reference, mitigation due date, owner, test evidence, and accepted/mitigated status.",
        },
    }

    documentation = {}
    for source_key, template in sections.items():
        entries = []
        for item in architecture.get(source_key, []):
            entries.append({
                "title": str(item),
                "purpose": template["purpose"],
                "process_context": input_summary,
                "implementation_guidance": template["action"],
                "acceptance_evidence": template["evidence"],
            })
        documentation[template["name"]] = entries
    return documentation


def _documentation_entries_html(entries):
    cards = []
    for entry in entries:
        if isinstance(entry, dict):
            cards.append(
                f'<article class="work-doc"><h4>{html.escape(str(entry.get("title", "")))}</h4>'
                f'<p><strong>Purpose:</strong> {html.escape(str(entry.get("purpose", "")))}</p>'
                f'<p><strong>Implementation:</strong> {html.escape(str(entry.get("implementation_guidance", "")))}</p>'
                f'<p><strong>Evidence:</strong> {html.escape(str(entry.get("acceptance_evidence", "")))}</p></article>'
            )
        else:
            cards.append(f"<li>{html.escape(str(entry))}</li>")
    return "".join(cards)


def _artifact_report_html(artifact):
    configuration = artifact.get("configuration", {})
    architecture = artifact.get("architecture", {})
    documentation = architecture.get("documentation", {})
    operator_input = configuration.get("operator_input", {})
    if isinstance(operator_input, dict):
        input_rows = "".join(
            f"<tr><th>{html.escape(str(key).replace('_', ' ').title())}</th><td>{html.escape(str(value))}</td></tr>"
            for key, value in operator_input.items()
        )
    else:
        input_rows = f"<tr><th>Operator input</th><td>{html.escape(str(operator_input))}</td></tr>"

    def documentation_panel(title):
        entries = documentation.get(title, [])
        if not entries:
            return ""
        cards = "".join(
            f'<article class="detail-item"><h3>{html.escape(str(entry.get("title", "")))}</h3>'
            f'<p><strong>Purpose</strong><br>{html.escape(str(entry.get("purpose", "")))}</p>'
            f'<p><strong>Process-specific inputs</strong><br>{html.escape(str(entry.get("process_context", "")))}</p>'
            f'<p><strong>Implementation guidance</strong><br>{html.escape(str(entry.get("implementation_guidance", "")))}</p>'
            f'<p><strong>Acceptance and evidence</strong><br>{html.escape(str(entry.get("acceptance_evidence", "")))}</p></article>'
            for entry in entries
        )
        return f'<section class="artifact-section"><h2>{html.escape(title)}</h2><div class="detail-list">{cards}</div></section>'

    return f"""
        <style>
            .artifact-summary {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:10px; margin:18px 0; }}
            .artifact-summary > div,.detail-item {{ padding:14px; border:1px solid #dbe4f0; background:#f8fafc; border-radius:6px; }}
            .artifact-summary .label {{ display:block; margin-bottom:6px; }}
            .artifact-section {{ margin-top:26px; }}
            .artifact-section h2 {{ color:#123f67; border-bottom:1px solid #dbe4f0; padding-bottom:8px; }}
            .detail-list {{ display:grid; gap:12px; }}
            .detail-item h3 {{ margin:0 0 10px; color:#123f67; font-size:17px; }}
            .detail-item p {{ margin:8px 0; color:#334155; line-height:1.55; }}
            .artifact-inputs {{ width:100%; border-collapse:collapse; margin-top:14px; }}
            .artifact-inputs th,.artifact-inputs td {{ border:1px solid #dbe4f0; padding:9px 11px; text-align:left; vertical-align:top; }}
            .artifact-inputs th {{ width:230px; background:#eef6fa; }}
            .artifact-actions {{ display:flex; gap:8px; flex-wrap:wrap; }}
        </style>
        <header class="header-row">
            <div><div class="label">Stage {artifact.get('step', '')} · {html.escape(str(artifact.get('artifact_type', 'process artifact')))}</div><h1>{html.escape(str(artifact.get('title', 'Process Artifact')))}</h1><p>{html.escape(str(artifact.get('description', '')))}</p></div>
            <nav class="artifact-actions"><a class="button-link" href="/wizard">Process builder</a><a class="button-link" href="/process/deliverables">Architecture reports</a></nav>
        </header>
        <div class="artifact-summary">
            <div><span class="label">Process</span><strong>{html.escape(str(artifact.get('process', {}).get('name', 'Not defined')))}</strong></div>
            <div><span class="label">Status</span><strong>{html.escape(str(artifact.get('status', 'draft')).title())}</strong></div>
            <div><span class="label">Artifact</span><strong>{html.escape(str(artifact.get('artifact_file', '')))}</strong></div>
            <div><span class="label">Architecture node</span><strong>{html.escape(str(artifact.get('architecture_node', '')))}</strong></div>
        </div>
        <section class="report-section"><h2>Configured Values</h2><div class="table-wrap"><table class="artifact-inputs"><tbody>{input_rows}</tbody></table></div></section>
        {documentation_panel("Architecture Deliverables")}
        {documentation_panel("Deployment Decisions")}
        {documentation_panel("Validation Checks")}
        {documentation_panel("Risk Considerations")}
        <p style="margin-top:20px;"><a href="{_artifact_href(str(artifact.get('artifact_file', '')))}?format=json">View raw JSON</a> · <a href="{_artifact_href(str(artifact.get('artifact_file', '')))}?download=1">Download JSON</a></p>
    """


def _clean_diagram_label(value, fallback):
    value = str(value or fallback).replace('"', "'").replace("\n", " ").strip()
    return value[:160] or fallback


def _format_system_label(value):
    label = _clean_diagram_label(value, "Enterprise system").title()
    for acronym in ("API", "CRM", "ERP", "IAM", "POS", "SSO", "KYC", "PCI", "SaaS"):
        label = re.sub(rf"\b{acronym.title()}\b", acronym, label)
    return label


def _answer_field(steps, answers, step_title, field, fallback="Not specified"):
    aliases = {
        ("Humans: Why What Who When Where Which", "why"): ("Outcome Charter", "problem"),
        ("Humans: Why What Who When Where Which", "what"): ("Enterprise Intent Canvas", "what"),
        ("Humans: Why What Who When Where Which", "who"): ("Outcome Charter", "owner"),
        ("Humans: Why What Who When Where Which", "when"): ("Enterprise Intent Canvas", "when"),
        ("Humans: Why What Who When Where Which", "where"): ("Enterprise Intent Canvas", "where"),
        ("Humans: Why What Who When Where Which", "which"): ("Enterprise Intent Canvas", "which"),
        ("Intent Envelope", "purpose"): ("Outcome Charter", "problem"),
        ("Intent Envelope", "outcome"): ("Enterprise Intent Canvas", "what"),
        ("Intent Envelope", "success_criteria"): ("Intent Envelope Schema", "success_evidence"),
        ("Intent Envelope", "scope"): ("Enterprise Intent Canvas", "which"),
        ("Intent Envelope", "constraints"): ("Intent Envelope Schema", "constraints"),
        ("Intent Envelope", "timing"): ("Enterprise Intent Canvas", "when"),
        ("Intent Envelope", "accountability"): ("Outcome Charter", "owner"),
        ("AI Agent: Delegated Operational How", "agent_id"): ("Agent Authority Profile", "principal"),
        ("AI Agent: Delegated Operational How", "responsibilities"): ("Tool and Action Registry", "registry"),
        ("AI Agent: Delegated Operational How", "allowed_actions"): ("Agent Authority Profile", "tools"),
        ("AI Agent: Delegated Operational How", "prohibited_actions"): ("Agent Authority Profile", "prohibitions"),
        ("AI Agent: Delegated Operational How", "escalation"): ("Governance, Incident, and Realization Playbook", "intervention"),
        ("Runtime Control Gateway", "controls"): ("Policy and Control Pack", "rules"),
        ("Runtime Control Gateway", "authorization"): ("Policy and Control Pack", "decision_point"),
        ("Runtime Control Gateway", "approvals"): ("Policy and Control Pack", "approvals"),
        ("Runtime Control Gateway", "execution"): ("Transaction and Recovery Map", "idempotency"),
        ("Identity / Authority / Policy / Approval", "principals"): ("Agent Authority Profile", "principal"),
        ("Identity / Authority / Policy / Approval", "authority"): ("Agent Authority Profile", "scopes"),
        ("Identity / Authority / Policy / Approval", "policies"): ("Policy and Control Pack", "rules"),
        ("Identity / Authority / Policy / Approval", "risk"): ("Autonomy-Risk Matrix", "autonomy_level"),
        ("Business Capabilities", "capabilities"): ("Capability-Readiness Map", "capabilities"),
        ("Business Capabilities", "owners"): ("Capability-Readiness Map", "capabilities"),
        ("Business Capabilities", "dependencies"): ("Capability-Readiness Map", "dependencies"),
        ("Outcome Contracts", "inputs"): ("Outcome Contract Template", "preconditions"),
        ("Outcome Contracts", "outputs"): ("Outcome Contract Template", "completion"),
        ("Outcome Contracts", "acceptance"): ("Outcome Contract Template", "completion"),
        ("Outcome Contracts", "service_levels"): ("Traceability and Evaluation Schema", "metrics"),
        ("Outcome Contracts", "failure_conditions"): ("Outcome Contract Template", "failure_recovery"),
        ("Domain APIs / Applications / Systems of Record", "systems"): ("Capability-Readiness Map", "systems"),
        ("Domain APIs / Applications / Systems of Record", "apis"): ("Capability-Readiness Map", "dependencies"),
        ("Data & Knowledge", "sources"): ("Capability-Readiness Map", "data"),
        ("Data & Knowledge", "access"): ("Capability-Readiness Map", "data"),
        ("Evidence / Observability", "events"): ("Traceability and Evaluation Schema", "provenance_links"),
        ("Evidence / Observability", "metrics"): ("Traceability and Evaluation Schema", "metrics"),
        ("Recovery / Compensation / Intervention", "failure_modes"): ("Transaction and Recovery Map", "states"),
        ("Recovery / Compensation / Intervention", "compensation"): ("Transaction and Recovery Map", "compensation"),
        ("Recovery / Compensation / Intervention", "escalation"): ("Governance, Incident, and Realization Playbook", "incident_roles"),
        ("Recovery / Compensation / Intervention", "retry"): ("Transaction and Recovery Map", "retries"),
    }
    target_title, target_field = aliases.get((step_title, field), (step_title, field))
    step = next((item for item in steps if item["title"] == target_title), None)
    if step is None:
        return fallback
    value = answers.get(step["id"], {})
    if isinstance(value, dict):
        return str(value.get(target_field) or fallback)
    return str(value or fallback)


def _process_systems(steps, answers):
    raw = _answer_field(
        steps,
        answers,
        "Domain APIs / Applications / Systems of Record",
        "systems",
        "Enterprise systems of record",
    )
    systems = re.split(r"[,;\n]|\band\b", raw)
    systems = [_format_system_label(item) for item in systems if item.strip()]
    return systems[:10] or ["Enterprise systems of record"]


def _process_deliverables(steps, artifacts):
    process = _wizard_state_get("process_definition", {})
    answers = _wizard_state_get("wizard_answers", {})
    process_name = _clean_diagram_label(process.get("name"), "Business Process")
    domain = _clean_diagram_label(process.get("domain"), "Business domain")
    outcome = _clean_diagram_label(process.get("business_outcome"), "Governed business outcome")
    owner = _clean_diagram_label(_answer_field(steps, answers, "Humans: Why What Who When Where Which", "who", "Process owner"), "Process owner")
    customer = _clean_diagram_label(_answer_field(steps, answers, "Humans: Why What Who When Where Which", "which", "Process participants"), "Process participants")
    agent_id = _clean_diagram_label(_answer_field(steps, answers, "AI Agent: Delegated Operational How", "agent_id", "Process Agent"), "Process Agent")
    systems = _process_systems(steps, answers)

    def diagram_label(value, fallback, max_chars=28):
        safe_value = _clean_diagram_label(value, fallback)
        safe_value = re.sub(r"[\[\]{}()|]", " ", safe_value)
        words = safe_value.split()
        lines = []
        line = ""
        for word in words:
            if line and len(line) + len(word) + 1 > max_chars:
                lines.append(line)
                line = word
            else:
                line = f"{line} {word}".strip()
        if line:
            lines.append(line)
        return "<br/>".join(html.escape(part, quote=True) for part in lines[:3]) or fallback

    process_label = diagram_label(process_name, "Business Process", 24)
    owner_label = diagram_label(owner, "Process owner", 24)
    user_label = diagram_label(customer, "Process participants", 24)
    agent_label = diagram_label(agent_id, "Process Agent", 24)
    system_nodes = [
        f'    sys{index}["{diagram_label(name, "Enterprise System", 22)}"]'
        for index, name in enumerate(systems, 1)
    ]
    context_links = [f"  processSystem -->|governed interaction| sys{index}" for index in range(1, len(systems) + 1)]
    c4_context = "\n".join([
        "---",
        f'title: "C4 System Context - {process_name}"',
        "---",
        "flowchart TB",
        "  subgraph actors[\"People and organizations\"]",
        "    direction LR",
        f'    owner(["Business owner<br/>{owner_label}"])',
        f'    participants(["Process participants<br/>{user_label}"])',
        "  end",
        f'  processSystem["{process_label}<br/>HDAE governed process<br/>Outcome: {diagram_label(outcome, "Business outcome", 34)}"]',
        '  barLifecycle["BAR capability lifecycle<br/>G0 legitimacy · G1 readiness<br/>G2 pilot · G3 scale"]',
        "  subgraph externalSystems[\"External systems and systems of record\"]",
        "    direction TB",
        *system_nodes,
        "  end",
        "  owner -->|defines value and authority| barLifecycle",
        "  barLifecycle -->|approved capability and autonomy ceiling| processSystem",
        "  processSystem -.->|episode evidence informs hold, remediate, scale, or stop| barLifecycle",
        "  owner -->|defines episode intent| processSystem",
        "  participants -->|initiates or participates| processSystem",
        *context_links,
        "  classDef person fill:#eaf3fb,stroke:#17608c,stroke-width:2px,color:#12324a",
        "  classDef hdae fill:#e4f5f6,stroke:#087e8b,stroke-width:2px,color:#073b4c",
        "  classDef external fill:#f4f6f8,stroke:#607080,stroke-width:1.5px,color:#263746",
        "  class owner,participants person",
        "  class processSystem,barLifecycle hdae",
        "  class " + ",".join(f"sys{index}" for index in range(1, len(systems) + 1)) + " external",
    ])

    container_systems = [
        f'    ext{index}["{diagram_label(name, "Enterprise System", 20)}"]'
        for index, name in enumerate(systems, 1)
    ]
    integration_links = [f"  integration -->|governed API| ext{index}" for index in range(1, len(systems) + 1)]
    c4_containers = "\n".join([
        "---",
        f'title: "C4 Container View - {process_name}"',
        "---",
        "flowchart TB",
        '  owner(["Business owner"]) --> portal["HDAE process portal<br/>Intent · design · approvals"]',
        '  subgraph runtime["HDAE runtime boundary"]',
        "    direction TB",
        f'    portal --> agent["Agent runtime<br/>{agent_label}"] --> gateway["Control gateway<br/>Authorize · enforce · audit"]',
        '    gateway --> policy["Identity and policy adapter"]',
        '    gateway --> integration["Domain integration adapter"]',
        '    agent --> knowledge["Governed data and knowledge"]',
        '    gateway --> evidence["Evidence and telemetry"]',
        '    gateway --> recovery["Recovery coordinator<br/>Retry · compensate · pause"]',
        "  end",
        "  subgraph external[\"External systems and systems of record\"]",
        "    direction TB",
        *container_systems,
        "  end",
        '  barReview["BAR lifecycle review<br/>G0 · G1 · G2 · G3<br/>Scale · hold · remediate · stop"]',
        *integration_links,
        "  evidence -.->|trace, outcome, adoption, benefit| barReview",
        "  barReview -.->|approved purpose, readiness, autonomy limits| portal",
        "  classDef person fill:#eaf3fb,stroke:#17608c,stroke-width:2px,color:#12324a",
        "  classDef app fill:#e4f5f6,stroke:#087e8b,stroke-width:2px,color:#073b4c",
        "  classDef external fill:#f4f6f8,stroke:#607080,stroke-width:1.5px,color:#263746",
        "  classDef lifecycle fill:#fff4df,stroke:#a66a00,stroke-width:2px,color:#5c3a00",
        "  class owner person",
        "  class portal,agent,gateway,policy,integration,knowledge,evidence,recovery app",
        "  class " + ",".join(f"ext{index}" for index in range(1, len(systems) + 1)) + " external",
        "  class barReview lifecycle",
    ])

    intent_why = _answer_field(steps, answers, "Humans: Why What Who When Where Which", "why")
    intent_what = _answer_field(steps, answers, "Humans: Why What Who When Where Which", "what", outcome)
    intent_when = _answer_field(steps, answers, "Humans: Why What Who When Where Which", "when")
    intent_where = _answer_field(steps, answers, "Humans: Why What Who When Where Which", "where", ", ".join(systems))
    intent_which = _answer_field(steps, answers, "Humans: Why What Who When Where Which", "which")
    success = _answer_field(steps, answers, "Intent Envelope", "success_criteria")
    scope = _answer_field(steps, answers, "Intent Envelope", "scope", intent_which)
    constraints = _answer_field(steps, answers, "Intent Envelope", "constraints")
    timing = _answer_field(steps, answers, "Intent Envelope", "timing", intent_when)
    accountability = _answer_field(steps, answers, "Intent Envelope", "accountability", owner)
    agent_controls = _answer_field(steps, answers, "AI Agent: Delegated Operational How", "prohibited_actions")
    policies = _answer_field(steps, answers, "Identity / Authority / Policy / Approval", "policies")
    integration_apis = _answer_field(steps, answers, "Domain APIs / Applications / Systems of Record", "apis")
    evidence = _answer_field(steps, answers, "Evidence / Observability", "events")
    metrics = _answer_field(steps, answers, "Evidence / Observability", "metrics")
    risks = _answer_field(steps, answers, "Recovery / Compensation / Intervention", "failure_modes")
    mitigation = _answer_field(steps, answers, "Recovery / Compensation / Intervention", "compensation")
    recovery = _answer_field(steps, answers, "Recovery / Compensation / Intervention", "retry")
    capabilities = _answer_field(steps, answers, "Business Capabilities", "capabilities")
    service_levels = _answer_field(steps, answers, "Outcome Contracts", "service_levels")
    gate_state = _wizard_state_get("hdae_gates", {})
    gate_status_rows = "\n".join(
        f"| {gate_id} {title} | {gate_state.get(gate_id, {}).get('status', 'pending')} | {gate_state.get(gate_id, {}).get('evidence', 'Evidence not yet recorded')} |"
        for gate_id, title, _criteria in _IMPLEMENTATION_GATES
    )
    executive_brief = f"""# Executive Brief - HDAE {process_name}

_{domain} | Generated {datetime.now(timezone.utc).date().isoformat()} | Conceptual framework; not empirically validated | Design baseline, not deployed_

## 1. Executive Summary

- **Business driver:** {intent_why}
- **Target outcome:** {outcome}
- **Operating model:** {intent_what}
- **Accountable owner:** {accountability}
- **HDAE value:** Governed automation with explicit authority, policy enforcement, traceable outcomes, and recovery.

## 2. Business Outcome and Scope

- **Scope:** {scope}
- **Participants / process population:** {intent_which}
- **Operating context:** {intent_where}
- **Timing:** {timing}
- **Success criteria:** {success}
- **Constraints:** {constraints}

## 3. Human Intent Snapshot

| Dimension | Process definition |
| --- | --- |
| Why | {intent_why} |
| What | {intent_what} |
| Who | {owner} |
| When | {intent_when} |
| Where | {intent_where} |
| Which | {intent_which} |

## 4. BAR-HDAE Dual-Loop Governance Model

**Outer BAR capability lifecycle:** BAR-B establishes legitimacy and intended value; BAR-A assesses readiness and integration; BAR-R governs responsible adoption, realization, and scale/hold/remediate/stop decisions.

**Inner HDAE outcome episode:** Human intent is captured in a versioned envelope. The **{agent_id}** proposes a bounded plan; technology independently mediates identity, authority, policy, contract, schema, approval, and transaction checks before domain systems act. Evidence links intent, plan, decision, tool call, transaction, intervention, outcome, and benefit back to BAR-R.

The BAR gates are non-compensatory evidence gates; a strong value case cannot offset a critical architecture or responsibility failure.

| BAR gate | Decision | Current state | Evidence reference |
| --- | --- | --- | --- |
{gate_status_rows}

**Business capabilities:** {capabilities}

## 5. Core Enterprise Systems

{chr(10).join(f'- {system}' for system in systems)}

**Integration operations:** {integration_apis}

## 6. Key Governance Controls

- **Policy baseline:** {policies}
- **Agent prohibited actions:** {agent_controls}
- **Evidence events:** {evidence}
- **Service objectives:** {service_levels}
- **Required measures:** {metrics}
- **Security baseline:** least privilege, managed workload identity, no secrets in generated artifacts, and sensitive-data minimization.

## 7. Risks and Mitigations

| Risk / failure mode | Planned mitigation / response |
| --- | --- |
| {risks} | {mitigation} |
| Uncertain or repeated state-changing operation | {recovery} |
| Policy, identity, or approval service unavailable | Fail closed for governed writes; pause execution and route to the named human owner. |
| Data exposure or incomplete audit evidence | Enforce source authorization, redact sensitive telemetry, and block promotion until evidence checks pass. |

## 8. KPI Targets

- **Business success criteria:** {success}
- **Service level:** {service_levels}
- **Operational measures:** {metrics}

Targets not supplied as numeric measures remain design inputs and must be agreed by the accountable process owner before pilot approval.

## 9. Executive Recommendation

1. Approve a bounded MVP scope, process owner, outcome contract, and prohibited-action boundary.
2. Implement in development with sandbox integrations, deny tests, idempotency, and complete evidence capture.
3. Run security, policy, outage, duplicate, partial-failure, and recovery tests before a restricted pilot.
4. Promote through test, staging, and production only with named approvals, rollback ownership, and operational monitoring.

## 10. Implementation Priority

| HDAE phase | BAR responsibility | Focus | Exit evidence |
| --- | --- | --- | --- |
| 1. Scope outcome episode | BAR-B | Outcome Charter, baseline, owner, value, scope, and risk class. | G0 legitimacy evidence |
| 2. Model Intent Envelope | BAR-B + HDAE | Human intent canvas and machine-validatable intent, expiry, constraints, success/recovery criteria. | Valid envelope and owner review |
| 3. Map capabilities and contracts | BAR-A + HDAE | Capability readiness, system boundaries, domain invariants, and outcome contracts. | G1 readiness evidence |
| 4. Design delegation and autonomy | BAR-R + HDAE | Authority profile, autonomy-risk fit, permissions, prohibitions, expiry, and revocation. | Deny, approval, and revocation tests |
| 5. Assemble agent toolchain | BAR-A + HDAE | Tool/action registry, schemas, independent policy decision point, approvals, durable handoff. | Complete mediation tests |
| 6. Engineer integrity and evidence | BAR-A/R + HDAE | Idempotency, recovery, compensation, traceability, intervention, and telemetry. | Failure drills and complete traces |
| 7. Validate, learn, and scale | BAR-B/R + HDAE | Controlled pilot, metric review, adoption, trust, realized benefits, residual risk. | G2 pilot decision; G3 scale/hold/remediate/stop decision |

## Architecture Deliverables

- [C4 System Context](c4-system-context.mmd)
- [C4 Container View](c4-container-view.mmd)
- [Enterprise Solution Architecture](/process/enterprise-solution-architecture.json)
- [Implementation Plan](/process/implementation-plan.json)

_Generated from the active HDAE process definition and wizard answers. Validate all values, targets, policies, system boundaries, and approvals with enterprise owners before implementation._
"""
    return {
        "c4_system_context": c4_context,
        "c4_container_view": c4_containers,
        "executive_brief": executive_brief,
    }


def _pipeline_state():
    state = _wizard_state_get("hdae_pipeline")
    if state:
        return state
    state = {
        "run_id": f"hdae-{uuid.uuid4().hex[:12]}",
        "status": "draft",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "events": [],
        "build": None,
    }
    _wizard_state_set("hdae_pipeline", state)
    return state


def _record_pipeline_event(state, event_type, step=None, detail=None):
    state["events"].append({
        "event_id": uuid.uuid4().hex,
        "event_type": event_type,
        "step": step,
        "detail": detail or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    state["updated_at"] = datetime.now(timezone.utc).isoformat()


def _pipeline_summary(steps, answers, state):
    configured = sum(_answer_complete(step, answers.get(step["id"], "")) for step in steps)
    missing = [step["number"] for step in steps if not _answer_complete(step, answers.get(step["id"], ""))]
    gates = _implementation_gates()
    gate_summary = _gate_summary(gates)
    prebuild_gates_missing = [gate_id for gate_id in ("G0", "G1") if gates.get(gate_id, {}).get("status") != "complete"]
    if missing or prebuild_gates_missing:
        state["status"] = "draft"
    elif state.get("build"):
        if gates.get("G3", {}).get("status") == "complete":
            state["status"] = "scaled"
        elif gates.get("G2", {}).get("status") == "complete":
            state["status"] = "pilot"
        else:
            state["status"] = "built"
    else:
        state["status"] = "ready"
    return {
        "run_id": state["run_id"],
        "status": state["status"],
        "configured_steps": configured,
        "total_steps": len(steps),
        "missing_steps": missing,
        "gates": gate_summary,
        "prebuild_gates_missing": prebuild_gates_missing,
        "bar_phase": "scale" if gates.get("G3", {}).get("status") == "complete" else "pilot" if gates.get("G2", {}).get("status") == "complete" else "readiness" if not prebuild_gates_missing else "legitimacy",
        "gate_details": gates,
        "event_count": len(state["events"]),
        "build": state.get("build"),
    }


def _nav(active_page: str):
    items = [
        ("dashboard", "Dashboard"),
        ("toolkit", "Toolkit"),
        ("wizard", "Wizard"),
        ("framework", "BAR-HDAE Model"),
        ("measurement", "Measures & Maturity"),
        ("governance", "Governance"),
        ("evidence", "Evidence"),
        ("policy", "Policy")
    ]
    links = []
    for key, label in items:
        cls = 'active' if key == active_page else ''
        links.append(f'<a class="{cls}" href="/{key}">{label}</a>')
    return "".join(links)


def _page_shell(title: str, active_page: str, body: str):
    return render_template_string(
        """
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>{{ title }}</title>
            <style>
                :root {
                    --bg: #f3f6fb;
                    --card: #ffffff;
                    --line: #dbe4f0;
                    --primary: #1d4ed8;
                    --primary-soft: #dfe9ff;
                    --success: #166534;
                    --success-soft: #dcfce7;
                    --text: #172033;
                    --muted: #48556c;
                    --sidebar: #0f172a;
                    --sidebar-text: #dfe9ff;
                }
                * { box-sizing: border-box; }
                body {
                    margin: 0;
                    font-family: Arial, Helvetica, sans-serif;
                    background: var(--bg);
                    color: var(--text);
                }
                .app-shell {
                    display: flex;
                    min-height: 100vh;
                }
                .sidebar {
                    width: 260px;
                    background: var(--sidebar);
                    color: var(--sidebar-text);
                    padding: 24px 18px;
                }
                .brand {
                    font-size: 1.6rem;
                    font-weight: 700;
                    margin-bottom: 24px;
                }
                .nav a {
                    display: block;
                    text-decoration: none;
                    color: var(--sidebar-text);
                    padding: 12px 14px;
                    border-radius: 10px;
                    margin-bottom: 8px;
                    background: rgba(255,255,255,0.02);
                }
                .nav a.active, .nav a:hover {
                    background: rgba(147, 197, 253, 0.25);
                    border-left: 3px solid #93c5fd;
                }
                .sidebar .meta {
                    margin-top: 30px;
                    padding-top: 16px;
                    border-top: 1px solid rgba(255,255,255,0.16);
                    color: #cbd5e1;
                    font-size: 0.9rem;
                }
                .content {
                    flex: 1;
                    padding: 28px;
                }
                .page-card {
                    background: var(--card);
                    border: 1px solid var(--line);
                    border-radius: 16px;
                    padding: 24px;
                    box-shadow: 0 8px 18px rgba(15, 23, 42, 0.04);
                }
                .header-row {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    gap: 16px;
                    margin-bottom: 20px;
                }
                h1, h2, h3 { margin-top: 0; }
                .pill {
                    display: inline-block;
                    padding: 6px 12px;
                    border-radius: 999px;
                    background: var(--success-soft);
                    color: var(--success);
                    font-size: 12px;
                    font-weight: 700;
                }
                .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }
                .stat {
                    background: var(--primary-soft);
                    border-radius: 12px;
                    padding: 16px;
                }
                .label {
                    text-transform: uppercase;
                    letter-spacing: 0.08em;
                    color: var(--muted);
                    font-size: 12px;
                    font-weight: 700;
                }
                .value { margin-top: 8px; font-size: 28px; font-weight: 700; }
                .list { margin: 0; padding-left: 18px; color: var(--muted); }
                form {
                    display: grid;
                    gap: 12px;
                    max-width: 420px;
                }
                input, select, button {
                    width: 100%;
                    padding: 12px 14px;
                    border-radius: 10px;
                    border: 1px solid var(--line);
                    font-size: 14px;
                }
                button {
                    background: var(--primary);
                    color: white;
                    border: none;
                    cursor: pointer;
                    font-weight: 700;
                }
                .output {
                    background: #0f172a;
                    color: #dfe9ff;
                    border-radius: 12px;
                    padding: 16px;
                    font-family: monospace;
                    white-space: pre-wrap;
                    overflow: auto;
                    min-height: 180px;
                }
                .login-box {
                    max-width: 420px;
                    margin: 60px auto;
                    background: white;
                    border-radius: 16px;
                    border: 1px solid var(--line);
                    padding: 28px;
                }
                .error {
                    color: #b91c1c;
                    background: #fee2e2;
                    padding: 10px 12px;
                    border-radius: 8px;
                    margin-bottom: 12px;
                }
                a.button-link {
                    display: inline-block;
                    padding: 10px 14px;
                    text-decoration: none;
                    background: var(--primary);
                    color: white;
                    border-radius: 10px;
                    font-weight: 700;
                }
            </style>
        </head>
        <body>
            <div class="app-shell">
                <aside class="sidebar">
                    <div class="brand">HDAE</div>
                    <nav class="nav">
                        {{ nav | safe }}
                    </nav>
                    <div class="meta">
                        <div>Signed in: {{ username }}</div>
                        <div style="margin-top: 10px;"><a href="/logout" style="color:#dfe9ff; text-decoration:none;">Logout</a></div>
                    </div>
                </aside>
                <main class="content">
                    <div class="page-card">
                        {{ body | safe }}
                    </div>
                </main>
            </div>
        </body>
        </html>
        """,
        title=title,
        nav=_nav(active_page),
        username=session.get("username", "operator"),
        body=body
    )


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "hdae-demo-secret-key")

    @app.before_request
    def protect_routes():
        public_paths = {"/login", "/logout", "/health"}
        if request.path in public_paths:
            return None
        if request.path.startswith("/api/") and request.endpoint not in {"toolkit_api"}:
            if not session.get("authenticated"):
                return jsonify({"error": "unauthorized"}), 401
        if request.endpoint in {"login", "logout", "health", "toolkit_api"}:
            return None
        if not session.get("authenticated"):
            return redirect(url_for("login"))

    @app.get("/")
    def index():
        if session.get("authenticated"):
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.get("/login")
    def login():
        if session.get("authenticated"):
            return redirect(url_for("dashboard"))
        return """
            <!doctype html>
            <html lang="en">
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>HDAE Login</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        margin: 0;
                        background: linear-gradient(135deg, #0f172a, #1d4ed8);
                        color: #172033;
                    }
                    .login-box {
                        max-width: 420px;
                        margin: 100px auto;
                        background: white;
                        border-radius: 16px;
                        padding: 30px 24px;
                        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.25);
                    }
                    h1 { margin-top: 0; }
                    form { display: grid; gap: 12px; }
                    input, button {
                        width: 100%;
                        padding: 12px 14px;
                        border-radius: 10px;
                        border: 1px solid #dbe4f0;
                        font-size: 14px;
                    }
                    button {
                        background: #1d4ed8;
                        color: white;
                        border: none;
                        font-weight: 700;
                        cursor: pointer;
                    }
                    .hint { color: #48556c; font-size: 0.9rem; }
                </style>
            </head>
            <body>
                <div class="login-box">
                    <h1>HDAE Enterprise Login</h1>
                    <p class="hint">Default demo credentials: admin / hdae-admin</p>
                    <form method="post" action="/login">
                        <input type="text" name="username" placeholder="Username" required>
                        <input type="password" name="password" placeholder="Password" required>
                        <button type="submit">Sign In</button>
                    </form>
                </div>
            </body>
            </html>
        """

    @app.post("/login")
    def login_post():
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == "admin" and password == "hdae-admin":
            session["authenticated"] = True
            session["username"] = username
            return redirect(url_for("dashboard"))
        return render_template_string(
            """
            <div class="login-box">
                <h1>Invalid credentials</h1>
                <p>Use admin / hdae-admin for the demo environment.</p>
                <a href="/login" class="button-link">Try again</a>
            </div>
            """
        )

    @app.get("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.get("/dashboard")
    def dashboard():
        steps = _parse_architecture_steps()
        answers = _wizard_state_get("wizard_answers", {})
        pipeline = _pipeline_state()
        summary = _pipeline_summary(steps, answers, pipeline)
        process = _wizard_state_get("process_definition", {})
        gate_rows = "".join(
            f'<li><strong>{gate_id} · {html.escape(title)}</strong><span class="status">{html.escape(_implementation_gates()[gate_id]["status"])}</span></li>'
            for gate_id, title, _criteria in _IMPLEMENTATION_GATES
        )
        body = f"""
            <div class="header-row">
                <div>
                    <div class="pill">BAR governs capability lifecycle · HDAE governs outcome episodes</div>
                    <h1>BAR-HDAE Control Plane</h1>
                </div>
                <a class="button-link" href="/wizard">Open implementation workbench</a>
            </div>
            <div class="grid">
                <div class="stat"><div class="label">Active capability</div><div class="value" style="font-size:20px;">{html.escape(process.get("name", "Not defined"))}</div></div>
                <div class="stat"><div class="label">HDAE artifacts</div><div class="value">{summary["configured_steps"]}/{summary["total_steps"]}</div></div>
                <div class="stat"><div class="label">BAR gates</div><div class="value">{summary["gates"]["completed"]}/{summary["gates"]["total"]}</div></div>
                <div class="stat"><div class="label">Lifecycle status</div><div class="value" style="font-size:20px;">{html.escape(summary["status"].replace("_", " ").title())}</div></div>
            </div>
            <div style="margin-top:24px;">
                <h2>Outer loop · BAR capability lifecycle</h2>
                <p><strong>BAR-B:</strong> Business Value and Purpose · <strong>BAR-A:</strong> Architecture Readiness and Integration · <strong>BAR-R:</strong> Responsible Adoption and Realization</p>
                <p>Decide whether the capability is legitimate, ready, responsibly piloted, and producing sustained value.</p>
                <ul class="stage-list">{gate_rows}</ul>
                <p><a class="button-link" href="/framework">Review BAR-HDAE dual-loop model</a> <a class="button-link" href="/measurement">Review measurement and maturity</a></p>
            </div>
        """
        return _page_shell("HDAE Enterprise Dashboard", "dashboard", body)

    @app.get("/framework")
    def framework_page():
        gate_cards = "".join(
            f'<article class="stat"><div class="label">{gate_id}</div><h3>{html.escape(title)}</h3><p>{html.escape(criteria)}</p></article>'
            for gate_id, title, criteria in _IMPLEMENTATION_GATES
        )
        phase_cards = "".join(
            f'<article class="stat"><div class="label">HDAE Phase {index}</div><h3>{html.escape(phase["name"])}</h3><p>{html.escape(phase["bar"])}</p></article>'
            for index, phase in enumerate(_HDAE_PHASES, 1)
        )
        body = f"""
            <div class="header-row"><div><div class="label">Revised journal model</div><h1>BAR-HDAE Dual Loop</h1></div><a class="button-link" href="/wizard">Open workbench</a></div>
            <p><strong>BAR</strong> governs whether, where, and to what extent an AI capability should operate. <strong>HDAE</strong> governs how each authorized outcome episode executes. Runtime evidence is the bridge from episodes back to adoption, remediation, autonomy, and scale decisions.</p>
            <section class="report-section"><h2>Outer loop · capability lifecycle</h2><div class="report-grid">
                <article class="report-panel"><h3>BAR-B · Business Value and Purpose</h3><p>Problem, baseline, benefit, accountable owner, stakeholders, and why AI is justified.</p></article>
                <article class="report-panel"><h3>BAR-A · Architecture Readiness and Integration</h3><p>Data, capability, contract, identity, integration, NFR, resilience, observability, and lifecycle cost readiness.</p></article>
                <article class="report-panel"><h3>BAR-R · Responsible Adoption and Realization</h3><p>Proportional authority, adoption, monitoring, incidents, human intervention, benefit realization, and scale/stop decisions.</p></article>
            </div></section>
            <section class="report-section"><h2>Evidence gates</h2><div class="report-grid">{gate_cards}</div></section>
            <section class="report-section"><h2>Inner loop · seven HDAE implementation phases</h2><div class="report-grid">{phase_cards}</div></section>
            <section class="report-section"><h2>Outcome episode</h2><p>Human intent → bounded agent plan → identity/authority/policy/contract mediation → durable domain action → evidence and postcondition verification → recover, reconcile, intervene, or close.</p><p>Domain systems retain authoritative state and invariants. Gateway mediation does not replace business authorization or domain controls.</p></section>
            <section class="report-section"><h2>Evidence bridge</h2><p>Each episode links intent, plan, policy decision, tool call, domain transaction, human intervention, verified outcome, and benefit evidence to BAR-R lifecycle reviews.</p></section>
        """
        return _page_shell("BAR-HDAE Dual Loop", "framework", body)

    @app.get("/measurement")
    def measurement_page():
        metric_panels = []
        for category, metrics in _BAR_METRICS.items():
            rows = "".join(f"<tr><td>{html.escape(name)}</td><td>{html.escape(definition)}</td><td>{html.escape(target)}</td></tr>" for name, definition, target in metrics)
            metric_panels.append(f'<section class="report-section"><h2>{html.escape(category)}</h2><div class="table-wrap"><table><thead><tr><th>Metric</th><th>Definition</th><th>Direction / target</th></tr></thead><tbody>{rows}</tbody></table></div></section>')
        maturity = "".join(f'<article class="stat"><div class="label">{level}</div><h3>{html.escape(name)}</h3><p>{html.escape(characteristics)}</p></article>' for level, name, characteristics in _MATURITY_LEVELS)
        body = f"""
            <div class="header-row"><div><div class="label">Conceptual measurement model</div><h1>Realization Measures and Maturity</h1></div><a class="button-link" href="/framework">BAR-HDAE model</a></div>
            <p>The manuscript is conceptual and not empirically validated. Treat these measures as operational definitions and pilot baselines, not validated universal scales. A critical readiness or responsibility failure cannot be compensated by a high value score.</p>
            {''.join(metric_panels)}
            <section class="report-section"><h2>Institutional maturity · L0–L4</h2><div class="report-grid">{maturity}</div></section>
            <section class="report-section"><h2>Value lens</h2><p><strong>Realized Enterprise Value = Expected Benefit × Adoption × Reliability × Trust − Lifecycle Cost − Residual Risk Exposure</strong></p><p>This is a theory-guided relationship, not a universal quantitative scoring formula. Use evidence and accountable review to decide scale, hold, remediate, or stop.</p></section>
        """
        return _page_shell("BAR-HDAE Measures and Maturity", "measurement", body)

    @app.get("/toolkit")
    def toolkit():
        artifact_cards = "".join(
            f'<article class="stat"><div class="label">Phase {step["phase"]}</div><h3>{html.escape(step["title"])}</h3><p>{html.escape(step["description"])}</p><a href="/process/artifact/{_ARTIFACT_DEFINITIONS[step["title"]][0]}">Open artifact</a></article>'
            for step in _parse_architecture_steps()
        )
        body = f"""
            <div class="header-row">
                <div><div class="label">12 paper-defined architecture artifacts</div><h1>BAR-HDAE Toolkit</h1></div>
                <a class="button-link" href="/dashboard">Back to Dashboard</a>
            </div>
            <p>Artifacts represent architecture responsibilities, not vendor products. They are grouped by the seven HDAE implementation phases.</p>
            <p><a class="button-link" href="/framework">BAR-HDAE dual-loop model</a> <a class="button-link" href="/measurement">Metrics and maturity</a></p>
            <div class="grid">{artifact_cards}</div>
        """
        return _page_shell("BAR-HDAE Toolkit", "toolkit", body)

    @app.route("/process/new", methods=["GET", "POST"])
    def process_new():
        error = ""
        values = {
            "name": request.form.get("name", ""),
            "description": request.form.get("description", ""),
            "domain": request.form.get("domain", ""),
            "business_outcome": request.form.get("business_outcome", ""),
        }
        if request.method == "POST":
            values = {key: value.strip() for key, value in values.items()}
            missing = [label for key, label in (
                ("name", "process name"),
                ("description", "process description"),
                ("domain", "business domain"),
                ("business_outcome", "target business outcome"),
            ) if not values[key]]
            if missing:
                error = "Provide " + ", ".join(missing) + "."
            else:
                process = {
                    "process_id": re.sub(r"[^a-z0-9]+", "-", values["name"].lower()).strip("-")[:48] or uuid.uuid4().hex[:12],
                    **values,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "scenario": "custom",
                }
                _wizard_state_set("process_definition", process)
                _wizard_state_set("wizard_answers", {})
                _wizard_state_set("wizard_step", 0)
                _wizard_state_set("hdae_gates", {})
                pipeline = {
                    "run_id": f"hdae-{uuid.uuid4().hex[:12]}",
                    "process_id": process["process_id"],
                    "status": "draft",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "events": [],
                    "build": None,
                }
                _record_pipeline_event(pipeline, "process_created", detail={"process_id": process["process_id"], "name": process["name"]})
                _wizard_state_set("hdae_pipeline", pipeline)
                return redirect(url_for("wizard_page"))

        error_html = f'<div class="error">{html.escape(error)}</div>' if error else ""
        body = f"""
            <div class="header-row"><div><h1>Define a Business Process</h1><p>Create a process-specific HDAE implementation run.</p></div><a class="button-link" href="/wizard">Back to wizard</a></div>
            {error_html}
            <form method="post" action="/process/new" style="max-width:760px;">
                <label for="name"><strong>Process name</strong></label>
                <input id="name" name="name" value="{html.escape(values['name'], quote=True)}" placeholder="e.g. Subscription sales and revenue collection" required>
                <label for="description"><strong>What process are you designing?</strong></label>
                <textarea id="description" name="description" rows="4" required>{html.escape(values['description'])}</textarea>
                <label for="domain"><strong>Business domain</strong></label>
                <input id="domain" name="domain" value="{html.escape(values['domain'], quote=True)}" placeholder="e.g. Subscription commerce and finance" required>
                <label for="business_outcome"><strong>Target business outcome</strong></label>
                <textarea id="business_outcome" name="business_outcome" rows="3" required>{html.escape(values['business_outcome'])}</textarea>
                <button type="submit">Create process and begin</button>
            </form>
        """
        return _page_shell("Define Business Process", "wizard", body)

    @app.route("/wizard", methods=["GET", "POST"])
    def wizard_page():
        steps = _parse_architecture_steps()
        if not steps:
            return _page_shell("HDAE Reference Architecture Wizard", "wizard", "<h1>Wizard unavailable</h1><p>No architecture steps were found.</p>")

        answers = _wizard_state_get("wizard_answers", {})
        current_index = min(max(int(_wizard_state_get("wizard_step", 0)), 0), len(steps) - 1)
        pipeline = _pipeline_state()
        gates = _implementation_gates()

        if request.method == "POST":
            action = request.form.get("action", "next")
            if action == "reset":
                _wizard_state_pop("wizard_answers")
                _wizard_state_set("wizard_step", 0)
                pipeline = _pipeline_state()
                pipeline["status"] = "draft"
                pipeline["build"] = None
                _wizard_state_pop("hdae_gates")
                gates = _implementation_gates()
                _record_pipeline_event(pipeline, "pipeline_reset")
                _wizard_state_set("hdae_pipeline", pipeline)
                return redirect(url_for("wizard_page"))

            current_step = steps[current_index]
            existing_answer = answers.get(current_step["id"], {})
            submitted_fields = {
                key: request.form.get(f"field_{key}", "").strip()
                for key, _label, _required in _step_fields(current_step)
            }
            legacy_answer = request.form.get("answer", "").strip()
            answer = submitted_fields if any(submitted_fields.values()) else legacy_answer
            if action == "next":
                if isinstance(answer, dict) and not _answer_complete(current_step, answer):
                    missing_labels = [
                        label for key, label, required in _step_fields(current_step)
                        if required and not answer.get(key, "").strip()
                    ]
                    error = "Complete required fields: " + ", ".join(missing_labels)
                elif not answer and not existing_answer:
                    error = "Add an answer before continuing."
                else:
                    answers[current_step["id"]] = answer or existing_answer
                    _wizard_state_set("wizard_answers", answers)
                    _wizard_state_set("wizard_step", min(current_index + 1, len(steps) - 1))
                    _record_pipeline_event(pipeline, "step_configured", current_step["number"], {
                        "artifact": _wizard_artifact(current_step, answers[current_step["id"]])["artifact_file"]
                    })
                    _wizard_state_set("hdae_pipeline", pipeline)
                    return redirect(url_for("wizard_page"))
            elif action == "back":
                if answer:
                    answers[current_step["id"]] = answer
                    _wizard_state_set("wizard_answers", answers)
                _wizard_state_set("wizard_step", max(current_index - 1, 0))
                _record_pipeline_event(pipeline, "step_updated", current_step["number"])
                _wizard_state_set("hdae_pipeline", pipeline)
                return redirect(url_for("wizard_page"))
            else:
                error = "Choose a valid wizard action."
        else:
            error = ""

        current_step = steps[current_index]
        current_guide = _load_step_guide(current_step["number"])
        current_answer = answers.get(current_step["id"], {})
        if not isinstance(current_answer, dict):
            current_answer = {"configuration": current_answer}
        field_inputs = []
        for key, label, required in _step_fields(current_step):
            value = html.escape(str(current_answer.get(key, "")), quote=True)
            required_mark = " *" if required else ""
            field_inputs.append(
                f'<label for="field_{key}"><strong>{html.escape(label)}{required_mark}</strong></label>'
                f'<textarea id="field_{key}" name="field_{key}" rows="3" required {"" if required else ""} style="width: 100%; padding: 12px 14px; border-radius: 10px; border: 1px solid #dbe4f0; font: inherit; resize: vertical;">{value}</textarea>'
            )
        current_artifact = _wizard_artifact(current_step, answers.get(current_step["id"], ""))
        progress = int(((current_index + 1) / len(steps)) * 100)
        completed = sum(_answer_complete(step, answers.get(step["id"], "")) for step in steps)
        pipeline_summary = _pipeline_summary(steps, answers, pipeline)
        process_definition = _wizard_state_get("process_definition", {})
        sample_loaded = process_definition.get("scenario") in {"customer_onboarding", "subscription_revenue"}
        sample_label = {
            "customer_onboarding": "Customer onboarding",
            "subscription_revenue": "Subscription sales and revenue collection",
        }.get(process_definition.get("scenario"), "")
        _wizard_state_set("hdae_pipeline", pipeline)
        error_html = f'<div class="error">{html.escape(error)}</div>' if error else ""
        checklist = []
        for index, step in enumerate(steps):
            status = "Complete" if _answer_complete(step, answers.get(step["id"], "")) else "Pending"
            current = " • Current" if index == current_index else ""
            phase_name = _HDAE_PHASES[step["phase"] - 1]["name"]
            checklist.append(f'<li><strong>{index + 1}. {html.escape(step["title"])}</strong> — {status}{current}<br><small>{html.escape(phase_name)}</small></li>')
        gate_cards = []
        for gate_id, title, dependency in _IMPLEMENTATION_GATES:
            gate = gates[gate_id]
            gate_status = gate["status"]
            button_label = "Mark pending" if gate_status == "complete" else "Mark complete"
            next_status = "pending" if gate_status == "complete" else "complete"
            gate_cards.append(f"""
                <div class="stat" style="background: #f8fafc;">
                    <div class="label">{html.escape(gate_status)}</div>
                    <strong>{html.escape(gate_id)} · {html.escape(title)}</strong>
                    <p style="color:#48556c; margin-bottom:8px;">Evidence required: {html.escape(dependency)}</p>
                    <form method="post" action="/pipeline/gates/{gate_id}" style="max-width:none;">
                        <input name="owner" value="{html.escape(gate.get('owner', ''), quote=True)}" placeholder="Owner">
                        <input name="evidence" value="{html.escape(gate.get('evidence', ''), quote=True)}" placeholder="Evidence or approval reference">
                        <button type="submit" name="status" value="{next_status}">{button_label}</button>
                    </form>
                </div>
            """)

        body = f"""
            <div class="header-row">
                <div><h1>BAR-HDAE Implementation Workbench</h1><span class="pill">{completed}/{len(steps)} toolkit artifacts complete</span></div>
                <a class="button-link" href="/dashboard">Back to Dashboard</a>
            </div>
            <div class="stat" style="margin-bottom:18px; background:#f8fafc;">
                <div class="label">Current process</div>
                <strong>{html.escape(process_definition.get("name", "No process defined yet"))}</strong>
                <p style="color:#48556c;">{html.escape(process_definition.get("business_outcome", "Create a process definition, or load a sample scenario to explore the full workflow."))}</p>
                {("<p class=\"pill\">Loaded example: " + html.escape(sample_label) + " | All 12 toolkit artifacts are prefilled</p>" if sample_loaded else "")}
                <a class="button-link" href="/process/new">Start a new process</a>
            </div>
            <p style="margin-top: 0; color: #48556c;">BAR governs capability legitimacy, readiness, and realization; HDAE governs each authorized outcome episode. Runtime evidence feeds back into scale, remediation, and stop decisions.</p>
            <p><a href="/framework">BAR-HDAE dual-loop model</a> · <a href="/measurement">Metrics and maturity</a></p>
            <div class="stat" style="margin-bottom: 18px; background: #eef6ff;">
                <strong>Load a sample process</strong>
                <p style="color:#48556c;">Samples prefill all 12 toolkit artifacts and include design evidence for G0/G1. G2 pilot and G3 scale remain pending until supported by real post-deployment evidence.</p>
                <div style="display:flex; gap:10px; flex-wrap:wrap;">
                    <form method="post" action="/wizard/demo" style="max-width:none;"><button type="submit">Customer onboarding</button></form>
                    <form method="post" action="/wizard/demo/subscription" style="max-width:none;"><button type="submit">Subscription sales and revenue</button></form>
                    <a class="button-link" href="/wizard/demo/runbook">Onboarding runbook</a>
                    <a class="button-link" href="/process-builder-guide">Process builder guide</a>
                </div>
            </div>
            <div style="height: 10px; background: #e2e8f0; border-radius: 999px; margin: 20px 0 24px;">
                <div style="height: 10px; width: {progress}%; background: #1d4ed8; border-radius: 999px;"></div>
            </div>
            {error_html}
            <div class="grid" style="grid-template-columns: minmax(0, 1.5fr) minmax(240px, 1fr); align-items: start;">
                <section>
                    <div class="label">Artifact {current_index + 1} of {len(steps)} · HDAE phase {current_step['phase']} of 7</div>
                    <h2 style="margin-top: 8px;">{html.escape(current_step["title"])}</h2>
                    <p style="color: #48556c;">{html.escape(current_step["description"])}</p>
                    <p><span class="pill">{html.escape(_HDAE_PHASES[current_step['phase'] - 1]['name'])} · {_HDAE_PHASES[current_step['phase'] - 1]['bar']}</span></p>
                    <p><span class="pill">Artifact: {html.escape(current_artifact["artifact_file"])}</span></p>
                    <form method="post" action="/wizard" style="max-width: none;">
                        {''.join(field_inputs)}
                        <div style="display: flex; gap: 10px;">
                            <button type="submit" name="action" value="back" {"disabled" if current_index == 0 else ""}>Back</button>
                            <button type="submit" name="action" value="next">{"Finish" if current_index == len(steps) - 1 else "Save and continue"}</button>
                        </div>
                    </form>
                    <form method="post" action="/wizard" style="margin-top: 10px; max-width: none;">
                        <button type="submit" name="action" value="reset" style="background: #64748b;">Reset wizard</button>
                    </form>
                    <p style="margin-top: 18px;">
                        <a class="button-link" href="/wizard/artifact/{current_step['number']}">Download step artifact</a>
                        <a class="button-link" href="/wizard/download" style="background: #166534; margin-left: 8px;">Download all artifacts</a>
                    </p>
                    <p><a href="/process/deliverables">View C4 diagrams and executive brief</a></p>
                    <div class="stat" style="margin-top: 18px; background: #f8fafc;">
                        <div class="label">Implementation pipeline</div>
                        <p><strong>Run:</strong> {html.escape(pipeline_summary["run_id"])}</p>
                        <p><strong>Status:</strong> {html.escape(pipeline_summary["status"])}</p>
                        <p><strong>Tracked events:</strong> {pipeline_summary["event_count"]}</p>
                        {("<form method=\"post\" action=\"/pipeline/build\"><button type=\"submit\" style=\"background:#166534;\">Build governed implementation package</button></form>" if pipeline_summary["status"] == "ready" else "<p style=\"color:#48556c;\">Complete all 12 toolkit artifacts and pass G0 business legitimacy and G1 architecture readiness to build. G2 pilot and G3 scale require post-deployment evidence.</p>")}
                    </div>
                </section>
                <aside class="stat">
                    <div class="label">Toolkit artifact checklist</div>
                    <ul class="list" style="margin-top: 12px;">{''.join(checklist)}</ul>
                </aside>
            </div>
            <section class="stat" style="margin-top: 20px; background: #f8fafc;">
                <div class="header-row" style="margin-bottom: 8px;">
                    <div><div class="label">Step guide and implementation help</div><h2 style="margin: 6px 0 0;">{html.escape(current_guide["file"].split("/")[-1])}</h2></div>
                    <a class="button-link" href="/wizard/guide/{current_step['number']}">Open guide</a>
                </div>
                <div style="color: #48556c; line-height: 1.55;">{_guide_html(current_guide["content"])}</div>
            </section>
            <section style="margin-top: 20px;">
                <div class="header-row"><div><div class="label">BAR evidence gates</div><h2 style="margin: 6px 0 0;">{pipeline_summary["gates"]["completed"]}/{pipeline_summary["gates"]["total"]} evidenced · Current BAR phase: {html.escape(pipeline_summary["bar_phase"].title())}</h2></div></div>
                <div class="grid">{''.join(gate_cards)}</div>
            </section>
        """
        return _page_shell("HDAE Reference Architecture Wizard", "wizard", body)

    @app.post("/wizard/demo")
    def wizard_demo():
        _load_demo_scenario(_parse_architecture_steps(), "customer_onboarding")
        return redirect(url_for("wizard_page"))

    @app.post("/wizard/demo/subscription")
    def wizard_subscription_demo():
        _load_demo_scenario(_parse_architecture_steps(), "subscription_revenue")
        return redirect(url_for("wizard_page"))

    @app.get("/wizard/demo/runbook")
    def wizard_demo_runbook():
        with open(os.path.join(os.path.dirname(__file__), "13_Implementation", "HDAE_Demo_Runbook.md"), "r", encoding="utf-8") as handle:
            content = handle.read()
        return _page_shell("HDAE Demo Runbook", "wizard", f'<div class="header-row"><h1>Governed Customer Onboarding Demo</h1><a class="button-link" href="/wizard">Back to wizard</a></div><div style="line-height:1.6;">{_guide_html(content)}</div>')

    @app.get("/process-builder-guide")
    def process_builder_guide():
        with open(os.path.join(os.path.dirname(__file__), "13_Implementation", "Process_Builder_Guide.md"), "r", encoding="utf-8") as handle:
            content = handle.read()
        return _page_shell("Process Builder Guide", "wizard", f'<div class="header-row"><h1>Build Any Business Process</h1><a class="button-link" href="/wizard">Back to wizard</a></div><div style="line-height:1.6;">{_guide_html(content)}</div>')

    @app.post("/pipeline/gates/<gate_id>")
    def pipeline_gate_update(gate_id):
        valid_gate_ids = {item[0] for item in _IMPLEMENTATION_GATES}
        if gate_id not in valid_gate_ids:
            return jsonify({"error": "implementation gate not found"}), 404
        gates = _implementation_gates()
        requested_status = request.form.get("status")
        owner = request.form.get("owner", "").strip()
        evidence = request.form.get("evidence", "").strip()
        prerequisites = {
            "G0": [],
            "G1": ["G0"],
            "G2": ["G0", "G1"],
            "G3": ["G0", "G1", "G2"],
        }
        if requested_status == "complete":
            missing = [required for required in prerequisites[gate_id] if gates[required]["status"] != "complete"]
            if gate_id in {"G2", "G3"} and not _pipeline_state().get("build"):
                missing.append("implementation build")
            if missing:
                return jsonify({"error": "BAR gate prerequisites are incomplete", "missing": missing}), 409
            if not owner or not evidence:
                return jsonify({"error": "gate owner and evidence reference are required"}), 400
        gates[gate_id] = {
            "status": "complete" if requested_status == "complete" else "pending",
            "owner": owner,
            "evidence": evidence,
        }
        pipeline = _pipeline_state()
        _record_pipeline_event(pipeline, "implementation_gate_updated", detail={"gate": gate_id, **gates[gate_id]})
        _wizard_state_set("hdae_gates", gates)
        _wizard_state_set("hdae_pipeline", pipeline)
        return redirect(url_for("wizard_page"))

    @app.get("/wizard/guide/<int:step_number>")
    def wizard_guide(step_number):
        steps = _parse_architecture_steps()
        if step_number < 1 or step_number > len(steps):
            return jsonify({"error": "wizard step not found"}), 404
        guide = _load_step_guide(step_number)
        if request.args.get("format") == "markdown":
            return send_file(
                io.BytesIO(guide["content"].encode("utf-8")),
                mimetype="text/markdown",
                as_attachment=True,
                download_name=guide["file"].split("/")[-1],
            )
        return _page_shell(
            f"Step {step_number} Guide",
            "wizard",
            f'<div class="header-row"><h1>Step {step_number}: {html.escape(steps[step_number - 1]["title"])}</h1><a class="button-link" href="/wizard">Back to wizard</a></div><div style="line-height:1.6;">{_guide_html(guide["content"])}</div><p><a href="/wizard/guide/{step_number}?format=markdown">Download markdown source</a></p>',
        )

    @app.post("/pipeline/build")
    def pipeline_build_page():
        steps = _parse_architecture_steps()
        answers = _wizard_state_get("wizard_answers", {})
        pipeline = _pipeline_state()
        summary = _pipeline_summary(steps, answers, pipeline)
        if summary["missing_steps"] or summary["prebuild_gates_missing"]:
            _record_pipeline_event(pipeline, "build_blocked", detail={"missing_artifacts": summary["missing_steps"], "missing_prebuild_gates": summary["prebuild_gates_missing"]})
            _wizard_state_set("hdae_pipeline", pipeline)
            return redirect(url_for("wizard_page"))
        pipeline["status"] = "built"
        pipeline["build"] = {
            "build_id": f"build-{uuid.uuid4().hex[:12]}",
            "built_at": datetime.now(timezone.utc).isoformat(),
            "artifact_count": len(steps),
            "package": "hdae-wizard-artifacts.zip",
        }
        _record_pipeline_event(pipeline, "implementation_built", detail=pipeline["build"])
        _wizard_state_set("hdae_pipeline", pipeline)
        return redirect(url_for("wizard_download"))

    @app.get("/api/pipeline")
    def pipeline_api():
        steps = _parse_architecture_steps()
        answers = _wizard_state_get("wizard_answers", {})
        pipeline = _pipeline_state()
        _wizard_state_set("hdae_pipeline", pipeline)
        return jsonify({**_pipeline_summary(steps, answers, pipeline), "events": pipeline["events"]})

    @app.post("/api/pipeline/build")
    def pipeline_build_api():
        steps = _parse_architecture_steps()
        answers = _wizard_state_get("wizard_answers", {})
        pipeline = _pipeline_state()
        summary = _pipeline_summary(steps, answers, pipeline)
        if summary["missing_steps"] or summary["prebuild_gates_missing"]:
            _record_pipeline_event(pipeline, "build_blocked", detail={"missing_artifacts": summary["missing_steps"], "missing_prebuild_gates": summary["prebuild_gates_missing"]})
            _wizard_state_set("hdae_pipeline", pipeline)
            return jsonify({"error": "pipeline is incomplete", **_pipeline_summary(steps, answers, pipeline)}), 409
        pipeline["status"] = "built"
        pipeline["build"] = {
            "build_id": f"build-{uuid.uuid4().hex[:12]}",
            "built_at": datetime.now(timezone.utc).isoformat(),
            "artifact_count": len(steps),
            "package": "hdae-wizard-artifacts.zip",
        }
        _record_pipeline_event(pipeline, "implementation_built", detail=pipeline["build"])
        _wizard_state_set("hdae_pipeline", pipeline)
        return jsonify(_pipeline_summary(steps, answers, pipeline))

    @app.get("/wizard/artifact/<int:step_number>")
    def wizard_artifact(step_number):
        steps = _parse_architecture_steps()
        if step_number < 1 or step_number > len(steps):
            return jsonify({"error": "wizard step not found"}), 404
        step = steps[step_number - 1]
        answers = _wizard_state_get("wizard_answers", {})
        artifact = _wizard_artifact(step, answers.get(step["id"], ""))
        payload = json.dumps(artifact, indent=2).encode("utf-8")
        return send_file(
            io.BytesIO(payload),
            mimetype="application/json",
            as_attachment=True,
            download_name=artifact["artifact_file"],
        )

    @app.get("/wizard/download")
    def wizard_download():
        steps = _parse_architecture_steps()
        answers = _wizard_state_get("wizard_answers", {})
        artifacts = [_wizard_artifact(step, answers.get(step["id"], "")) for step in steps]
        architecture = _solution_architecture(steps, artifacts)
        implementation_plan = _implementation_plan(steps, artifacts)
        deliverables = _process_deliverables(steps, artifacts)
        manifest = {
            "bundle_version": "1.0",
            "process": _wizard_state_get("process_definition", {}),
            "source_file": "14_Architecture/HDAE_Reference_Architecture.md",
            "status": "configured" if all(item["status"] == "configured" for item in artifacts) else "draft",
            "pipeline": _wizard_state_get("hdae_pipeline", {}),
            "implementation_gates": _wizard_state_get("hdae_gates", {}),
            "artifacts": [item["artifact_file"] for item in artifacts],
        }
        bundle = io.BytesIO()
        with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("hdae-wizard-manifest.json", json.dumps(manifest, indent=2))
            archive.writestr("process-definition.json", json.dumps(_wizard_state_get("process_definition", {}), indent=2))
            archive.writestr("enterprise-solution-architecture.json", json.dumps(architecture, indent=2))
            archive.writestr("implementation-plan.json", json.dumps(implementation_plan, indent=2))
            archive.writestr("c4-system-context.mmd", deliverables["c4_system_context"])
            archive.writestr("c4-container-view.mmd", deliverables["c4_container_view"])
            archive.writestr("executive-brief.md", deliverables["executive_brief"])
            archive.writestr("pipeline-events.json", json.dumps(_wizard_state_get("hdae_pipeline", {}).get("events", []), indent=2))
            archive.writestr(
                "README.md",
                "# HDAE Wizard Artifact Bundle\n\n"
                "Review each JSON artifact, replace draft values with deployment-specific configuration, "
                "then apply them to the corresponding HDAE control-plane component.\n",
            )
            for document in ("Process_Builder_Guide.md", "HDAE_Demo_Runbook.md"):
                path = os.path.join(os.path.dirname(__file__), "13_Implementation", document)
                with open(path, "r", encoding="utf-8") as handle:
                    archive.writestr(f"guides/{document}", handle.read())
            for step in steps:
                guide = _load_step_guide(step["number"])
                archive.writestr(f"guides/{guide['file'].split('/')[-1]}", guide["content"])
            for artifact in artifacts:
                archive.writestr(artifact["artifact_file"], json.dumps(artifact, indent=2))
        bundle.seek(0)
        return send_file(
            bundle,
            mimetype="application/zip",
            as_attachment=True,
            download_name="hdae-wizard-artifacts.zip",
        )

    @app.get("/process/deliverables")
    def process_deliverables_page():
        steps = _parse_architecture_steps()
        answers = _wizard_state_get("wizard_answers", {})
        artifacts = [_wizard_artifact(step, answers.get(step["id"], "")) for step in steps]
        deliverables = _process_deliverables(steps, artifacts)
        process = _wizard_state_get("process_definition", {})
        process_title = html.escape(process.get("name", "Current Process"))
        body = f"""
            <style>
                .diagram-frame {{ width: 100%; overflow-x: auto; padding: 12px; background: #f7fafc; border: 1px solid #dbe4f0; border-radius: 8px; }}
                .mermaid {{ min-width: 900px; }}
                .mermaid svg {{ max-width: none !important; height: auto; }}
                .executive-brief {{ max-width: 1100px; line-height: 1.65; }}
                .executive-brief h1, .executive-brief h2 {{ color: #123f67; margin: 28px 0 12px; }}
                .executive-brief h1 {{ font-size: 28px; }}
                .executive-brief h2 {{ font-size: 20px; border-bottom: 1px solid #dbe4f0; padding-bottom: 6px; }}
                .executive-brief p, .executive-brief ul, .executive-brief ol {{ color: #334155; }}
                .executive-brief li {{ margin: 5px 0; }}
                .brief-table-wrap {{ width: 100%; overflow-x: auto; margin: 14px 0 22px; }}
                .executive-brief table {{ width: 100%; border-collapse: collapse; min-width: 620px; font-size: 14px; }}
                .executive-brief th {{ background: #e8f3f8; color: #123f67; text-align: left; }}
                .executive-brief th, .executive-brief td {{ padding: 9px 11px; border: 1px solid #cbd5e1; vertical-align: top; }}
                .executive-brief tr:nth-child(even) td {{ background: #f8fafc; }}
                .executive-brief a {{ color: #075985; }}
                @media (max-width: 760px) {{ .mermaid {{ min-width: 760px; }} }}
            </style>
            <div class="header-row"><div><div class="label">Generated architecture deliverables</div><h1>{process_title}</h1></div><a class="button-link" href="/wizard">Back to process builder</a></div>
            <p>These C4 views and the brief are generated from the current process definition and saved wizard inputs.</p>
            <p><a href="/process/deliverable/c4-system-context">C4 System Context</a> · <a href="/process/deliverable/c4-container-view">C4 Container View</a> · <a href="/process/deliverable/executive-brief">Executive Brief</a> · <a href="/wizard/download">Download full package</a></p>
            <h2>C4 System Context</h2><div class="diagram-frame"><pre class="mermaid">{html.escape(deliverables["c4_system_context"])}</pre></div>
            <h2>C4 Container View</h2><div class="diagram-frame"><pre class="mermaid">{html.escape(deliverables["c4_container_view"])}</pre></div>
            <h2>Executive Brief</h2><article class="executive-brief">{_markdown_html(deliverables["executive_brief"])}</article>
            <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
            <script>mermaid.initialize({{startOnLoad:true, theme:'neutral', flowchart:{{htmlLabels:true, curve:'basis', nodeSpacing:55, rankSpacing:75, padding:16}}}});</script>
        """
        return _page_shell("Architecture Deliverables", "wizard", body)

    @app.get("/process/enterprise-solution-architecture.json")
    @app.get("/process/implementation-plan.json")
    def process_json_deliverable():
        steps = _parse_architecture_steps()
        answers = _wizard_state_get("wizard_answers", {})
        artifacts = [_wizard_artifact(step, answers.get(step["id"], "")) for step in steps]
        if request.path.endswith("enterprise-solution-architecture.json"):
            document = _solution_architecture(steps, artifacts)
            filename = "enterprise-solution-architecture.json"
            title = "Enterprise Solution Architecture"
            process = document.get("process", {})
            implementation_sequence = document.get("implementation_sequence", [])
            promotion = document.get("environment_promotion", [])
            architecture_views = document.get("architecture_views", {})
            loops = document.get("governance_loops", {})
            gate_status = document.get("implementation_gate_status", {})
            business_view = architecture_views.get("business", {})
            integration_view = architecture_views.get("application_and_integration", {})
            security_view = architecture_views.get("security_and_control", {})
            evidence_view = architecture_views.get("data_and_evidence", {})
            resilience_view = architecture_views.get("resilience", {})
            gate_status_rows = "".join(
                f'<tr><td>{gate_id}</td><td>{html.escape(title)}</td><td>{html.escape(gate_status.get(gate_id, {}).get("status", "pending"))}</td><td>{html.escape(gate_status.get(gate_id, {}).get("owner", ""))}</td><td>{html.escape(gate_status.get(gate_id, {}).get("evidence", ""))}</td></tr>'
                for gate_id, title, _criteria in _IMPLEMENTATION_GATES
            )
            summary_html = f"""
                <section class="report-section"><h2>Business Context</h2>
                    <p><strong>Domain:</strong> {html.escape(str(process.get('domain', 'Not specified')))}</p>
                    <p><strong>Process:</strong> {html.escape(str(process.get('name', 'Not specified')))}</p>
                    <p><strong>Outcome:</strong> {html.escape(str(process.get('business_outcome', 'Not specified')))}</p>
                </section>
                <section class="report-section"><h2>BAR-HDAE Dual-Loop Model</h2>
                    <div class="report-grid">
                        <article class="report-panel"><h3>Outer BAR lifecycle</h3><p>{html.escape(" → ".join(loops.get("outer_BAR_capability_lifecycle", [])))}</p></article>
                        <article class="report-panel"><h3>Inner HDAE outcome episode</h3><p>{html.escape(" → ".join(loops.get("inner_HDAE_outcome_episode", [])))}</p></article>
                    </div>
                    <p><strong>Evidence bridge:</strong> {html.escape(str(loops.get("evidence_bridge", "")))}</p>
                    <p><em>{html.escape(str(document.get("theory_status", "")))}</em></p>
                </section>
                <section class="report-section"><h2>Architecture Views</h2>
                    <div class="report-grid">
                        <div class="report-panel"><h3>C4 Diagrams</h3><p><a href="/process/deliverable/c4-system-context">System Context</a></p><p><a href="/process/deliverable/c4-container-view">Container View</a></p></div>
                        <div class="report-panel"><h3>Business</h3><p>Outcome charter: {_artifact_link(str(business_view.get('outcome_charter_artifact', 'outcome-charter.json')))}</p><p>Capabilities: {_artifact_link(str(business_view.get('capability_artifact', 'capability-readiness-map.json')))}</p><p>Outcome contract: {_artifact_link(str(business_view.get('outcome_contract_artifact', 'outcome-contract.json')))}</p></div>
                        <div class="report-panel"><h3>Application and Integration</h3><p>Readiness map: {_artifact_link(str(integration_view.get('capability_readiness_artifact', 'capability-readiness-map.json')))}</p><p>Tool/action registry: {_artifact_link(str(integration_view.get('tool_registry_artifact', 'tool-action-registry.json')))}</p></div>
                        <div class="report-panel"><h3>Security and Control</h3><p>Authority profile: {_artifact_link(str(security_view.get('identity_authority_artifact', 'agent-authority-profile.json')))}</p><p>Autonomy-risk matrix: {_artifact_link(str(security_view.get('autonomy_risk_artifact', 'autonomy-risk-matrix.json')))}</p><p>Policy/control pack: {_artifact_link(str(security_view.get('policy_artifact', 'policy-control-pack.json')))}</p></div>
                        <div class="report-panel"><h3>Data, Evidence, and Resilience</h3><p>Evidence: {_artifact_link(str(evidence_view.get('evidence_artifact', 'traceability-evaluation-schema.json')))}</p><p>Recovery: {_artifact_link(str(resilience_view.get('recovery_artifact', 'transaction-recovery-map.json')))}</p><p>Metrics: <a href="/measurement">BAR-HDAE measures</a></p></div>
                    </div>
                </section>
                <section class="report-section"><h2>Implementation Sequence</h2>
                    <ol class="stage-list">{''.join(f'<li><strong>{html.escape(str(item.get("name", "Stage")))}</strong><span>{_artifact_link(str(item.get("artifact", "")))}</span><span class="status">{html.escape(str(item.get("status", "draft")))}</span></li>' for item in implementation_sequence)}</ol>
                </section>
                <section class="report-section"><h2>Environment Promotion</h2>
                    <div class="table-wrap"><table><thead><tr><th>Environment</th><th>Entry Criteria</th><th>Exit Criteria</th></tr></thead><tbody>{''.join(f'<tr><td>{html.escape(str(item.get("environment", "")))}</td><td>{html.escape("; ".join(item.get("entry_criteria", [])))}</td><td>{html.escape("; ".join(item.get("exit_criteria", [])))}</td></tr>' for item in promotion)}</tbody></table></div>
                </section>
                <section class="report-section"><h2>BAR Evidence Gate Status</h2><div class="table-wrap"><table><thead><tr><th>Gate</th><th>Decision</th><th>Status</th><th>Owner</th><th>Evidence reference</th></tr></thead><tbody>{gate_status_rows}</tbody></table></div></section>
                <section class="report-section"><h2>Deployment Boundary</h2><p>{html.escape(str(document.get('deployment_boundary', '')))}</p></section>
            """
        else:
            document = _implementation_plan(steps, artifacts)
            filename = "implementation-plan.json"
            title = "Implementation Plan"
            process = _wizard_state_get("process_definition", {})
            work_items = document.get("work_items", [])
            work_item_cards = []
            for item in work_items:
                phase = item.get("hdae_phase", {})
                documentation_panels = []
                for section_title, key in (
                    ("Architecture Deliverables", "architecture_deliverables"),
                    ("Deployment Decisions", "deployment_decisions"),
                    ("Validation Checks", "validation_checks"),
                    ("Risk Considerations", "risk_considerations"),
                ):
                    entries_html = _documentation_entries_html(item.get(key, []))
                    if entries_html:
                        documentation_panels.append(f'<section class="work-doc-group"><h4>{section_title}</h4>{entries_html}</section>')
                work_item_cards.append(f"""
                    <article class="work-item">
                        <div class="work-heading">
                            <span class="step-number">{int(item.get('sequence', 0)):02d}</span>
                            <div><h3>{html.escape(str(item.get('work_item', 'Implementation stage')))}</h3>
                            <p>HDAE Phase {int(item.get('hdae_phase_number', 0))} · {html.escape(str(phase.get('name', 'HDAE phase')))} · {html.escape(str(phase.get('bar', 'BAR + HDAE')))}</p>
                            <p>{_artifact_link(str(item.get('artifact', '')))}</p></div>
                            <span class="status">{html.escape(str(item.get('status', 'draft')))}</span>
                        </div>
                        <div class="work-documentation">{''.join(documentation_panels)}</div>
                    </article>
                """)
            summary_html = f"""
                <section class="report-section"><h2>Process</h2>
                    <p><strong>Name:</strong> {html.escape(str(document.get('process_name', 'Not specified')))}</p>
                    <p><strong>Process ID:</strong> {html.escape(str(document.get('process_id', 'Not specified')))}</p>
                    <p><strong>Outcome:</strong> {html.escape(str(process.get('business_outcome', 'Not specified')))}</p>
                </section>
                <section class="report-section"><h2>Work Items</h2>
                    <div class="work-list">{''.join(work_item_cards)}</div>
                </section>
                <section class="report-section"><h2>Promotion Path</h2><p>{html.escape(" → ".join(document.get("required_environment_path", [])))}</p><p><strong>Change control:</strong> {html.escape(str(document.get('change_control', '')))}</p></section>
            """
        payload = json.dumps(document, indent=2).encode("utf-8")
        if request.args.get("format") == "json":
            return current_app.response_class(payload, mimetype="application/json")
        if request.args.get("download") == "1":
            return send_file(
                io.BytesIO(payload),
                mimetype="application/json",
                as_attachment=True,
                download_name=filename,
            )
        process_name = html.escape(str(_wizard_state_get("process_definition", {}).get("name", "Current Process")))
        body = f"""
            <style>
                .report-header {{ display:flex; justify-content:space-between; align-items:flex-start; gap:16px; flex-wrap:wrap; }}
                .report-actions {{ display:flex; gap:8px; flex-wrap:wrap; }}
                .report-section {{ margin-top:24px; }}
                .report-section h2 {{ color:#123f67; border-bottom:1px solid #dbe4f0; padding-bottom:8px; }}
                .report-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; }}
                .report-panel,.work-item {{ border:1px solid #dbe4f0; background:#f8fafc; border-radius:6px; padding:16px; }}
                .report-panel h3,.work-item h3 {{ margin:0 0 8px; }}
                .table-wrap {{ overflow-x:auto; }}
                table {{ border-collapse:collapse; width:100%; min-width:640px; }}
                th,td {{ text-align:left; vertical-align:top; border:1px solid #cbd5e1; padding:10px; }}
                th {{ background:#e8f3f8; color:#123f67; }}
                .stage-list {{ padding-left:24px; }}
                .stage-list li {{ display:grid; grid-template-columns:minmax(200px,1fr) minmax(180px,auto) auto; gap:12px; padding:10px; border-bottom:1px solid #e2e8f0; }}
                .status {{ justify-self:start; color:#166534; background:#dcfce7; border-radius:999px; padding:3px 9px; font-size:12px; }}
                .work-list {{ display:grid; gap:12px; }}
                .work-heading {{ display:flex; align-items:center; gap:12px; }}
                .work-heading h3,.work-heading p {{ margin:0; }}
                .work-heading p {{ color:#64748b; font-size:13px; }}
                .step-number {{ display:grid; place-items:center; width:34px; height:34px; border-radius:50%; background:#dcecf5; color:#123f67; font-weight:700; flex:none; }}
                .work-documentation {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:12px; margin:14px 0 0 46px; }}
                .work-doc-group {{ min-width:0; }}
                .work-doc-group > h4 {{ margin:8px 0; color:#123f67; }}
                .work-doc {{ border:1px solid #dbe4f0; background:#fff; border-radius:5px; padding:12px; margin-bottom:8px; }}
                .work-doc h4 {{ margin:0 0 8px; font-size:14px; }}
                .work-doc p {{ margin:6px 0; font-size:13px; line-height:1.5; color:#334155; }}
                @media(max-width:700px) {{ .stage-list li {{ grid-template-columns:1fr; gap:4px; }} .work-documentation {{ margin-left:0; }} }}
            </style>
            <header class="report-header">
                <div><div class="label">HDAE generated deliverable</div><h1>{title}</h1><p>{process_name}</p></div>
                <nav class="report-actions"><a class="button-link" href="/process/deliverables">All deliverables</a><a class="button-link" href="/wizard">Process builder</a></nav>
            </header>
            <p><a href="/process/{filename}?format=json">View JSON</a> · <a href="/process/{filename}?download=1">Download JSON</a></p>
            {summary_html}
        """
        return _page_shell(title, "wizard", body)

    @app.get("/process/artifact/<path:artifact_filename>")
    def process_artifact_page(artifact_filename):
        steps = _parse_architecture_steps()
        answers = _wizard_state_get("wizard_answers", {})
        artifacts = [_wizard_artifact(step, answers.get(step["id"], "")) for step in steps]
        artifact = next((item for item in artifacts if item["artifact_file"] == artifact_filename), None)
        if artifact is None:
            return jsonify({"error": "process artifact not found"}), 404
        payload = json.dumps(artifact, indent=2).encode("utf-8")
        if request.args.get("format") == "json":
            return current_app.response_class(payload, mimetype="application/json")
        if request.args.get("download") == "1":
            return send_file(io.BytesIO(payload), mimetype="application/json", as_attachment=True, download_name=artifact_filename)
        return _page_shell(
            artifact["title"],
            "wizard",
            _artifact_report_html(artifact),
        )

    @app.get("/process/deliverable/<deliverable_name>")
    def process_deliverable_download(deliverable_name):
        filename_map = {
            "c4-system-context": ("c4-system-context.mmd", "c4_system_context", "text/plain"),
            "c4-container-view": ("c4-container-view.mmd", "c4_container_view", "text/plain"),
            "executive-brief": ("executive-brief.md", "executive_brief", "text/markdown"),
        }
        if deliverable_name not in filename_map:
            return jsonify({"error": "deliverable not found"}), 404
        steps = _parse_architecture_steps()
        answers = _wizard_state_get("wizard_answers", {})
        artifacts = [_wizard_artifact(step, answers.get(step["id"], "")) for step in steps]
        deliverables = _process_deliverables(steps, artifacts)
        filename, key, mimetype = filename_map[deliverable_name]
        content = deliverables[key]
        if request.args.get("download") == "1":
            return send_file(
                io.BytesIO(content.encode("utf-8")),
                mimetype=mimetype,
                as_attachment=True,
                download_name=filename,
            )
        if deliverable_name in {"c4-system-context", "c4-container-view"}:
            preview = f'<div style="width:100%; overflow:auto; padding:12px; background:#f7fafc; border:1px solid #dbe4f0; border-radius:8px;"><pre class="mermaid" style="min-width:900px;">{html.escape(content)}</pre></div><script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script><script>mermaid.initialize({{startOnLoad:true, theme:"neutral", flowchart:{{htmlLabels:true, curve:"basis", nodeSpacing:55, rankSpacing:75, padding:16}}}});</script>'
        elif deliverable_name == "executive-brief":
            preview = f'<style>.executive-brief{{max-width:1100px;line-height:1.65}}.executive-brief h1,.executive-brief h2{{color:#123f67;margin:28px 0 12px}}.executive-brief h2{{font-size:20px;border-bottom:1px solid #dbe4f0;padding-bottom:6px}}.executive-brief li{{margin:5px 0}}.brief-table-wrap{{width:100%;overflow-x:auto;margin:14px 0 22px}}.executive-brief table{{width:100%;border-collapse:collapse;min-width:620px;font-size:14px}}.executive-brief th{{background:#e8f3f8;color:#123f67;text-align:left}}.executive-brief th,.executive-brief td{{padding:9px 11px;border:1px solid #cbd5e1;vertical-align:top}}.executive-brief tr:nth-child(even) td{{background:#f8fafc}}</style><article class="executive-brief">{_markdown_html(content)}</article>'
        else:
            preview = f'<pre style="white-space:pre-wrap; overflow:auto;">{html.escape(content)}</pre>'
        return _page_shell(
            filename,
            "wizard",
            f'<div class="header-row"><h1>{html.escape(filename)}</h1><a class="button-link" href="/process/deliverables">All deliverables</a></div>{preview}<a href="/process/deliverable/{deliverable_name}?download=1">Download file</a>',
        )

    @app.get("/governance")
    def governance():
        gates = _implementation_gates()
        gate_rows = "".join(
            f'<tr><td>{gate_id}</td><td>{html.escape(title)}</td><td>{html.escape(gates[gate_id]["status"])}</td><td>{html.escape(gates[gate_id].get("owner", ""))}</td><td>{html.escape(gates[gate_id].get("evidence", ""))}</td><td>{html.escape(criteria)}</td></tr>'
            for gate_id, title, criteria in _IMPLEMENTATION_GATES
        )
        body = f"""
            <div class="header-row"><div><div class="label">Capability lifecycle evidence</div><h1>BAR Governance Gates</h1></div><a class="button-link" href="/wizard">Open workbench</a></div>
            <p>Gate completion requires an accountable owner and an evidence reference. G2 requires a built implementation and G0/G1; G3 requires G2.</p>
            <div class="table-wrap"><table><thead><tr><th>Gate</th><th>Decision</th><th>Status</th><th>Owner</th><th>Evidence</th><th>Minimum evidence</th></tr></thead><tbody>{gate_rows}</tbody></table></div>
        """
        return _page_shell("Governance", "governance", body)

    @app.get("/evidence")
    def evidence_page():
        pipeline = _pipeline_state()
        events = pipeline.get("events", [])
        event_rows = "".join(
            f'<tr><td>{html.escape(str(event.get("timestamp", "")))}</td><td>{html.escape(str(event.get("event_type", "")))}</td><td>{html.escape(str(event.get("step", "")))}</td><td><code>{html.escape(str(event.get("event_id", "")))}</code></td><td>{html.escape(json.dumps(event.get("detail", {}), sort_keys=True))}</td></tr>'
            for event in reversed(events)
        ) or '<tr><td colspan="5">No episode or lifecycle events have been recorded in this run.</td></tr>'
        body = f"""
            <div class="header-row"><div><div class="label">Runtime evidence bridge</div><h1>Episode Traceability</h1></div><a class="button-link" href="/wizard">Open workbench</a></div>
            <p>Evidence is scoped to active run <strong>{html.escape(pipeline.get('run_id', 'not started'))}</strong>. The local POC hash-links runtime episode events; production requires durable, access-controlled evidence storage.</p>
            <div class="table-wrap"><table><thead><tr><th>Timestamp</th><th>Event</th><th>Phase/step</th><th>Event ID</th><th>Details</th></tr></thead><tbody>{event_rows}</tbody></table></div>
        """
        return _page_shell("Evidence", "evidence", body)

    @app.get("/policy")
    def policy_page():
        steps = _parse_architecture_steps()
        answers = _wizard_state_get("wizard_answers", {})
        policy_step = next(item for item in steps if item["title"] == "Policy and Control Pack")
        artifact = _wizard_artifact(policy_step, answers.get(policy_step["id"], {}))
        body = f'<div class="header-row"><div><div class="label">BAR-R + HDAE complete mediation</div><h1>Policy and Control Pack</h1></div><a class="button-link" href="/framework">Framework model</a></div>{_artifact_report_html(artifact)}'
        return _page_shell("Policy", "policy", body)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "service": "HDAE runtime"})

    @app.get("/api/toolkit")
    def toolkit_api():
        return jsonify({
            "name": "BAR-Governed HDAE Toolkit",
            "status": "active",
            "framework_status": "conceptual; not empirically validated",
            "bar_gates": [{"gate": gate_id, "decision": title, "evidence_required": criteria} for gate_id, title, criteria in _IMPLEMENTATION_GATES],
            "hdae_phases": _HDAE_PHASES,
            "artifacts": [{"number": stage["number"], "title": stage["title"], "phase": stage["phase"], "file": _ARTIFACT_DEFINITIONS[stage["title"]][0]} for stage in _parse_architecture_steps()],
        })

    @app.get("/api/architecture")
    def architecture_api():
        return jsonify({"source_file": "14_Architecture/HDAE_Reference_Architecture.md", "steps": _parse_architecture_steps()})

    @app.get("/api/wizard")
    def wizard_api():
        steps = _parse_architecture_steps()
        answers = _wizard_state_get("wizard_answers", {})
        current_index = min(max(int(_wizard_state_get("wizard_step", 0)), 0), max(len(steps) - 1, 0))
        artifacts = [_wizard_artifact(step, answers.get(step["id"], "")) for step in steps]
        pipeline = _pipeline_state()
        return jsonify({
            "current_step": current_index,
            "completed_steps": sum(_answer_complete(step, answers.get(step["id"], "")) for step in steps),
            "total_steps": len(steps),
            "answers": answers,
            "artifacts": [
                {"step": artifact["step"], "file": artifact["artifact_file"], "status": artifact["status"]}
                for artifact in artifacts
            ],
            "guides": [
                {
                    "step": step["number"],
                    "file": _load_step_guide(step["number"])["file"],
                    "url": url_for("wizard_guide", step_number=step["number"]),
                }
                for step in steps
            ],
            "pipeline": _pipeline_summary(steps, answers, pipeline),
            "process": _wizard_state_get("process_definition", {}),
            "sample_loaded": _wizard_state_get("process_definition", {}).get("scenario") in {"customer_onboarding", "subscription_revenue"},
        })

    @app.get("/api/process")
    def process_api():
        return jsonify({"process": _wizard_state_get("process_definition", {})})

    @app.get("/api/wizard/guide/<int:step_number>")
    def wizard_guide_api(step_number):
        steps = _parse_architecture_steps()
        if step_number < 1 or step_number > len(steps):
            return jsonify({"error": "wizard step not found"}), 404
        guide = _load_step_guide(step_number)
        return jsonify({
            "step": step_number,
            "title": steps[step_number - 1]["title"],
            "file": guide["file"],
            "content": guide["content"],
        })

    @app.post("/api/execute")
    def execute():
        if not session.get("authenticated"):
            return jsonify({"error": "unauthorized"}), 401

        data = request.get_json(silent=True) or {}
        intent = {
            "intent_id": data.get("intent_id", "demo-intent"),
            "version": data.get("intent_version", "demo-intent-v1"),
            "permitted_actions": (data.get("authority") or {}).get("allowed_actions", ["create_record"]),
            "success_criteria": data.get("success_criteria", []),
        }
        authority = data.get("authority", {
            "allowed_actions": ["create_record"],
            "prohibited_actions": [],
            "approval_required_for": []
        })
        action = data.get("action", "create_record")
        context = data.get("context", {"state_changing": False, "correlation_id": "demo-correlation"})
        context["identity"] = context.get("identity", {
            "human_principal_authenticated": bool(session.get("username")),
            "agent_workload_authenticated": True,
            "target_tool_authenticated": True,
        })
        context.setdefault("policy_id", "hdae-local-demo-policy")
        context.setdefault("policy_version", "demo-v1")
        context.setdefault("schema_valid", True)
        context.setdefault("preconditions_valid", True)

        def adapter(ctx):
            return {
                "ok": True,
                "message": f"Executed action '{action}' for intent {intent['intent_id']}",
                "context": ctx,
            }

        result = governed_episode(
            intent,
            authority,
            action,
            context,
            adapter,
            plan=data.get("plan", {"plan_id": data.get("plan_id", "demo-plan"), "action": action}),
            policy_decision=data.get("policy_decision"),
            human_approval=bool(data.get("human_approval", False)),
        )
        return jsonify(result)

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
