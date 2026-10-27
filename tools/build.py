#!/usr/bin/env python3
"""Build .ipk packages from translations/ and patches/.

usage: tools/build.py --po2lmo /path/to/po2lmo [--out dist]
"""
import argparse
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import mkipk  # noqa: E402

REL = open(os.path.join(ROOT, 'VERSION')).read().strip()
CLEAR = 'rm -rf /tmp/luci-indexcache* /tmp/luci-modulecache 2>/dev/null\n'


def read(p, mode='rb'):
    with open(os.path.join(ROOT, p), mode) as f:
        return f.read()


def overlay_scripts(name):
    d = f'/usr/share/hiveton-i18n/{name}'
    return {
        'postinst': '#!/bin/sh\n[ -n "$IPKG_INSTROOT" ] && exit 0\n'
                    f'ucode {d}/ru-patch.uc apply {d}/patches\n' + CLEAR + 'exit 0\n',
        'prerm': '#!/bin/sh\n[ -n "$IPKG_INSTROOT" ] && exit 0\n'
                 f'ucode {d}/ru-patch.uc restore {d}/patches\n' + CLEAR + 'exit 0\n',
    }


def overlay_files(name, patchdir):
    d = f'/usr/share/hiveton-i18n/{name}'
    files = {f'{d}/ru-patch.uc': (read('files/ru-patch.uc'), 0o755)}
    for fn in sorted(os.listdir(os.path.join(ROOT, patchdir))):
        if fn.endswith('.json'):
            files[f'{d}/patches/{fn}'] = read(os.path.join(patchdir, fn))
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--po2lmo', required=True)
    ap.add_argument('--out', default=os.path.join(ROOT, 'dist'))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    built = []

    # 1. QModem Next: plain LuCI translation
    with tempfile.TemporaryDirectory() as td:
        lmo = os.path.join(td, 'ru.lmo')
        subprocess.check_call([a.po2lmo, os.path.join(ROOT, 'translations/qmodem-next/ru.po'), lmo])
        built.append(mkipk.build(
            a.out, 'luci-i18n-qmodem-next-ru', f'3.0.0-{REL}', 'luci-app-qmodem-next',
            'Russian translation for luci-app-qmodem-next',
            {'/usr/lib/lua/luci/i18n/luci-app-qmodem-next.ru.lmo': open(lmo, 'rb').read()},
            {'postinst': '#!/bin/sh\n[ -n "$IPKG_INSTROOT" ] && exit 0\n' + CLEAR + 'exit 0\n',
             'postrm': '#!/bin/sh\n' + CLEAR + 'exit 0\n'}))

    # 2. QuickStart: ru.json + byte patch for hardcoded strings
    name = 'luci-i18n-quickstart-ru'
    files = overlay_files(name, 'patches/quickstart')
    files['/www/luci-static/quickstart/i18n/ru.json'] = read('translations/quickstart/ru.json')
    built.append(mkipk.build(
        a.out, name, f'1.01.2-{REL}', 'luci-app-quickstart, ucode, ucode-mod-fs',
        'Russian translation for luci-app-quickstart (iStoreOS QuickStart)',
        files, overlay_scripts(name)))

    # 3. Modem WebUI (port 8001)
    name = 'luci-i18n-modemwebui-ru'
    built.append(mkipk.build(
        a.out, name, f'1.2.2-{REL}', 'luci-app-modemwebui, ucode, ucode-mod-fs',
        'Russian translation for Modem WebUI (port 8001, Quectel/FM350 webui000)',
        overlay_files(name, 'patches/modemwebui'), overlay_scripts(name)))

    # 4. Screensaver / system alerts overlay (luci-overlay + system-monitor)
    name = 'luci-i18n-overlay-ru'
    built.append(mkipk.build(
        a.out, name, f'1.0.0-{REL}', 'ucode, ucode-mod-fs',
        'Russian translation for the LuCI screensaver / system alerts overlay',
        overlay_files(name, 'patches/overlay'), overlay_scripts(name)))

    for b in built:
        print(b)


if __name__ == '__main__':
    main()
