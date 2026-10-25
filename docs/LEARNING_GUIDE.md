# Build and understand your analytics portfolio

Prepared for Abhi. Start with the workforce project, then SQL quality, then hospitality.
Suggested learning pace: six sessions of 45–90 minutes. This is a flexible practice plan.

## What has been built, and why

An employer should be able to see a business question, inspect working evidence and
understand the judgement behind a recommendation. Each project therefore contains:

1. A README stating the problem, findings and limits.
2. Synthetic source data with a clear grain: what one row represents.
3. SQL or Excel calculations that can be inspected and rerun.
4. Results and a visual preview that can be viewed quickly.
5. Checks tying the results back to source records.
6. Exercises so you can explain and extend the work yourself.

The source records are fictional. The projects are AI-assisted demonstrations,
not your previous employer's reports. The examples reflect familiar workforce,
data quality and business questions without claiming real delivery outcomes.

## Session 1: Understand the repository

Open the root README on GitHub, then open `projects/01-workforce-reporting`.

| Term | Plain meaning | Example here |
| --- | --- | --- |
| Repository | Project folder with recorded versions | Abhi_Portfolio |
| README | The first explanation a visitor reads | Project question and findings |
| CSV | Table saved as plain text | positions.csv |
| Grain | What one row represents | One approved position at one date |
| Business key | Identifier used to recognise an entity | employee_id |
| Dimension | Descriptive lookup table | departments |
| Measure | Calculation used in reporting | Filled FTE |
| Commit | A recorded set of file changes | Add verified portfolio analyses |
| Reconciliation | Account for all source records or money | Filled + vacant = approved |

On the repository page choose **Code > Download ZIP**, then extract it. On Windows,
right-click the ZIP and choose Extract All. Keep the folder somewhere easy to find.
Open a project CSV in Excel to inspect it; don't resave it before the first build.

**Checkpoint:** explain the difference between a repository, a README and a dataset.

## Session 2: Run and understand workforce SQL

### First learn the business definitions

Headcount counts people. FTE measures capacity relative to a full-time role. Two
people working 0.5 FTE each are headcount 2 and FTE 1.0.

An approved position can be vacant and therefore still belong in the vacancy-rate
denominator. For Operations: 12 vacancies / 50 positions = 24%. Dividing 12 by the
38 employees would answer a different question.

### Run the supplied pipeline

Install Python 3.10+ if you do not already have it. Open a terminal in the extracted
repository folder. On Windows, open the folder in File Explorer, type `cmd` in the
address bar and press Enter. Run:

```bash
python scripts/build_portfolio.py
```

If Windows uses the Python launcher instead, run:

```bash
py scripts/build_portfolio.py
```

No package installation is required for the core build. It generates the datasets,
loads them into an in-memory SQLite database, executes the SQL files and exports
results. A final PASS message means its programmed checks completed. It does not
mean the Power BI or Excel desktop applications have been checked.

The generator produces the same baseline every time. Editing an exported CSV and
rerunning the generator overwrites that edit. To keep an experiment, copy the project
or intentionally change the generator and document the new expected results.

### Read the SQL

Open `projects/01-workforce-reporting/analysis.sql` in a text editor.

```sql
SUM(CASE WHEN p.status='Filled' THEN p.fte ELSE 0 END)
```

This reads each position: if filled, add its FTE; otherwise add zero. GROUP BY creates
one result for each department. JOIN attaches the readable department name to its ID.
The vacancy-rate expression uses `1.0*` so SQLite performs decimal division.

Expected overall results: 120 positions, 96 employees, 85.8 filled FTE, 24 vacant
positions, 19.8 vacant FTE, 20% vacancy rate and 15 vacancies older than 60 days.

**Practise:** use the Finance rows to calculate its vacancy rate by hand. Check against
`outputs/department_summary.csv`. Explain why headcount and FTE differ.

## Session 3: Build Power BI yourself

Follow [the Power BI guide](../projects/01-workforce-reporting/POWER_BI_GUIDE.md).
It explains CSV import, data types, relationships, measures, pages and checks.

The relationship from departments to positions lets a department selection filter
the measures. The DAX measure uses that current filter context when calculating a
total. Recruitment stages are kept on a separate page so they do not create a
misleading capacity denominator.

Build the cards and matrix first. Reconcile them before formatting. Then add the bars,
department slicer and recruitment page. Save the `.pbix` and take actual Power BI
screenshots. Label them separately from the supplied Matplotlib preview.

