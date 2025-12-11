To implement screenshot capture on test failure in other repositories, you need to copy these components:

## 📋 **Required Components**

### 1. **Dependencies** (add to requirements.txt)
```txt
pytest-html
beautifulsoup4
```

### 2. **Imports** (in conftest.py)
```python
import os
from datetime import datetime
import base64
import pytest
from pytest_html import extras as pytest_html
```

### 3. **The Hook Function** (in conftest.py)

Copy this entire function:

```python
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Unified hook to:
    1. Capture screenshot on test failure and embed in HTML report
    2. Capture logs and add to report description
    """
    outcome = yield
    report = outcome.get_result()
    
    # Initialize extras list for pytest-html
    extra = getattr(report, 'extras', [])

    # Handle screenshot capture on failure
    if report.when == "call" and report.failed:
        # Get the page from the test fixture
        if hasattr(item, 'funcargs') and 'login_logout' in item.funcargs:
            page = item.funcargs['login_logout']
            
            # Create screenshots directory if it doesn't exist
            screenshots_dir = os.path.join("report", "screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)
            
            # Generate screenshot filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            test_name = item.name.replace(" ", "_").replace("/", "_").replace("::", "_")
            screenshot_filename = f"failure_{test_name}_{timestamp}.png"
            screenshot_path = os.path.join(screenshots_dir, screenshot_filename)
            
            try:
                # Capture screenshot
                page.screenshot(path=screenshot_path, full_page=True)
                
                # Add screenshot to HTML report as embedded base64 image
                if os.path.exists(screenshot_path):
                    with open(screenshot_path, 'rb') as f:
                        screenshot_base64 = base64.b64encode(f.read()).decode('utf-8')
                        html_img = f'<div><img src="data:image/png;base64,{screenshot_base64}" alt="screenshot" style="width:100%; max-width:800px; cursor:pointer;" onclick="window.open(this.src)" title="Click to open in new tab"/></div>'
                        extra.append(pytest_html.extras.html(html_img))
                
                logging.info(f"Screenshot captured and embedded: {screenshot_path}")
            except Exception as e:
                logging.error(f"Failed to capture screenshot: {str(e)}")
    
    # Set extras for pytest-html
    report.extras = extra
```

### 4. **GitHub Workflow Updates** (in `.github/workflows/*.yml`)

**Before test execution:**
```yaml
- name: Run tests
  run: |
    mkdir -p tests/e2e-test/report/screenshots
    pytest --html=report/report.html --self-contained-html
```

**Upload artifacts:**
```yaml
- name: Upload test report
  uses: actions/upload-artifact@v4
  if: ${{ !cancelled() }}
  with:
    name: test-report
    path: |
      tests/e2e-test/report/*.html
      tests/e2e-test/report/screenshots/**
```

## ⚠️ **Important Adjustments**

### **Fixture Name**
If your other repos use a different fixture name for the Playwright page object, change this line:
```python
if hasattr(item, 'funcargs') and 'login_logout' in item.funcargs:
    page = item.funcargs['login_logout']  # Change 'login_logout' to your fixture name
```

### **Common Fixture Names**
- `page`
- `browser_page`
- `playwright_page`
- `context`

## 🎯 **Quick Checklist**

- [ ] Add `pytest-html` and `beautifulsoup4` to requirements.txt
- [ ] Add imports to conftest.py
- [ ] Copy `pytest_runtest_makereport` function to conftest.py
- [ ] Update fixture name if different from `login_logout`
- [ ] Update workflow to create screenshots directory
- [ ] Update workflow to upload screenshots with report

That's it! The screenshot capture will work automatically on test failures.