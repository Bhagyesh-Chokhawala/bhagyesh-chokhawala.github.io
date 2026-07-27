# Traffic-Light Gate Model

- **GREEN**: every dimension is GREEN, no blocking gates fail, and the risk-tier score is met.
- **AMBER**: at least one dimension is AMBER, no dimension is RED, and no blocking gate fails. A remediation plan or documented risk acceptance is required.
- **RED**: any blocking gate fails, any dimension is RED, or the overall score is below the amber threshold. Release is blocked.

The Markdown report uses visible traffic-light indicators, and the JSON report exposes `traffic_light` at both overall and dimension levels.
