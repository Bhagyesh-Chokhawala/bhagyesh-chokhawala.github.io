# Runtime Control Algorithm

For each material action:
1. Resolve Human Intent Envelope.
2. Authenticate agent/workload identity.
3. Resolve represented principal.
4. Load Agent Authority Profile.
5. Validate action and capability permission.
6. Evaluate policy and risk.
7. Obtain human approval when required.
8. Require correlation/idempotency for state changes.
9. Confirm recovery/compensation.
10. Record pre-execution evidence.
11. Invoke authorized contract/tool.
12. Record domain result.
13. Verify outcome completion.
14. Recover/compensate/escalate if incomplete.
15. Emit metrics and evidence.

## Fail closed
Missing/expired intent; unknown identity; expired delegation; policy unavailable;
approval missing; scope mismatch; evidence unavailable for protected action;
recovery undefined for material state change.