**Checkpoint:** select Technology, explain the 20% rate, clear the selection and
confirm 20% overall. Explain why those percentages happen to match in this fixture.

## Session 4: Investigate SQL data quality

Read `projects/02-sql-data-quality/README.md`, then compare the raw file with each output.

Follow E003 through the raw data. Two versions exist. The latest timestamp wins,
not the highest raw ID. Its older invalid FTE stays in the superseded export. Now
follow E011: its latest FTE of 1.4 fails this fixture's rule and is quarantined.

Inspect E008, E009 and E010 to distinguish a missing manager, an unknown manager and
self-reporting. They are different problems and should not be fixed with one default value.

The important reconciliation is:

**16 raw records = 2 superseded versions + 8 accepted latest records + 6 quarantined latest records.**

`UNION ALL` combines issue rows without removing duplicates. One employee could have
two different issues, so count distinct employees when measuring affected people.
`NOT EXISTS` prevents a flagged candidate entering the accepted dataset.

**Practise:** explain to a stakeholder why reporting on only 8 accepted employees
does not mean that 6 people left the organisation. Describe the follow-up you would
send to a data owner. Do not claim quarantining records resolved the source errors.

## Session 5: Explain business profitability in Excel

Download and open `projects/03-hospitality-profitability/hospitality_analysis.xlsx`.
Start on Monthly results, trace a month back to Sales calculation, then to Inputs.

Revenue is $465,948. Contribution is $272,730.77. Overhead is $357,000. The operating
surplus is negative $84,269.23. The business therefore loses money under these assumptions.

Contribution margin measures revenue remaining after food cost and channel fees.
It does not include the overhead costs. A higher-volume channel may still have a
lower margin because of fees. Overall margin is total contribution / total revenue;
averaging three channel percentages would give the channels equal weight incorrectly.

Try the controlled input experiments listed in the project README. Write down your
prediction before changing a cell, compare the result, then restore the baseline.
Fee calculations use integer basis points (1.5% = 150 basis points) to round cents
consistently; fee inputs support up to four decimal places as decimal rates.

**Checkpoint:** explain why reducing overhead improves operating surplus but does
not change contribution. Explain why operating surplus is not cash flow.

## Session 6: Make the portfolio yours and prepare to share

1. Complete the [review checklist](REVIEW_CHECKLIST.md) truthfully.
2. Replace one interpretation with your own explanation, supported by its figures.
3. Add your verified Power BI screenshot and `.pbix` after reconciliation.
4. Add an improvement you understand: for example, a department vacancy-age band.
5. Record the question, change, expected effect and check in the project README.

To update files using GitHub's website: open the repository, choose Add file > Upload
files, drag the changed files into the correct folder, and use a descriptive commit
message. Edit text files with the pencil icon. Check the rendered README afterward.

For your profile, add a professional photo and a short bio about SQL, Excel, Power BI
and workforce reporting. You can create a public repository named exactly
`abhi86thakur86` with a README to display an introduction on your profile. Pin
`Abhi_Portfolio` using Customise your pins. These profile steps have not been performed
as part of this repository build.

## How to discuss the work in an interview

Use a simple sequence: problem, data, method, check, finding, limitation, next action.

For workforce reporting, practise explaining how the position denominator was chosen,
why vacancies remain in the dataset, and why a single snapshot cannot show attrition.
For SQL quality, practise explaining latest-record selection and quarantine.
For hospitality, practise explaining channel fees and the difference between
contribution, operating surplus and cash flow.

If asked about authorship, explain that these are AI-assisted demonstration projects
you reviewed and extended. State which work you personally completed. Do not claim
independent end-to-end Power BI delivery before implementing and verifying it yourself.

## Add to your CV when ready

Link [Data Analytics Portfolio](https://github.com/abhi86thakur86/Abhi_Portfolio).
Keep a completed personal project separate from employment achievements. Describe
the synthetic data, tools used and calculations checked. A simulated result is not
evidence of money saved or outcomes delivered for an employer.

Good evidence to discuss: 120-position model, 16-record quality fixture fully
reconciled, 144-row operating analysis. Add Power BI only after completing that step.

## Technical documentation

- [Microsoft: star schema guidance](https://learn.microsoft.com/en-us/power-bi/guidance/star-schema)
- [Microsoft: relationships](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-relationships-understand)
- [SQLite: window functions](https://www.sqlite.org/windowfunctions.html)
- [GitHub: profile customisation](https://docs.github.com/en/account-and-profile/how-tos/profile-customization)
