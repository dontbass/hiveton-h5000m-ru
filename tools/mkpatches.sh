#!/bin/sh
# Regenerate byte patches from ORIGINAL files taken from the router.
# usage: tools/mkpatches.sh <dump-root>
#   <dump-root> must contain the original files at their router paths, e.g.
#   <dump-root>/www/webui/webui000/web/*.js
#   <dump-root>/www/webui/webui000/web/scripts/loading.js
#   <dump-root>/www/luci-static/quickstart/index.js
# On the router:  tar czf /tmp/src.tar.gz /www/webui/webui000/web /www/luci-static/quickstart
set -e
D="$1"; [ -d "$D" ] || { echo "usage: $0 <dump-root>"; exit 1; }
cd "$(dirname "$0")/.."
[ -d tools/node_modules ] || (cd tools && npm install --silent)

rm -f patches/quickstart/*.json patches/modemwebui/*.json
node tools/i18n.js mkpatch translations/quickstart/hardcoded.json \
  "$D/www/luci-static/quickstart/index.js" /www/luci-static/quickstart/index.js \
  patches/quickstart/index.js.json translations/quickstart/raw.json

for f in "$D"/www/webui/webui000/web/*.js; do
  b=$(basename "$f")
  node tools/i18n.js mkpatch translations/modemwebui/dict.json "$f" \
    "/www/webui/webui000/web/$b" "patches/modemwebui/$b.json"
done
echo '{}' > /tmp/empty-dict.json
node tools/i18n.js mkpatch /tmp/empty-dict.json "$D/www/webui/webui000/web/scripts/loading.js" \
  /www/webui/webui000/web/scripts/loading.js patches/modemwebui/scripts_loading.js.json \
  translations/modemwebui/loading.json
# drop empty patches
for p in patches/*/*.json; do
  grep -q '"ops":\[\]' "$p" && rm -f "$p"
done
# list strings still untranslated
node tools/i18n.js extract /tmp/strings.json "$D"/www/webui/webui000/web/*.js
echo "done; full string list: /tmp/strings.json"
