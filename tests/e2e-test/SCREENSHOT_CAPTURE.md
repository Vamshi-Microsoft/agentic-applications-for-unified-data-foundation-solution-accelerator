# Screenshot Capture on Test Failure

## Overview
The E2E test framework now automatically captures screenshots when tests fail and embeds them in the HTML test report.

## Features

### Automatic Screenshot Capture
- **When**: Screenshots are automatically captured when any test fails during the `call` phase
- **Where**: Screenshots are saved to `tests/e2e-test/report/screenshots/`
- **Format**: PNG files with naming pattern: `failure_{test_name}_{timestamp}.png`

### HTML Report Integration
- Screenshots are **embedded directly** in the HTML report as base64-encoded images
- Click on any screenshot to open it in a new tab for full-screen viewing
- Screenshots appear in the "Extras" section of failed test results
- Report includes both logs and screenshots for comprehensive debugging

## File Structure

```
tests/e2e-test/
├── report/
│   ├── report.html          # Main HTML test report
│   └── screenshots/         # Screenshot directory
│       └── failure_*.png    # Captured failure screenshots
```

## GitHub Actions Integration

The workflow automatically:
1. Creates the screenshots directory before test execution
2. Captures screenshots on test failures (with retry logic)
3. Uploads both HTML report and screenshots as artifacts
4. Makes artifacts available for download from GitHub Actions UI

## Configuration

The screenshot functionality is configured in `tests/e2e-test/tests/conftest.py`:

```python
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # Screenshot capture on failure
    # Log capture
    # HTML report integration
```

## Usage

No additional configuration needed! Just run your tests normally:

```bash
pytest --html=report/report.html --self-contained-html
```

Screenshots will be automatically captured and embedded in the report when tests fail.

## Technical Details

- Uses Playwright's `page.screenshot()` method for full-page captures
- Screenshots are base64-encoded and embedded in HTML for portability
- Works with pytest-html plugin for seamless integration
- Includes timestamp to ensure unique filenames
- Error handling prevents screenshot failures from breaking test execution
