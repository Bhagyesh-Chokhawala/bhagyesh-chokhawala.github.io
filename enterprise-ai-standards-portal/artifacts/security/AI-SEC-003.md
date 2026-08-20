# AI-SEC-003 — Prompt Injection and Untrusted Content Defense

**Domain:** Security  
**Requirement:** MUST  
**Applicable risk tiers:** R1, R2, R3, R4  
**Lifecycle phases:** Implementation, Build & Evaluation, Runtime

## Standard

User input and retrieved content must be treated as untrusted and must not be able to redefine system authority, permissions, or safety policies.

## Required controls

- Separate trusted instructions from untrusted context
- Test direct and indirect prompt injection
- Constrain tools with independent authorization
- Sanitize or isolate active content when applicable
- Monitor anomalous instruction patterns

## Required evidence

- Prompt injection test results
- Tool authorization evidence
- Adversarial evaluation report

## Framework mapping

- Security
- Technology Readiness

## Tags

prompt-injection, security, rag
