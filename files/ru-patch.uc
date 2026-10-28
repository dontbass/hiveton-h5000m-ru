#!/usr/bin/ucode -S
// Applies / reverts byte patches with Russian strings to web UI bundles.
// usage: ucode ru-patch.uc apply|restore|status <patch-dir>
// Patch file (JSON): { target, orig_md5, orig_size, new_md5, ops: [[offset, oldlen, new, old], ...] }
// offsets/lengths are bytes relative to the ORIGINAL file.

'use strict';

import * as fs from 'fs';

function md5(path) {
	let p = fs.popen(sprintf("md5sum '%s' 2>/dev/null", replace(path, "'", "'\\''")), 'r');
	if (!p) return null;
	let line = p.read('line');
	p.close();
	let m = match(line ?? '', /^([0-9a-f]{32})/);
	return m ? m[1] : null;
}

function apply_ops(data, ops) {
	let out = [], pos = 0;
	for (let op in ops) {
		push(out, substr(data, pos, op[0] - pos), op[2]);
		pos = op[0] + op[1];
	}
	push(out, substr(data, pos));
	return join('', out);
}

function revert_ops(data, ops) {
	let out = [], pos = 0, delta = 0;
	for (let op in ops) {
		let start = op[0] + delta, newlen = length(op[2]);
		push(out, substr(data, pos, start - pos), op[3]);
		pos = start + newlen;
		delta += newlen - op[1];
	}
	push(out, substr(data, pos));
	return join('', out);
}

function write_atomic(path, data) {
	// write to a temp file and rename over the target: keeps working for
	// running executables and preserves the original permission bits
	let tmp = path + '.ru-tmp', st = fs.stat(path);
	if (fs.writefile(tmp, data) == null) return false;
	if (st) {
		let mode = st.mode & 4095;
		if (type(fs.chmod) != 'function' || !fs.chmod(tmp, mode))
			system(sprintf("chmod %o '%s'", mode, replace(tmp, "'", "'\\''")));
	}
	return fs.rename(tmp, path) != null;
}

let mode = ARGV[0] ?? 'status', dir = ARGV[1];
if (!dir) { warn('usage: ru-patch.uc apply|restore|status <patch-dir>\n'); exit(2); }

let files = filter(fs.lsdir(dir) ?? [], f => match(f, /\.json$/));
for (let pf in sort(files)) {
	pf = dir + '/' + pf;
	let p = json(fs.readfile(pf));
	let t = p.target, cur = md5(t);
	if (cur == null) { print(`missing: ${t}\n`); continue; }

	if (mode == 'apply') {
		if (cur == p.new_md5) { print(`already: ${t}\n`); continue; }
		if (cur != p.orig_md5) { print(`SKIP (other version): ${t}\n`); continue; }
		let res = apply_ops(fs.readfile(t), p.ops);
		if (write_atomic(t, res) && md5(t) == p.new_md5) print(`patched: ${t}\n`);
		else print(`ERROR: ${t}\n`);
	}
	else if (mode == 'restore') {
		if (cur != p.new_md5) continue;
		let res = revert_ops(fs.readfile(t), p.ops);
		if (write_atomic(t, res) && md5(t) == p.orig_md5) print(`restored: ${t}\n`);
		else print(`ERROR: ${t}\n`);
	}
	else {
		print(`${cur == p.new_md5 ? 'ru' : (cur == p.orig_md5 ? 'original' : 'unknown')}: ${t}\n`);
	}
}
