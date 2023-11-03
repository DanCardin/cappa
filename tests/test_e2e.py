def successful_test_run(pytester, *, count=None, skipped_count=0):
    pytester.copy_example()
    result = pytester.runpytest_inprocess(
        "-vv", "--log-cli-level=WARNING", "--log-level=WARNING", "conftest.py"
    )
    result.assert_outcomes(passed=count, skipped=skipped_count, failed=0)


def test_kitchen_sink(pytester):
    successful_test_run(pytester, count=1)
