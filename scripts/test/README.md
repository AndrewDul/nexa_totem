# Test Scripts

This folder is for scripts that run project checks and tests.

`run_unit_tests.py` runs the standard unit test suite with `unittest discover`.

`run_all_checks.py` runs unit tests and the fast diagnostics runner. It does not run camera capture by default.

`run_resource_benchmark.py` runs quick timing checks for existing diagnostics and panel data building. It does not run camera capture by default.

These scripts can print JSON with `--json`.

When requested, test results can be saved as latest reports or history reports for the future diagnostic panel:

- `--save-report`
- `--save-history`

This lets the future panel show the last test result without running tests every time the panel loads.

Resource benchmark reports are also saved only when requested.
