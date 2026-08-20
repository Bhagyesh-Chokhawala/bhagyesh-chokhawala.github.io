# AI-OPS-003 — Runtime Safety and Kill Switch

**Domain:** Operations  
**Requirement:** MUST  
**Applicable risk tiers:** R3, R4  
**Lifecycle phases:** Runtime

## Standard

Agentic and high-impact AI deployments must support rapid suspension of model, tool, workflow, tenant, or autonomous behavior without full application redeployment.

## Required controls

- Provide disable-agent control
- Provide disable-tool/model/workflow controls
- Allow forced human approval mode
- Support affected-tenant or use-case isolation
- Test emergency procedures

## Required evidence

- Kill-switch runbook
- Emergency test
- Access-control list for emergency actions

## Framework mapping

- Security
- Operating Model
- Governance

## Tags

kill-switch, safety, agent
