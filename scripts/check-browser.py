"""Optional local UI check: requires Python playwright and Chromium. Never publishes."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = 'http://127.0.0.1:4321'
ROUTES = ['/', '/work/fern-and-field/', '/demos/fern-and-field/']
results = []
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    for width, height in [(1440, 1000), (768, 1024), (390, 844), (320, 740)]:
        context = browser.new_context(viewport={'width': width, 'height': height}, reduced_motion='reduce')
        for route in ROUTES:
            page = context.new_page()
            errors, requests, failures = [], [], []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('request', lambda req: requests.append(req.url))
            page.on('response', lambda res: failures.append(f'{res.status} {res.url}') if res.status >= 400 else None)
            response = page.goto(BASE + route, wait_until='networkidle')
            assert response.status == 200, (route, response.status)
            assert not errors, errors
            assert not failures, failures
            assert all(url.startswith(BASE) for url in requests), requests
            assert page.locator('h1').count() == 1
            assert page.locator('form, input, textarea').count() == 0
            layout = page.evaluate('''() => ({viewport: innerWidth, width: document.documentElement.scrollWidth,
                overflow: [...document.querySelectorAll('body *')].filter(el => {
                    const r = el.getBoundingClientRect();
                    return getComputedStyle(el).position !== 'fixed' && (r.right > innerWidth + 1 || r.left < -1)
                }).filter(el => !el.closest('[aria-hidden="true"]')).map(el => el.tagName+'.'+el.className).slice(0,8)})''')
            assert layout['width'] <= width, (route, width, layout)
            page.keyboard.press('Tab')
            assert page.evaluate('document.activeElement.textContent').strip() == 'Skip to content'
            page.keyboard.press('Enter')
            assert page.evaluate('location.hash') == '#main'
            if route == '/demos/fern-and-field/':
                assert page.locator('button[disabled]').count() == 1
                details = page.locator('details').first
                details.locator('summary').click()
                assert details.get_attribute('open') is not None
                page.locator('a[href="#care"]').first.click()
                assert page.evaluate('location.hash') == '#care'
            results.append({'route':route, 'viewport':f'{width}x{height}', 'status':'pass', 'page_errors':len(errors), 'external_requests':0, 'horizontal_overflow':False})
            page.close()
        context.close()
    browser.close()
print(json.dumps({'checks':results,'total':len(results),'result':'PASS'},indent=2))
