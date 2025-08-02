# KangarooCurrents-Real-Time-Lakehouse-for-Australia-s-Electricity-Grid

This repository demonstrates basic data quality checks using [Great Expectations](https://greatexpectations.io/).

## Expectation Suites

Expectation suites live in `great_expectations/expectations/`.

- **Bronze** (`bronze_suite`):
  - `id` and `reading` must be non-null.
  - `reading` values must fall between 0 and 1000.
- **Silver** (`silver_suite`):
  - `id` must be 99% complete and unique.
  - `reading` must be 98% complete.

## Validation in Spark Jobs

Sample Spark jobs in `jobs/data_quality.py` load data, apply the relevant expectation
suite, and raise a `ValueError` if validation fails. The thresholds above define
expected success rates; failure triggers a job halt for investigation.
