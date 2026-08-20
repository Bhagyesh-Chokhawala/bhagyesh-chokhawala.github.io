# AI-SEC-005 — AI Output Validation

**Domain:** Security  
**Requirement:** MUST  
**Applicable risk tiers:** R1, R2, R3, R4  
**Lifecycle phases:** Implementation, Build & Evaluation

## Standard

Model output must be treated as untrusted before execution, rendering, storage, API submission, query construction, or system-of-record update.

## Required controls

- Validate structured output against schema
- Escape or sanitize rendered output
- Do not execute generated code or commands without independent controls
- Validate identifiers and target resources before actions

## Required evidence

- Schema-validation tests
- Output sanitization tests
- Tool action validation tests

## Framework mapping

- Security
- User Trust & Completeness

## Tags

output-validation, security, schema
