package api.release
default allow := false
deny contains "object-level authorization is required" if { not input.security.object_level_authorization }
deny contains "idempotency is required for process APIs" if { input.api.layer == "process"; not input.integrity.idempotency }
deny contains "MCP execution requires audit" if { input.ai.mcp.enabled; not input.ai.mcp.audit }
allow if { count(deny) == 0 }
