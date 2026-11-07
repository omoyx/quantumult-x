// Run the fetched public KOP parser with QX globals and entirely fictional nodes.
// These API mocks test compatibility; Node vm is not a security isolation boundary.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));

function parse(type, content, link) {
  const results = [];
  const context = vm.createContext({
    $resource: { type, content, link, tag: 'Public integration fixture' },
    $environment: { version: 'Quantumult X v1.5.6 build918' },
    $done: value => results.push(value),
    $notify: () => {},
    console: { log: () => {} },
  });
  vm.runInContext(input.parser, context, { timeout: 5000 });
  const result = results.at(-1)?.content;
  assert.equal(typeof result, 'string');
  assert.ok(result.length > 0);
  return result;
}
const siri = parse('filter', input.siri,
  'https://raw.githubusercontent.com/byx020119/Shadowrocket-Siri/main/siri3.list');
const fictional = [
  'ss://YWVzLTEyOC1nY206ZXhhbXBsZS1wYXNzd29yZA@192.0.2.10:1234#US-test',
  'ss://YWVzLTEyOC1nY206ZXhhbXBsZS1wYXNzd29yZA@192.0.2.11:1234#JP-test',
].join('\n');
const nodeOutput = parse('server', fictional, 'https://example.invalid/public-fixture');
// QX accepts the parser's Base64-encoded native node subscription.
const nodes = nodeOutput.startsWith('shadowsocks=')
  ? nodeOutput : Buffer.from(nodeOutput, 'base64').toString('utf8');
assert.equal(nodes.split('\n').length, 2);
assert.match(nodes, /tag=US-test/);
assert.match(nodes, /tag=JP-test/);
process.stdout.write(JSON.stringify({ siri, nodes: 2 }));
