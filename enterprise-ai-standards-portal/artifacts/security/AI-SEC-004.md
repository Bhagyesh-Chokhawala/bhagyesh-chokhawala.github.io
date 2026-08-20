# AI-SEC-004 — Secrets and Credential Management

**Domain:** Security  
**Requirement:** MUST  
**Applicable risk tiers:** R1, R2, R3, R4  
**Lifecycle phases:** Implementation, Build & Evaluation, Deployment

## Standard

Secrets must use approved secret-management controls and must not appear in prompts, source code, model context, or logs.

## Required controls

- Store secrets in approved secret manager
- Run secret scanning in CI
- Use short-lived credentials where possible
- Redact sensitive values from telemetry
- Rotate compromised credentials

## Required evidence

- Secret-scan result
- Secrets manager configuration
- Credential rotation record

## Framework mapping

- Security
- Developer Enablement

## Tags

secrets, credentials, ci-cd
