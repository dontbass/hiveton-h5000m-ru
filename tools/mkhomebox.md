# Homebox: как пересобрать патч

Веб-интерфейс теста скорости (`:3300`) хранится в `/usr/bin/homebox` (go-bindata) как gzip-блоб.
1. Найти блоб с китайскими строками (`1f 8b 08` + распаковка), извлечь JS.
2. `node tools/i18n.js mkpatch translations/homebox/dict.json main.js /x main.json translations/homebox/raw.json`,
   применить, добиться **того же размера** несжатого JS (размер зашит в bindataFileInfo и уходит в Content-Length):
   в raw.json для этого обнуляются пути неиспользуемой иконки Blueprint `inbox-geo`.
3. Сжать (deflate -9) и добить gzip-заголовок полем FEXTRA до точного размера исходного блоба.
4. Блобы `*.new.bin` / `*.old.bin` + `homebox.bin.json` (op с `{file: ...}`) — в patches/homebox.
