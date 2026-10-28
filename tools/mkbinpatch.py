#!/usr/bin/env python3
"""Make an in-place string patch for a compiled binary.

usage: tools/mkbinpatch.py <dict.json> <original-binary> <target-path> <out.json>

dict.json maps whole NUL-terminated C strings (zh) to replacements (ru).
A replacement must fit into the original byte length (it is NUL-padded),
keep the same printf specifiers, and the original must occur exactly once.
"""
import hashlib, json, re, sys

dict_file, src, target, out = sys.argv[1:5]
d = json.load(open(dict_file, encoding='utf-8'))
b = open(src, 'rb').read()
spec = re.compile(r'%[-+ #0-9.]*l*[sdufxXc]')
ops, errors = [], 0
for zh, ru in d.items():
    zb, rb = zh.encode(), ru.encode()
    occ = [m.start() + 1 for m in re.finditer(re.escape(b'\0' + zb + b'\0'), b)]
    if len(occ) != 1:
        print(f'skip (found {len(occ)}x): {zh!r}'); errors += 1; continue
    if len(rb) > len(zb):
        print(f'too long ({len(rb)} > {len(zb)} bytes): {ru!r}'); errors += 1; continue
    if spec.findall(zh) != spec.findall(ru):
        print(f'format mismatch: {zh!r} -> {ru!r}'); errors += 1; continue
    ops.append([occ[0], len(zb), (rb + b'\0' * (len(zb) - len(rb))).decode('utf-8'), zh])
ops.sort()
nb = bytearray(b)
for off, ln, new, _ in ops:
    nb[off:off + ln] = new.encode()
json.dump({'target': target, 'orig_md5': hashlib.md5(b).hexdigest(), 'orig_size': len(b),
           'new_md5': hashlib.md5(nb).hexdigest(), 'ops': ops},
          open(out, 'w', encoding='utf-8'), ensure_ascii=False)
print(target, 'ops', len(ops), 'errors', errors)
sys.exit(1 if errors else 0)
