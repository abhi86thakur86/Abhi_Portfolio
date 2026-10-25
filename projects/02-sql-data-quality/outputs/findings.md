# Data quality findings

Synthetic test fixture, reporting cutoff 31 December 2025.

16 raw records represent 14 employees. Two older versions are retained separately.
The latest-record checks accept 8 employees and quarantine 6. Each quarantined
employee has one issue in this fixture: missing manager, unknown manager,
self-reporting, invalid FTE, unmapped department, or start date after cutoff.

Reconciliation: 16 raw = 2 superseded + 8 accepted + 6 quarantined.
An issue count can exceed affected employees when a row breaks several rules.

Action: send the six exceptions to the source owner for confirmation, then rerun.
Do not guess a manager or silently clamp FTE to 1. The accepted dataset is incomplete
until exceptions are resolved; lower headcount after filtering is not a business reduction.
The fixture does not implement full organisation-cycle detection or production schema validation.
