#!/usr/bin/env python3
"""Minimal OpenWrt .ipk builder (opkg tar.gz format)."""
import io, os, tarfile, time, gzip


def _tar_gz(entries):
    """entries: list of (arcname, bytes|None(dir), mode)"""
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode='wb', mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode='w', format=tarfile.GNU_FORMAT) as tf:
            for name, data, mode in entries:
                ti = tarfile.TarInfo(name)
                ti.uid = ti.gid = 0
                ti.uname = ti.gname = 'root'
                ti.mtime = int(time.time())
                ti.mode = mode
                if data is None:
                    ti.type = tarfile.DIRTYPE
                    tf.addfile(ti)
                else:
                    ti.size = len(data)
                    tf.addfile(ti, io.BytesIO(data))
    return buf.getvalue()


def build(out_dir, name, version, depends, description, files, scripts=None, conffiles=None):
    """files: dict target_path -> bytes (or (bytes, mode))."""
    scripts = scripts or {}
    dirs = set()
    data_entries = []
    size = 0
    for target in sorted(files):
        v = files[target]
        data, mode = (v if isinstance(v, tuple) else (v, 0o644))
        parts = target.strip('/').split('/')
        for i in range(1, len(parts)):
            dirs.add('./' + '/'.join(parts[:i]) + '/')
        data_entries.append(('./' + target.strip('/'), data, mode))
        size += len(data)
    entries = [('./', None, 0o755)] + [(d, None, 0o755) for d in sorted(dirs)] + data_entries
    data_tgz = _tar_gz(entries)

    control = (
        f"Package: {name}\n"
        f"Version: {version}\n"
        f"Depends: {depends}\n"
        f"Source: hiveton-i18n-ru\n"
        f"SourceName: {name}\n"
        f"License: MIT\n"
        f"Section: luci\n"
        f"Maintainer: Vladimir\n"
        f"Architecture: all\n"
        f"Installed-Size: {size}\n"
        f"Description: {description}\n"
    ).encode()
    centries = [('./', None, 0o755), ('./control', control, 0o644)]
    if conffiles:
        centries.append(('./conffiles', ('\n'.join(conffiles) + '\n').encode(), 0o644))
    for sname, body in scripts.items():
        centries.append(('./' + sname, body.encode(), 0o755))
    control_tgz = _tar_gz(centries)

    outer = _tar_gz([
        ('./debian-binary', b'2.0\n', 0o644),
        ('./data.tar.gz', data_tgz, 0o644),
        ('./control.tar.gz', control_tgz, 0o644),
    ])
    fn = os.path.join(out_dir, f"{name}_{version}_all.ipk")
    with open(fn, 'wb') as f:
        f.write(outer)
    return fn
