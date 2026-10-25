-- SQLite dialect. One row per approved position at a single snapshot.
-- 'Filled' positions have exactly one unique employee in this example.
SELECT d.department,
 COUNT(*) AS approved_positions,
 SUM(CASE WHEN p.status='Filled' THEN 1 ELSE 0 END) AS headcount,
 ROUND(SUM(CASE WHEN p.status='Filled' THEN p.fte ELSE 0 END),2) AS filled_fte,
 SUM(CASE WHEN p.status='Vacant' THEN 1 ELSE 0 END) AS vacant_positions,
 ROUND(SUM(CASE WHEN p.status='Vacant' THEN p.fte ELSE 0 END),2) AS vacant_fte,
 ROUND(1.0*SUM(CASE WHEN p.status='Vacant' THEN 1 ELSE 0 END)/COUNT(*),4) AS vacancy_rate,
 SUM(CASE WHEN p.status='Vacant'
   AND julianday(p.snapshot_date)-julianday(p.vacancy_open_date)>60
   THEN 1 ELSE 0 END) AS vacancies_over_60_days
FROM positions p JOIN departments d ON p.department_id=d.department_id
GROUP BY d.department_id,d.department ORDER BY d.department_id;
