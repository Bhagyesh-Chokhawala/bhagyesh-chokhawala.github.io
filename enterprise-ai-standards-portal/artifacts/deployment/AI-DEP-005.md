# AI-DEP-005 — Multicomponent AI Rollback

**Domain:** Deployment  
**Requirement:** MUST  
**Applicable risk tiers:** R2, R3, R4  
**Lifecycle phases:** Deployment, Runtime

## Standard

Rollback must cover application, model, prompt, policy, retriever/index, and agent/tool configuration, with a known-safe release configuration.

## Required controls

- Define known-safe configuration
- Test model and prompt rollback
- Test retriever/index rollback
- Test policy and tool rollback
- Define rollback authority and recovery objective

## Required evidence

- Rollback runbook
- Rollback test evidence
- Known-safe manifest

## Framework mapping

- Technology Readiness
- Operating Model
- Security

## Tags

rollback, recovery, deployment
