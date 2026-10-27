// usage:
//   node i18n.js extract <out.json> file1.js file2.js ...
//   node i18n.js patch <dict.json> <srcdir> <dstdir> file1.js ...   (dict: {zh: ru|null})
const fs = require('fs');
const path = require('path');
const acorn = require('acorn');
const walk = require('acorn-walk');

const HAN = /[一-鿿]/;

function parse(src) {
  const opts = { ecmaVersion: 'latest', allowHashBang: true, allowReturnOutsideFunction: true,
    allowAwaitOutsideFunction: true, allowImportExportEverywhere: true };
  try { return acorn.parse(src, { ...opts, sourceType: 'module' }); }
  catch (e) { return acorn.parse(src, { ...opts, sourceType: 'script' }); }
}

function collect(src) {
  const ast = parse(src);
  const items = [];
  walk.fullAncestor(ast, (node, state, ancestors) => {
    const parent = ancestors[ancestors.length - 2];
    let ctx = parent ? parent.type : '';
    if (parent && parent.type === 'BinaryExpression') ctx += ':' + parent.operator;
    if (parent && parent.type === 'Property' && parent.key === node) ctx = 'PropertyKey';
    if (node.type === 'Literal' && typeof node.value === 'string' && HAN.test(node.value)) {
      items.push({ kind: 'lit', start: node.start, end: node.end, value: node.value, quote: src[node.start], ctx });
    } else if (node.type === 'TemplateElement' && node.value.cooked && HAN.test(node.value.cooked)) {
      items.push({ kind: 'tpl', start: node.start, end: node.end, value: node.value.cooked, ctx });
    }
  });
  return items;
}

function esc(t, quote) {
  let o = '';
  for (const ch of t) {
    const c = ch.codePointAt(0);
    if (ch === '\\') o += '\\\\';
    else if (ch === quote) o += '\\' + ch;
    else if (ch === '\n') o += '\\n';
    else if (ch === '\r') o += '\\r';
    else if (quote === '`' && ch === '$') o += '\\$';
    else if (c >= 32 && c < 127) o += ch;
    else if (c > 0xffff) { const v = c - 0x10000; o += '\\u' + (0xd800 + (v >> 10)).toString(16).toUpperCase().padStart(4, '0') + '\\u' + (0xdc00 + (v & 0x3ff)).toString(16).toUpperCase().padStart(4, '0'); }
    else o += '\\u' + c.toString(16).toUpperCase().padStart(4, '0');
  }
  return o;
}

const [cmd, ...args] = process.argv.slice(2);
if (cmd === 'extract') {
  const [out, ...files] = args;
  const res = {};
  for (const f of files) {
    const src = fs.readFileSync(f, 'utf8');
    res[path.basename(f)] = collect(src).map(({ kind, value, ctx, quote }) => ({ kind, value, ctx, quote }));
  }
  fs.writeFileSync(out, JSON.stringify(res, null, 0));
} else if (cmd === 'patch') {
  const [dictFile, srcdir, dstdir, ...files] = args;
  const dict = JSON.parse(fs.readFileSync(dictFile, 'utf8'));
  const report = {};
  for (const f of files) {
    let src = fs.readFileSync(path.join(srcdir, f), 'utf8');
    const items = collect(src).sort((a, b) => b.start - a.start);
    let n = 0, miss = 0;
    for (const it of items) {
      const tr = dict[it.value];
      if (tr === undefined) { miss++; continue; }
      if (tr === null) continue;
      let rep;
      if (it.kind === 'lit') rep = it.quote + esc(tr, it.quote) + it.quote;
      else rep = esc(tr, '`');
      src = src.slice(0, it.start) + rep + src.slice(it.end);
      n++;
    }
    parse(src); // must still parse
    fs.mkdirSync(dstdir, { recursive: true });
    fs.writeFileSync(path.join(dstdir, f), src);
    report[f] = { replaced: n, untranslated: miss };
  }
  console.log(JSON.stringify(report, null, 1));
} else if (cmd === 'mkpatch') {
  // node i18n.js mkpatch <dict.json> <srcfile> <target-path-on-router> <out.json> [raw.json]
  const crypto = require('crypto');
  const [dictFile, srcFile, target, outFile, rawFile] = args;
  const dict = JSON.parse(fs.readFileSync(dictFile, 'utf8'));
  const raw = rawFile ? JSON.parse(fs.readFileSync(rawFile, 'utf8')) : [];
  const origBuf = fs.readFileSync(srcFile);
  const src = origBuf.toString('utf8');
  if (Buffer.compare(Buffer.from(src, 'utf8'), origBuf) !== 0) throw new Error('not clean utf8');
  const reps = [];
  for (const it of collect(src)) {
    const tr = dict[it.value];
    if (tr === undefined || tr === null) continue;
    if (it.kind === 'lit') reps.push([it.start, it.end, it.quote + esc(tr, it.quote) + it.quote]);
    else reps.push([it.start, it.end, esc(tr, '`')]);
  }
  for (const [o, n] of raw) { // exact raw substring replacements
    let i = -1;
    while ((i = src.indexOf(o, i + 1)) !== -1) reps.push([i, i + o.length, n]);
  }
  reps.sort((a, b) => a[0] - b[0]);
  for (let i = 1; i < reps.length; i++) if (reps[i][0] < reps[i - 1][1]) throw new Error('overlap at ' + reps[i][0]);
  // build result + byte ops
  let out = '', last = 0, byteLast = 0;
  const ops = [];
  for (const [s, e, n] of reps) {
    const pre = src.slice(last, s);
    byteLast += Buffer.byteLength(pre);
    const oldB = Buffer.byteLength(src.slice(s, e));
    ops.push([byteLast, oldB, n, src.slice(s, e)]);
    byteLast += oldB;
    out += pre + n; last = e;
  }
  out += src.slice(last);
  parse(out);
  const md5 = b => crypto.createHash('md5').update(b).digest('hex');
  const res = { target, orig_md5: md5(origBuf), orig_size: origBuf.length, new_md5: md5(Buffer.from(out, 'utf8')), ops };
  fs.writeFileSync(outFile, JSON.stringify(res));
  console.log(target, 'ops', ops.length);
}
