# AI-DEP-002 — Versioned AI Deployment Unit

**Domain:** Deployment  
**Requirement:** MUST  
**Applicable risk tiers:** R1, R2, R3, R4  
**Lifecycle phases:** Deployment, Runtime

## Standard

Every release must pin application, model, prompt, RAG configuration, embedding/index, policy, tool configuration, and evaluation versions.

## Required controls

- Create immutable release identifier
- Pin model and prompt versions
- Record retrieval/index version
- Record policy and tool configuration
- Link release to evaluation evidence

## Required evidence

- AI release manifest
- Artifact checksums
- Evaluation linkage

## Framework mapping

- Technology Readiness
- Governance
- Operating Model

## Tags

release, versioning, manifest
