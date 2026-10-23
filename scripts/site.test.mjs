import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const routes = ['index.html', 'work/fern-and-field/index.html', 'demos/fern-and-field/index.html'];
const pages = routes.map(route => ({route, html: readFileSync(join('dist', route), 'utf8')}));
const files = dir => readdirSync(dir, {withFileTypes:true}).flatMap(e => e.isDirectory() ? files(join(dir,e.name)) : [join(dir,e.name)]);

for (const {route,html} of pages) {
  test(`${route}: semantic shell, title and draft indexing protection`, () => {
    assert.match(html, /<html[^>]*lang="en"/);
    assert.equal((html.match(/<h1\b/g)||[]).length,1);
    assert.equal((html.match(/<main\b/g)||[]).length,1);
    assert.match(html, /<title>[^<]+<\/title>/);
    assert.match(html, /name="description"\s+content="[^"]+"/);
    assert.match(html, /name="robots"\s+content="noindex, nofollow"/);
    assert.match(html, /href="#main"/);
    assert.match(html, /id="main"/);
  });
  test(`${route}: no data collection, scripts, remote assets or contact details`, () => {
    assert.doesNotMatch(html, /<(form|input|textarea|iframe|script)\b/i);
    assert.doesNotMatch(html, /(?:mailto:|tel:|supabase\.co|api[_-]?key)/i);
    assert.doesNotMatch(html, /\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b/i);
    assert.doesNotMatch(html, /(?:src|action)="https?:/i);
    assert.doesNotMatch(html, /<link[^>]+href="https?:/i);
  });
  test(`${route}: every local link, fragment and asset resolves`, () => {
    for (const [,url] of html.matchAll(/(?:href|src)="([^"]+)"/g)) {
      if (/^https:\/\//.test(url)) {
        assert.ok(url.startsWith('https://github.com/Krespolabs'),`unexpected external link: ${url}`);
        continue;
      }
      const [path,fragment] = url.split('#');
      const target = path ? join('dist',path.endsWith('/') ? path+'index.html' : path) : join('dist',route);
      assert.ok(existsSync(target),`${url} should resolve from ${route}`);
      if(fragment) assert.ok(readFileSync(target,'utf8').includes(`id="${fragment}"`),`missing fragment ${url}`);
    }
  });
}
test('source project descriptions retain unverified-status caveats', () => {
  const home=pages[0].html;
  assert.match(home,/Deployment and current status are unverified/);
  assert.match(home,/Working integrations are unverified/);
  assert.match(home,/prototype interface/i);
});
test('fictional demo is explicitly labelled and enquiry is disabled', () => {
  const demo=pages[2].html;
  assert.match(demo,/fictional business/i);
  assert.match(demo,/design demo/i);
  assert.match(demo,/<button[^>]*disabled/);
  assert.ok((demo.match(/<details\b/g)||[]).length>=2,'native FAQs are present');
});
test('both demo logos return to the demo home, not the portfolio', () => {
  const demo=pages[2].html;
  for (const className of ['wordmark', 'footer-brand']) {
    assert.match(demo, new RegExp(`<a class="${className}" href="/demos/fern-and-field/"`));
  }
});
test('static output contains no runtime JavaScript or media', () => {
  const outputFiles=files('dist');
  assert.ok(outputFiles.length>=5);
  assert.ok(!outputFiles.some(f => /\.(js|mjs|mp4|mov|webm|mp3)$/i.test(f)));
  assert.match(readFileSync('dist/robots.txt','utf8'),/Disallow: \/\s*$/);
});
