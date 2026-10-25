# SQL data quality investigation

**Question:** Which employee records are usable for reporting, and which need review?

![SQL data quality results](outputs/quality.png)

## Outcome

16 fictional raw records represent 14 employees. Two superseded versions are retained
separately. Latest-record checks accept 8 employees and quarantine 6. All source rows
are accounted for. [Read findings](outputs/findings.md).

## Walk through the SQL

Open [analysis.sql](analysis.sql) and read in this order:

1. `dq_ranked`: `ROW_NUMBER()` selects latest employee versions by update timestamp,
   then raw ID as a tie-breaker. All timestamps use the same ISO text format.
2. `dq_candidates`: normalises department aliases using `LOWER`, `TRIM` and `CASE`.
3. `dq_issues`: uses `UNION ALL` to preserve each separate rule failure.
4. `dq_quarantine`: uses `EXISTS` to isolate records needing a source-owner decision.
5. `dq_clean`: uses `NOT EXISTS` to return accepted records.

Run `python scripts/build_portfolio.py` at the repository root to load the fixture,
execute the SQL and regenerate all outputs. The database exists in memory during
the run. If using a SQLite GUI, import `data/raw_employees.csv` into `raw_employees`
with raw_id INTEGER, fte REAL and other fields TEXT, then execute `analysis.sql`.
Run `SELECT * FROM dq_clean;` to inspect results.

## Data dictionary and rule decisions

| Field | Meaning and rule |
| --- | --- |
| raw_id | Unique source version ID; deterministic tie-breaker |
| employee_id | Business key; repeated for different source versions |
| department_raw | Preserve original label; map only known aliases |
| fte | Capacity, must be >0 and <=1 for this fixture |
| manager_id | Must exist; E001 alone may have no manager; self-reporting fails |
| start_date | ISO date; must be parseable and not after 2025-12-31 |
| updated_at | ISO text timestamp used to choose latest version |

The source is deliberately small enough to inspect manually. The fixture includes
two old FTE errors which disappear when the latest version is selected; these old
versions remain in `outputs/superseded_records.csv` for traceability.

## Evidence

- [Issue log](outputs/issue_log.csv) and [rule counts](outputs/quality_summary.csv)
- [Quarantined records](outputs/quarantined_employees.csv)
- [Accepted records](outputs/clean_employees.csv)
- [Department reporting output](outputs/department_summary.csv)
- [Expected reconciliation](outputs/expected_metrics.json)

## Limits and next steps

This is a teaching pipeline, not a production HR ingestion service. The generator
supplies typed values and valid business keys. Full missing-key checks, strict calendar
date validation, timezone parsing, arbitrary organisation-cycle detection and cascading
manager quarantine need additional rules for real source systems. The build verifies
that all accepted managers are accepted in this particular fixture.

For real data, agree FTE and manager exceptions with the business owner. A single
employee may legitimately exceed 1 FTE across multiple assignments; this example's
rule applies only to its one-record-per-employee model.

**Practise:** give E014 an unknown manager, rerun and explain why quarantine rises
to 7. The baseline assertions intentionally fail until you explicitly update expected
controls for your changed fixture. Restore the generator afterward.
