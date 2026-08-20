# AI-SEC-002 — Least Privilege for Agents and Tools

**Domain:** Security  
**Requirement:** MUST  
**Applicable risk tiers:** R2, R3, R4  
**Lifecycle phases:** Architecture, Implementation, Runtime

## Standard

Agents and tools must receive only the permissions necessary for the assigned business capability and risk tier.

## Required controls

- Use scoped roles and permissions
- Prohibit generic admin tokens
- Review privilege changes
- Expire or rotate short-lived credentials
- Separate read, propose and execute privileges

## Required evidence

- Role matrix
- Permission test
- Credential policy
- Access review record

## Framework mapping

- Security
- Governance

## Tags

least-privilege, authorization, agent
