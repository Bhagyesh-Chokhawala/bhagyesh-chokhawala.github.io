# Security

Do not commit credentials, production tokens, customer data, or unmasked production payloads.
Report authorization bypass, unsafe MCP execution, or policy-evasion defects privately to maintainers.

## Website and report publication

The validation portal publishes sanitized text-based logs and reports. Teams must prevent credentials, production payloads, regulated information, and private customer data from entering validation artifacts. Redaction patterns in `website/portal-config.yaml` are defense-in-depth controls and do not guarantee removal of every sensitive value.

Use a private GitHub Pages or internal hosting environment when validation evidence is not suitable for public access. Binary artifacts are not content-inspected by the portal generator.
