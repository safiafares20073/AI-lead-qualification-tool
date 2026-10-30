"""Optional browser checks against the real server; requires Playwright + Chromium.
No API responses are mocked. Run: python tests/browser_check.py
"""
import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

root = Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    page = browser.new_page(viewport={"width": 1440, "height": 1080})
    errors, requests_seen, loading_checks = [], [], []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('request', lambda request: requests_seen.append((request.method, request.url)))
    response = page.goto('http://127.0.0.1:8005/')
    assert response.status == 200 and 'text/html' in response.headers['content-type']
    expect(page.locator('h1')).to_contain_text('Welcome')
    assert len(page.locator('[id]').evaluate_all('(nodes) => nodes.map(node => node.id)')) == len(set(page.locator('[id]').evaluate_all('(nodes) => nodes.map(node => node.id)')))
    script = (root / 'static/app.js').read_text()
    for element_id in re.findall(r'byId\("([\w-]+)"\)', script):
        assert page.locator(f'#{element_id}').count() == 1, element_id
    for field in ['name', 'company', 'email', 'phone', 'need', 'budget', 'timeline', 'category', 'intent', 'score', 'priority', 'summary', 'suggested_reply']:
        assert page.locator(f'#{field}').count() == 1
    before = len(requests_seen)
    page.locator('#sample-button').click()
    page.wait_for_timeout(350)
    assert len(requests_seen) == before, 'Sample button unexpectedly made a network request'
    assert page.locator('#lead-message').input_value().startswith("Hi, I'm Sara Ahmed from Bright Tech.")
    assert 'sara@brighttech.example' in page.locator('#lead-message').input_value()

    def observe_loading(route):
        # Continue the real request after checking the UI's loading state.
        loading_checks.append(page.locator('#loading-state').is_visible())
        loading_checks.append(page.locator('#analyze-button').is_disabled())
        route.continue_()

    page.route('**/qualify', observe_loading)
    with page.expect_response(lambda r: r.url.endswith('/qualify') and r.request.method == 'POST', timeout=70000) as pending:
        page.locator('#analyze-button').click()
    result = pending.value
    body = result.json()
    assert result.request.post_data_json == {'message': page.locator('#lead-message').input_value()}
    assert all(loading_checks)
    assert result.url == 'http://127.0.0.1:8005/qualify'
    if result.ok:
        expect(page.locator('#results')).to_be_visible()
        assert json.loads(page.locator('#json-output').text_content()) == body
        page.locator('#copy-button').click()
        expect(page.locator('#copy-status')).not_to_be_empty()
        outcome = 'Live result displayed (see provider status separately)'
    else:
        expect(page.locator('#error-state')).to_be_visible()
        expect(page.locator('#error-message')).to_have_text(body['error'])
        expect(page.locator('#results')).to_be_hidden()
        outcome = f"Real API error displayed: HTTP {result.status}: {body['error']}"
    expect(page.locator('#analyze-button')).to_be_enabled()
    page.screenshot(path=str(root / 'tests/demo-desktop.png'), full_page=True)
    page.set_viewport_size({'width':375,'height':812})
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Horizontal overflow at mobile width'
    expect(page.locator('#lead-message')).to_be_visible()
    page.screenshot(path=str(root / 'tests/demo-mobile.png'), full_page=True)
    assert not errors, errors
    print('PASS: customer HTML, actual JS IDs, zero-request sample, same-origin POST, loading state, actual response display, mobile width, no JS errors')
    print(outcome)
    browser.close()
