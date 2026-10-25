-- SQLite 3.25+ dialect. scripts/build_portfolio.py loads raw_employees first.
-- Preserve raw versions. Choose the most recent record per business key,
-- using raw_id as a deterministic tie-breaker. Never silently average FTE.
DROP VIEW IF EXISTS dq_clean;
DROP VIEW IF EXISTS dq_quarantine;
DROP VIEW IF EXISTS dq_issues;
DROP VIEW IF EXISTS dq_candidates;
DROP VIEW IF EXISTS dq_ranked;
CREATE VIEW dq_ranked AS
SELECT *, ROW_NUMBER() OVER (
  PARTITION BY employee_id ORDER BY updated_at DESC, raw_id DESC
) AS version_rank FROM raw_employees;

CREATE VIEW dq_candidates AS
SELECT raw_id, employee_id,
 CASE lower(trim(department_raw))
   WHEN 'ops' THEN 'Operations' WHEN 'operations' THEN 'Operations'
   WHEN 'finance' THEN 'Finance' WHEN 'fin' THEN 'Finance'
   WHEN 'people' THEN 'People' WHEN 'hr' THEN 'People'
   WHEN 'technology' THEN 'Technology' WHEN 'it' THEN 'Technology'
   ELSE NULL END AS department,
 fte, NULLIF(trim(manager_id),'') AS manager_id, start_date, updated_at
FROM dq_ranked WHERE version_rank=1;

-- One row per issue. A record may have more than one issue.
-- For this fixture E001 is the sole authorised top-level manager.
CREATE VIEW dq_issues AS
SELECT raw_id, employee_id, 'UNMAPPED_DEPARTMENT' AS rule_code
 FROM dq_candidates WHERE department IS NULL
UNION ALL
SELECT raw_id, employee_id, 'INVALID_FTE' FROM dq_candidates
 WHERE fte IS NULL OR fte<=0 OR fte>1
UNION ALL
SELECT raw_id, employee_id, 'MISSING_MANAGER' FROM dq_candidates
 WHERE employee_id<>'E001' AND manager_id IS NULL
UNION ALL
SELECT c.raw_id, c.employee_id, 'UNKNOWN_MANAGER' FROM dq_candidates c
 LEFT JOIN dq_candidates m ON c.manager_id=m.employee_id
 WHERE c.manager_id IS NOT NULL AND m.employee_id IS NULL
UNION ALL
SELECT raw_id, employee_id, 'SELF_REPORTING' FROM dq_candidates
 WHERE manager_id=employee_id
UNION ALL
SELECT raw_id, employee_id, 'INVALID_START_DATE' FROM dq_candidates
 WHERE date(start_date) IS NULL OR date(start_date)>'2025-12-31';

CREATE VIEW dq_quarantine AS SELECT c.* FROM dq_candidates c
WHERE EXISTS(SELECT 1 FROM dq_issues i WHERE i.employee_id=c.employee_id);
CREATE VIEW dq_clean AS SELECT c.* FROM dq_candidates c
WHERE NOT EXISTS(SELECT 1 FROM dq_issues i WHERE i.employee_id=c.employee_id);

-- Business summaries use accepted records only. Quarantined records remain
-- visible in separate exports for follow-up with the data owner.
