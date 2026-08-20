# AI-INT-001 — Controlled API and Tool Invocation

**Domain:** Architecture  
**Requirement:** MUST  
**Applicable risk tiers:** R2, R3, R4  
**Lifecycle phases:** Architecture, Implementation

## Standard

AI agents may invoke only bounded, schema-defined, authorized tools and domain APIs through controlled execution paths.

## Required controls

- Define tool identifier and business capability
- Validate caller identity and authorization
- Validate input/output schema
- Define timeout, retry, idempotency and compensation
- Record every action in an audit trail

## Required evidence

- Tool registry
- API contract
- Authorization policy
- Tool execution audit sample

## Framework mapping

- Technology Readiness
- Security
- Governance

## Tags

agent, tool, api
