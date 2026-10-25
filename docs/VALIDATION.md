# Validation and delivery limits

Build date: 25 October 2026. Reporting data are fictional CY2025 examples.

## Core pipeline

`python scripts/build_portfolio.py` regenerates source fixtures and runs the
committed SQLite analyses. Its assertions check:

- Workforce unique employee IDs, approved-position totals and filled/vacant FTE reconciliation.
- Exactly one requisition for each vacant position in this fixture.
- SQL quality partitions: 16 raw = 2 superseded + 8 accepted + 6 quarantined.
- Accepted/quarantine populations are disjoint and accepted records satisfy FTE and
  department rules; accepted manager references resolve in the accepted fixture.
- Hospitality contains 144 source rows and 12 month summaries.
- Revenue reconciles to quantity x price independently of SQL aggregation.
- Channel and monthly contribution totals agree; contribution less overhead ties to operating surplus.
- Row-level fee rounding agrees with an independent Decimal half-up calculation.

These controls validate this fixture. They are not a complete production data quality framework.
Known baseline constants are deliberate: changing the fixture may require reviewing controls.

`python scripts/verify_portfolio.py` additionally checks a tied update timestamp,
two issue flags on one employee, the strict 60/61-day boundary, an all-vacant department,
financial export totals and local Markdown links using disposable databases.

## Spreadsheet

The Excel workbook was authored with `@oai/artifact-tool`. Its calculated annual
revenue, contribution and operating surplus were compared with independent SQLite
results to the nearest cent. Input-change propagation and zero-revenue margin behaviour
were checked and restored before export. The three sheets were rendered for visual review.

Fee rates are represented as basis points during cent rounding to avoid binary
floating-point half-cent differences between engines. Inputs support fee rates to
four decimal places (decimal rate, e.g. 0.0150). Source data contain whole-dollar prices.

The generated workbook was inspected for formula errors. Native Microsoft Excel was
not available, so desktop rendering/recalculation remains a personal review step.

## Power BI

CSV inputs, definitions, relationships, DAX and expected results are supplied.
DAX and report interactions were not executed in a Power BI engine. There is no
native `.pbix` in this initial build. All supplied PNGs are Matplotlib analytical
previews, not Power BI screenshots. Follow the Power BI guide to complete this work.

## Reproduction boundaries

The Python core uses standard-library modules and Python 3.10+. Matplotlib is optional
for chart rebuilding. It is not required to reproduce the numerical results.
The committed XLSX can be opened and edited directly. Rebuilding that file requires
the separately documented spreadsheet authoring dependency; the Python build preserves it.
No external API, credentials or employer datasets are required by the portfolio scripts.

This repository makes no claims of workshop attendance, certificates, measured client
savings, employer ownership of these examples, or independent personal completion.
