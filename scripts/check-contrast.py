"""Rendered WCAG AA regression: npm ci; npm run build; npm run test:contrast.
Requires Python playwright and /usr/bin/chromium. Serves dist on loopback only.
Axe checks actual rendering; the extra computed-style audit also covers visible
aria-hidden decorative text and disabled controls (voluntarily, beyond WCAG).
"""
import functools
import http.server
import json
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass

AUDIT_TEXT = r"""() => {
  const rgba = value => {
    const nums = value.match(/[\d.]+/g).map(Number);
    return [nums[0], nums[1], nums[2], nums.length > 3 ? nums[3] : 1];
  };
  const over = (fg, bg) => {
    const a = fg[3] + bg[3] * (1 - fg[3]);
    return [0,1,2].map(i => (fg[i]*fg[3] + bg[i]*bg[3]*(1-fg[3]))/a).concat(a);
  };
  const background = el => {
    const layers = [];
    for (let node=el; node; node=node.parentElement) {
      const s=getComputedStyle(node);
      if (s.backgroundImage !== 'none') throw Error('Unsupported text background image: '+node.className);
      if (Number(s.opacity)!==1 || s.mixBlendMode!=='normal') throw Error('Unsupported text compositing: '+node.className);
      layers.push(rgba(s.backgroundColor));
    }
    return layers.reverse().reduce((bg, fg) => over(fg,bg),[255,255,255,1]);
  };
  const luminance = rgb => rgb.slice(0,3).map(v => v/255).map(v => v<=0.04045 ? v/12.92 : ((v+0.055)/1.055)**2.4).reduce((n,v,i)=>n+v*[0.2126,0.7152,0.0722][i],0);
  const ratio = (fg,bg) => (Math.max(luminance(fg),luminance(bg))+.05)/(Math.min(luminance(fg),luminance(bg))+.05);
  const failures=[], checked=[];
  const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
  while(walker.nextNode()) {
    const node=walker.currentNode, el=node.parentElement, text=node.textContent.trim();
    if(!text || el.closest('svg,script,style')) continue;
    const s=getComputedStyle(el), range=document.createRange(); range.selectNodeContents(node);
    const rects=[...range.getClientRects()];
    if(s.visibility!=='visible' || !rects.some(r=>r.width>0&&r.height>0)) continue;
    const bg=background(el), fg=over(rgba(s.color),bg), contrast=ratio(fg,bg);
    const size=parseFloat(s.fontSize), weight=parseFloat(s.fontWeight)||400;
    const minimum=size>=24 || (size>=18.6666666667 && weight>=700) ? 3 : 4.5;
    const result={selector:el.tagName.toLowerCase()+(el.className?'.'+el.className.trim().replace(/\s+/g,'.'):''),text,foreground:s.color,background:bg.slice(0,3),ratio:contrast,minimum};
    checked.push(result); if(contrast<minimum) failures.push(result);
  }
  return {checked,failures};
}"""

server = http.server.ThreadingHTTPServer(('127.0.0.1',0), functools.partial(QuietHandler,directory=str(ROOT/'dist')))
threading.Thread(target=server.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{server.server_port}/demos/fern-and-field/'
reports=[]
notes=[]
normal_ratios=[]
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
        for width,height in [(1440,1000),(768,1024),(390,844),(320,740)]:
            page=browser.new_page(viewport={'width':width,'height':height},reduced_motion='reduce')
            page.goto(url,wait_until='networkidle')
            page.add_script_tag(path=str(ROOT/'node_modules/axe-core/axe.min.js'))
            for expanded in [False,True]:
                page.locator('details').evaluate_all('(nodes,open)=>nodes.forEach(node=>node.open=open)',expanded)
                result=page.evaluate(AUDIT_TEXT)
                axe=page.evaluate("async () => await axe.run(document, {runOnly: {type:'rule',values:['color-contrast']}})")
                reports.append({'width':width,'state':'faqs-open' if expanded else 'faqs-closed','text_nodes':len(result['checked']),'failures':result['failures'],'axe_violations':axe['violations'],'axe_incomplete':axe['incomplete']})
                note=next(row for row in result['checked'] if row['selector']=='p.demo-explanation')
                notes.append(note['ratio'])
                normal_ratios.extend(row['ratio'] for row in result['checked'] if row['minimum']==4.5)
                assert note['ratio']>=4.5,note
                assert not result['failures'],json.dumps(reports[-1],indent=2)
                assert not axe['violations'],json.dumps(axe['violations'],indent=2)
                # Axe cannot classify some arrow-only glyphs; they are independently
                # measured by AUDIT_TEXT. Fail on every other incomplete result.
                unexpected = [node for finding in axe['incomplete'] for node in finding['nodes']
                              if not node['any'] or any(check.get('data',{}).get('messageKey') != 'nonBmp'
                                                        for check in node['any'])]
                assert not unexpected,json.dumps(unexpected,indent=2)
            for selector in ['a','button[disabled]']:
                for el in page.locator(selector).all():
                    if not el.is_visible():
                        continue
                    states = ['focus'] if el.get_attribute('class') == 'skip-link' else (['hover','focus'] if selector=='a' else ['hover'])
                    for state in states:
                        if state=='hover': el.hover(force=True)
                        else: el.focus()
                        result=page.evaluate(AUDIT_TEXT)
                        assert not result['failures'],json.dumps({'width':width,'state':state,'failures':result['failures']},indent=2)
                        normal_ratios.extend(row['ratio'] for row in result['checked'] if row['minimum']==4.5)
                        reports.append({'width':width,'state':state,'text_nodes':len(result['checked']),'failures':[]})
                        page.mouse.move(0,0)
                        page.evaluate('document.activeElement.blur()')
            for selector in ['.wordmark','.footer-brand']:
                logo=page.locator(selector)
                assert logo.get_attribute('href')=='/demos/fern-and-field/'
                logo.click()
                assert page.url==url, page.url
            page.close()
        browser.close()
finally:
    server.shutdown()
print(json.dumps({'result':'PASS','viewports':4,'rendered_states':len(reports),'text_node_checks':sum(r['text_nodes'] for r in reports),'axe_runs':sum('axe_violations' in r for r in reports),'contrast_failures':0,'axe_violations':0,'axe_nontext_notices':sum(len(r.get('axe_incomplete',[])) for r in reports),'unresolved_text_findings':0,'logo_checks':8,'enquiry_note_min_ratio':min(notes),'normal_text_min_ratio':min(normal_ratios)},indent=2))
