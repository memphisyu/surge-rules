const fs = require('node:fs');
const crypto = require('node:crypto');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const dir = process.argv[2] || 'Surge';
const manifest = JSON.parse(fs.readFileSync(path.join(dir, 'manifest.json')));
let count = 0;
for (const [brand, info] of Object.entries(manifest.rulesets)) {
  const content = fs.readFileSync(path.join(dir, brand + '.list'), 'utf8');
  assert.equal(crypto.createHash('sha256').update(content).digest('hex'), info.sha256);
  const list = content.trim().split('\n');
  for (const rule of list) assert.match(rule, /^(DOMAIN|DOMAIN-SUFFIX|DOMAIN-KEYWORD|IP-CIDR|IP-CIDR6|IP-ASN|PROCESS-NAME|SCRIPT),[^\r\n]+$/);
  assert.deepEqual(list.filter(rule => rule.startsWith('SCRIPT,')), info.regex_rules ? ['SCRIPT,HawaiineRegex-' + brand] : []);
  assert.equal(list.length, info.source_rules - info.regex_rules + (info.regex_rules ? 1 : 0));
  if (!info.regex_rules) continue;
  const code = fs.readFileSync(path.join(dir, brand + '.js'), 'utf8');
  // Compile every expression even if an earlier expression matches.
  const patterns = JSON.parse(code.split('\n')[0].slice('const patterns = '.length, -1));
  assert.equal(patterns.length, info.regex_rules);
  patterns.forEach(pattern => new RegExp(pattern));
  let result;
  vm.runInNewContext(code, {$request: {hostname: 'example.com'}, $done: value => {result = value;}}, {timeout: 1000});
  assert.equal(typeof result.matched, 'boolean');
  assert.equal(result.matched, patterns.some(pattern => new RegExp(pattern).test('example.com')));
  count += patterns.length;
}
console.log(`Verified ${Object.keys(manifest.rulesets).length} sets and ${count} regex expressions`);
