# AI-RAG-001 — Grounded and Authorized Retrieval

**Domain:** AI Engineering  
**Requirement:** MUST  
**Applicable risk tiers:** R1, R2, R3, R4  
**Lifecycle phases:** Implementation, Build & Evaluation, Runtime

## Standard

RAG implementations must preserve authorization, provenance, source traceability, and tenant isolation while treating retrieved content as untrusted input.

## Required controls

- Filter retrieval by user authorization
- Preserve source identifiers and provenance
- Prevent cross-tenant retrieval
- Validate context relevance and source freshness
- Treat retrieved instructions as untrusted content

## Required evidence

- Retrieval authorization tests
- Groundedness evaluation
- Cross-tenant isolation test
- Provenance sample

## Framework mapping

- Technology Readiness
- Security
- User Trust & Completeness

## Tags

rag, retrieval, grounding
