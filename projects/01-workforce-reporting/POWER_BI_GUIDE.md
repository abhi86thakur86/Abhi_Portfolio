# Build the workforce report in Power BI Desktop

This is a guided implementation. The native report has not been created or run here.
Menu labels can vary by version. Save your report locally while you work.

## 1. Import three CSV files

Download the repository: GitHub repository page, **Code > Download ZIP**, then extract it.
In Power BI Desktop use **Get data > Text/CSV** for `departments.csv`, `positions.csv`
and `recruitment.csv` in this project's `data` folder. Choose **Transform data**.
Use these exact query names: `departments`, `positions`, `recruitment`.

Set identifiers, status, department, role_family and stage to Text. Set `fte` to
Decimal number. Set the two date fields to Date. Empty vacancy dates and employee
IDs should be null, not the text `null` or a space. Review row counts: 4, 120, 24.
Choose Close & Apply.

## 2. Create and check relationships

In Model view, create active relationships with **single-direction filtering**:

| From | To | Cardinality |
| --- | --- | --- |
| departments[department_id] | positions[department_id] | One to many |
| positions[position_id] | recruitment[position_id] | One to many |

For the second relationship explicitly choose one-to-many with positions on the
one side, even though this sample has only one requisition per position. This allows
multiple requisitions in a future extension. Remove incorrect auto-detected links.
Do not connect recruitment directly to departments or turn on bidirectional filtering.

Department filters will reach positions and then recruitment. A recruitment stage
filter will not filter positions backward. Use stage only with the Requisitions measure.
This avoids ambiguous vacancy totals.

Reference: [Microsoft model relationships](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-relationships-understand).

## 3. Add measures one at a time

Open [measures.dax](measures.dax). For each definition, select **New measure** and
paste just that measure, not the whole file. Set Vacancy Rate to Percentage with
one decimal; FTE to one decimal and headcount/position counts to whole numbers.

Read the expression aloud. For example, Filled FTE first filters to filled roles,
then sums the role capacity. DIVIDE handles an empty denominator as blank.

## 4. Build two report pages

**Capacity page**

- Title: Workforce capacity. Add subtitle: Synthetic data, snapshot 31 December 2025.
- Cards: Headcount, Filled FTE, Vacancy Rate, Vacancies Over 60 Days.
- Stacked bar: departments[department] with Headcount and Vacant Positions.
- Bar: departments[department] with Vacancy Rate.
- Matrix: department, Approved Positions, Headcount, Filled FTE, Vacant Positions,
  Vacant FTE, Vacancy Rate.
- Slicer: departments[department]. Do not add status or recruitment-stage slicers to
  this page; the vacancy-rate denominator is all approved positions in a department.

**Recruitment page**

- Bar: recruitment[stage] with Requisitions. Order manually as Approved, Advertised,
  Interview, Offer, or add a stage-order column in Power Query and sort by it.
- Table: requisition_id, position_id, stage. Add department slicer.
- Keep this page's stage filter separate from the capacity page.

Use consistent navy for filled roles and amber for vacancies. Keep table totals visible.

## 5. Reconcile your report

Clear all filters. Expected cards: Headcount **96**, Filled FTE **85.8**,
Vacancy Rate **20.0%**, Vacancies Over 60 Days **15**. Total requisitions: **24**.
Operations should show 50 positions, 38 headcount, 12 vacancies and **24%** vacancy rate.
Check the entire matrix against `outputs/department_summary.csv`.

Select Technology: 35 positions, 28 headcount, 7 vacancies, 20% vacancy rate.
Clear the selection and verify totals return. Check blanks in the model if headcount
is 97: DISTINCTCOUNT may be counting a blank employee when the filter is missing.

The DAX is provided as build material and has not been executed in a Power BI engine.
SQL control values have been tested; confirm DAX and slicer behaviour on your computer.

## 6. Save and document your work

Save as `workforce_capacity.pbix` in this project folder. Export screenshots of both
pages to `outputs/` and link them from the project README, explicitly identifying
them as Power BI screenshots. Keep the existing Matplotlib preview labelled correctly.
Record your Power BI version, reconciliation results and any changes in
`docs/REVIEW_CHECKLIST.md`. Then upload the new files to GitHub.

Only describe the Power BI implementation as completed after those checks pass.
