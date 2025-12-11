import atexit
import io
import logging
import os
from datetime import datetime
import base64


from bs4 import BeautifulSoup

from config.constants import URL

from playwright.sync_api import sync_playwright

import pytest
from pytest_html import extras as pytest_html


@pytest.fixture(scope="session")
def login_logout():
    # perform login and browser close once in a session
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--start-maximized"])
        context = browser.new_context(no_viewport=True)
        context.set_default_timeout(80000)
        page = context.new_page()
        # Navigate to the login URL
        page.goto(URL, wait_until="domcontentloaded")

        yield page
        # perform close the browser
        browser.close()


@pytest.hookimpl(tryfirst=True)
def pytest_html_report_title(report):
    report.title = "Automation_FabricSQL"


log_streams = {}


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    # Prepare StringIO for capturing logs
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.INFO)

    logger = logging.getLogger()
    logger.addHandler(handler)

    # Save handler and stream
    log_streams[item.nodeid] = (handler, stream)


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

    # Handle log capture
    handler, stream = log_streams.get(item.nodeid, (None, None))
    if handler and stream:
        # Make sure logs are flushed
        handler.flush()
        log_output = stream.getvalue()

        # Only remove the handler, don't close the stream yet
        logger = logging.getLogger()
        logger.removeHandler(handler)

        # Store the log output on the report object for HTML reporting
        report.description = f"<pre>{log_output.strip()}</pre>"

        # Clean up references
        log_streams.pop(item.nodeid, None)
    else:
        report.description = ""
    
    # Set extras for pytest-html
    report.extras = extra


def pytest_collection_modifyitems(items):
    for item in items:
        if hasattr(item, 'callspec'):
            prompt = item.callspec.params.get("prompt")
            if prompt:
                item._nodeid = prompt  # This controls how the test name appears in the report


def rename_duration_column():
    report_path = os.path.abspath("report.html")  # or your report filename
    if not os.path.exists(report_path):
        print("Report file not found, skipping column rename.")
        return

    with open(report_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # Find and rename the header
    headers = soup.select('table#results-table thead th')
    for th in headers:
        if th.text.strip() == 'Duration':
            th.string = 'Execution Time'
            # print("Renamed 'Duration' to 'Execution Time'")
            break
    else:
        print("'Duration' column not found in report.")

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))


# Register this function to run after everything is done
atexit.register(rename_duration_column)


# Add logs and docstring to report
# @pytest.hookimpl(hookwrapper=True)
# def pytest_runtest_makereport(item, call):
#     outcome = yield
#     report = outcome.get_result()
#     report.description = str(item.function.__doc__)
#     os.makedirs("logs", exist_ok=True)
#     extra = getattr(report, "extra", [])
#     report.extra = extra
