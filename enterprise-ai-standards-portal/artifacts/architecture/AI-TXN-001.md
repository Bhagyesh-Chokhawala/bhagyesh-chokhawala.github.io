# AI-TXN-001 — Transaction Integrity for AI Actions

**Domain:** Architecture  
**Requirement:** MUST  
**Applicable risk tiers:** R2, R3, R4  
**Lifecycle phases:** Architecture, Implementation

## Standard

AI-generated decisions must use controlled business transactions; models must not directly mutate authoritative enterprise state.

## Required controls

- Route state changes through domain transaction APIs
- Implement idempotency and concurrency protection
- Define atomicity or compensation
- Preserve correlation and audit identifiers
- Require approval for high-impact actions

## Required evidence

- Transaction sequence diagram
- Idempotency test
- Compensation test
- Approval boundary definition

## Framework mapping

- Technology Readiness
- User Trust & Completeness
- Governance

## Tags

transaction, integrity, api
