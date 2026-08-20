# AI-AGENT-001 — Explicit Agent Authority Boundaries

**Domain:** AI Engineering  
**Requirement:** MUST  
**Applicable risk tiers:** R2, R3, R4  
**Lifecycle phases:** Architecture, Implementation, Runtime

## Standard

Every production agent must declare goal, allowed knowledge, tools, decisions, actions, human approval boundaries, resource budgets, and termination conditions.

## Required controls

- Define goal and allowed knowledge
- Allow-list tools and actions
- Set execution-step, token, time and cost limits
- Define human escalation and approval
- Provide kill switch and termination conditions

## Required evidence

- Agent manifest
- Tool allow-list
- Budget configuration
- Human-approval workflow
- Kill-switch test

## Framework mapping

- Technology Readiness
- Security
- Ethics
- Governance

## Tags

agent, autonomy, tools
