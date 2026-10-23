"""Full axe suite plus rendered label-in-name regressions; never publishes.
Run npm run build && npm run test:a11y. Requires Python playwright/Chromium.
No runOnly/tag filtering: all default axe rules run, plus the experimental
label-content-name-mismatch rule explicitly enabled for WCAG 2.5.3 coverage.
"""
import functools
import http.server
import json
from pathlib import Path
import re
import threading
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ['/', '/work/fern-and-field/', '/demos/fern-and-field/']
VIEWPORTS = [(1440, 1000), (768, 1024), (390, 844), (320, 740)]

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass

server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(ROOT/'dist')))
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{server.server_port}'
runs, failures, names = [], [], []
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
        for width, height in VIEWPORTS:
            for route in ROUTES:
                page = browser.new_page(viewport={'width':width, 'height':height}, reduced_motion='reduce')
                page.goto(base+route, wait_until='networkidle')
                if route != '/demos/fern-and-field/':
                    brand = page.locator('.site-header .brand')
                    desktop = width > 1000
                    expected = re.compile(r'^KRESPO LABS\s*/\s*PORTFOLIO$') if desktop else re.compile(r'^KRESPO LABS$')
                    try:
                        expect(brand).to_have_accessible_name(expected, timeout=1000)
                        expect(page.locator('.brand-sub')).to_be_visible() if desktop else expect(page.locator('.brand-sub')).to_be_hidden()
                        brand.focus()
                        assert page.evaluate('document.activeElement.classList.contains("brand")')
                        names.append({'route':route,'width':width,'control':'shared-header','result':'pass'})
                    except Exception as exc:
                        failures.append({'route':route,'width':width,'control':'shared-header','error':str(exc)})
                    page.evaluate('document.activeElement.blur()')
                if route == '/':
                    try:
                        preview = page.locator('a.garden-preview')
                        expect(preview.locator('.preview-cta')).to_have_text('Explore the garden ↗')
                        expect(preview).to_have_accessible_name(re.compile(r'Explore the garden'), timeout=1000)
                        assert preview.get_attribute('href') == '/demos/fern-and-field/'
                        names.append({'route':route,'width':width,'control':'garden-preview','result':'pass'})
                    except Exception as exc:
                        failures.append({'route':route,'width':width,'control':'garden-preview','error':str(exc)})
                if route == '/demos/fern-and-field/':
                    try:
                        expect(page.locator('.wordmark')).to_have_accessible_name('fern & field', timeout=1000)
                        names.append({'route':route,'width':width,'control':'demo-wordmark','result':'pass'})
                    except Exception as exc:
                        failures.append({'route':route,'width':width,'control':'demo-wordmark','error':str(exc)})
                page.add_script_tag(path=str(ROOT/'node_modules/axe-core/axe.min.js'))
                for expanded in ([False, True] if route == '/demos/fern-and-field/' else [False]):
                    page.locator('details').evaluate_all('(nodes,open)=>nodes.forEach(el=>el.open=open)', expanded)
                    result = page.evaluate("""async () => await axe.run(document, {
                        rules: {'label-content-name-mismatch': {enabled: true}}
                    })""")
                    incomplete = []
                    decorative = 0
                    for finding in result['incomplete']:
                        for node in finding['nodes']:
                            only_symbol = finding['id'] == 'color-contrast' and not node['all'] and not node['none'] and node['any'] and all(check.get('data',{}).get('messageKey') == 'nonBmp' for check in node['any'])
                            if only_symbol:
                                decorative += 1
                            else:
                                incomplete.append({'rule':finding['id'],'target':node['target'],'summary':node.get('failureSummary')})
                    issues = [{'rule':finding['id'],'impact':finding.get('impact'),'targets':[node['target'] for node in finding['nodes']]} for finding in result['violations']]
                    runs.append({'route':route,'width':width,'faqs_open':expanded,'rules_evaluated':len(result['passes'])+len(result['violations'])+len(result['incomplete'])+len(result['inapplicable']),'violations':issues,'unresolved_findings':incomplete,'arrow_only_notices':decorative})
                    if issues or incomplete:
                        failures.append(runs[-1])
                page.close()
        browser.close()
finally:
    server.shutdown()
summary = {'result':'FAIL' if failures else 'PASS','full_axe_runs':len(runs),'viewports':len(VIEWPORTS),'routes':len(ROUTES),'rules_per_run':sorted(set(run['rules_evaluated'] for run in runs)),'label_name_regressions_passed':len(names),'shared_header_checks':sum(n['control']=='shared-header' for n in names),'cta_checks':sum(n['control']=='garden-preview' for n in names),'demo_wordmark_checks':sum(n['control']=='demo-wordmark' for n in names),'axe_violations':sum(len(run['violations']) for run in runs),'unresolved_findings':sum(len(run['unresolved_findings']) for run in runs),'arrow_only_notices':sum(run['arrow_only_notices'] for run in runs),'failures':failures}
print(json.dumps(summary, indent=2))
raise SystemExit(1 if failures else 0)
