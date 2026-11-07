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

// Numbered JMS-style names need user-supplied geography. These are fixtures,
// not a country lookup for a real JMS plan or subscription.
const numberedNames = ['LA-1 洛杉矶', 'LA-2 洛杉矶', 'LA-GIA 洛杉矶', 'Osaka 大阪', 'NL 荷兰'];
const numbered = numberedNames.map((_, index) =>
  `shadowsocks=192.0.2.${index + 20}:1234, method=aes-128-gcm, password=example-password, tag=c123s${index + 1}`
).join('\n');
// Encode only field values; @ and + are parser syntax and stay literal.
const fragment = '#rename=' + numberedNames.map((name, index) =>
  `c123s${index + 1}@${encodeURIComponent(name)}`
).join('+') + '&emoji=1';
const renamedOutput = parse('server', numbered, 'https://example.invalid/numbered-fixture' + fragment);
const renamed = renamedOutput.startsWith('shadowsocks=')
  ? renamedOutput : Buffer.from(renamedOutput, 'base64').toString('utf8');
const renamedTags = renamed.split('\n').map(node => node.split('tag=')[1].trim());
assert.deepEqual(renamedTags, numberedNames.map((name, index) =>
  `${['🇺🇸', '🇺🇸', '🇺🇸', '🇯🇵', '🇳🇱'][index]} ${name}`
));

// Explicit flags also work without the automatic emoji parameter. This covers
// the alternative for a device where renaming succeeds but flags are missing.
const explicitFragment = '#rename=' + renamedTags.map((name, index) =>
  `c123s${index + 1}@${encodeURIComponent(name)}`
).join('+');
const explicitOutput = parse('server', numbered, 'https://example.invalid/explicit-flag-fixture' + explicitFragment);
const explicitNodes = explicitOutput.startsWith('shadowsocks=')
  ? explicitOutput : Buffer.from(explicitOutput, 'base64').toString('utf8');
const explicitTags = explicitNodes.split('\n').map(node => node.split('tag=')[1].trim());
assert.deepEqual(explicitTags, renamedTags);

// rename replaces a substring; replace can remove the complete tag value.
// A comma + tag field boundary prevents matching identifiers in credentials,
// hosts or other connection fields. Word boundaries keep s1 distinct from s10.
const compactTags = ['🇺🇸 洛杉矶①', '🇺🇸 洛杉矶②', '🇺🇸 洛杉矶③', '🇯🇵 大阪', '🇳🇱 荷兰'];
const compactFragment = '#replace=' + compactTags.map((name, index) =>
  `(%2C%5Cs*tag=)[^%2C]*%5Cbc123s${index + 1}%5Cb[^%2C]*@$1${name.replaceAll(' ', '%20')}`
).join('+');
assert.ok(fs.readFileSync(`${__dirname}/README.md`, 'utf8').includes(compactFragment),
  'The published copyable fragment must match the integration fixture');
const paddedNames = [
  ...compactTags.map((_, index) => `JMS LA500 - c123s${index + 1}.example.invalid - SS - 1x`),
  'JMS-1234567@c123s801.example.invalid:443',
  'JMS c123s10 - unknown',
  'other c999s1 - unchanged',
];
const paddedNodes = paddedNames.map((name, index) =>
  `shadowsocks=c123s1-${index}.example.invalid:1234, method=aes-128-gcm, password=tag=c123s2, tag=${name}, udp-relay=true, fast-open=false`
).join('\n');
function native(result) {
  return result.startsWith('shadowsocks=') ? result : Buffer.from(result, 'base64').toString('utf8');
}
const baseline = native(parse('server', paddedNodes, 'https://example.invalid/padded-fixture')).split('\n');
const compact = native(parse('server', paddedNodes,
  'https://example.invalid/padded-fixture' + compactFragment)).split('\n');
const compactActual = compact.map(node => node.match(/(?:^|,\s*)tag=([^,]*)/)[1].trim());
assert.deepEqual(compactActual, [...compactTags, ...paddedNames.slice(5)]);
const withoutTag = node => node.replace(/(,\s*tag=)[^,]*/, '$1<name>');
assert.deepEqual(compact.map(withoutTag), baseline.map(withoutTag));
assert.equal(compact.length, paddedNames.length);
for (const node of compact) {
  assert.match(node, /password=tag=c123s2,/);
  assert.match(node, /udp-relay=true,/);
  assert.match(node, /fast-open=false,/);
}

// The optional s801 mapping labels a purpose without inventing geography or a
// current traffic multiplier. The five-node fragment alone leaves it unchanged.
const downloadSuffix = '+(%2C%5Cs*tag=)[^%2C]*%5Cbc123s801%5Cb[^%2C]*@$1📥%20下载';
assert.ok(fs.readFileSync(`${__dirname}/README.md`, 'utf8').includes(downloadSuffix));
const download = native(parse('server', paddedNodes,
  'https://example.invalid/download-fixture' + compactFragment + downloadSuffix)).split('\n');
const downloadTags = download.map(node => node.match(/(?:^|,\s*)tag=([^,]*)/)[1].trim());
assert.deepEqual(downloadTags, [...compactTags, '📥 下载', ...paddedNames.slice(6)]);
assert.deepEqual(download.map(withoutTag), baseline.map(withoutTag));
process.stdout.write(JSON.stringify({ siri, nodes: 2, renamed_jms_tags: renamedTags,
  explicit_flag_tags: explicitTags, compact_jms_tags: compactActual,
  compact_connection_fields_unchanged: true, download_jms_tags: downloadTags,
  download_connection_fields_unchanged: true }));
