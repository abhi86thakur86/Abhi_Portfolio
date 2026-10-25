# Workforce data dictionary

All identifiers are fictional. Empty CSV fields mean not applicable in this dataset.

| File and field | Type | Meaning |
| --- | --- | --- |
| departments.department_id | Text, unique | Department lookup key |
| departments.department | Text | Operations, Finance, People or Technology |
| positions.position_id | Text, unique | One approved position at the snapshot |
| positions.department_id | Text | Foreign key to departments |
| positions.role_family | Text | Generic grouping, not a real employer job title |
| positions.status | Text | Filled or Vacant |
| positions.employee_id | Text | Unique employee on a filled role; blank for a vacancy |
| positions.fte | Decimal | Approved capacity of the role: 0.6, 0.8 or 1.0 |
| positions.snapshot_date | ISO date | Fixed reporting date, 2025-12-31 |
| positions.vacancy_open_date | ISO date | Date vacancy opened; blank on filled positions |
| recruitment.requisition_id | Text, unique | Vacancy recruitment reference |
| recruitment.position_id | Text, unique | Foreign key to vacant position |
| recruitment.stage | Text | Approved, Advertised, Interview or Offer |

Headcount = distinct nonblank employee IDs on filled positions.
Filled FTE = sum of FTE for filled positions. Vacant FTE = sum for vacant positions.
Position vacancy rate = vacant positions / all approved positions.
Vacancy age = snapshot date minus vacancy open date in calendar days.
Over 60 days means strictly greater than 60, not greater than or equal to 60.

This register includes only positions approved at the snapshot. Recruitment stages
are synthetic and do not imply elapsed time in each stage.
