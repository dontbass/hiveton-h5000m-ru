# Hiveton H5000M — русский перевод стоковой прошивки

Пакеты для роутера **Hiveton H5000M** со стоковой прошивкой
`ImmortalWrt 24.10-SNAPSHOT Build By Snowflakes` (сборка 20251231): переводят на русский всё,
что в ней осталось на китайском. Прошивку пересобирать не нужно.

| Пакет | Что переводит |
|---|---|
| `luci-i18n-modemwebui-ru` | Панель модема на порту `:8001` (Modem WebUI, «Powered by @Snowflakes»): экран загрузки, меню, обзор, сеть, дозвон, APN/PDP, SIM/PIN, привязка к диапазонам и сотам, SMS, AT-терминал, температура модуля, встроенные тексты Ant Design |
| `luci-i18n-quickstart-ru` | Главная страница LuCI — QuickStart (iStoreOS): карточки, мастера, тест скорости, Wi-Fi, NAS/RAID |
| `luci-i18n-qmodem-next-ru` | Раздел **Modem** в меню LuCI (QModem Next 3.0.0) |
| `luci-i18n-overlay-ru` | Заставка при бездействии (часы, CPU, память, диск, модем), всплывающие системные оповещения (тексты переведены в самой программе `system-monitor`) и страница настроек *Система → Заставка* |
| `luci-i18n-smsforward-ru` | SmsForward: шаблон пересылаемых SMS («От / Текст / Время / №» вместо «发件人 / 内容 / 时间 / 编号»), история пересылок, журнал службы |

![Обзор](docs/modemwebui-dashboard.png)

![Заставка](docs/screensaver.png)

## Установка

Скачайте `.ipk` из [Releases](../../releases/latest) и установите:

```sh
scp -O luci-i18n-*-ru_*.ipk root@192.168.88.1:/tmp/
ssh root@192.168.88.1 'opkg install /tmp/luci-i18n-*-ru_*.ipk && rm /tmp/luci-i18n-*-ru_*.ipk'
```

Или прямо на роутере (нужен доступ к GitHub):

```sh
cd /tmp
for p in modemwebui-ru_1.2.2 quickstart-ru_1.01.2 qmodem-next-ru_3.0.0 overlay-ru_1.0.0 smsforward-ru_1.0.0; do
  wget -q "https://github.com/dontbass/hiveton-h5000m-ru/releases/latest/download/luci-i18n-${p}-5_all.ipk"
done
opkg install /tmp/luci-i18n-*-ru_*.ipk && rm /tmp/luci-i18n-*-ru_*.ipk
```

Язык LuCI должен быть русским: *Система → Система → Язык и стиль*.

### Обязательно сбросьте кэш браузера

Пакеты правят файлы на месте под теми же именами. Браузер, в котором интерфейс роутера
уже открывали, продолжит показывать старые китайские версии из кэша. Это касается любого
браузера и устройства. Сбросьте кэш отдельно для LuCI (`http://192.168.88.1`) и для
панели модема (`http://192.168.88.1:8001`):

- **Chrome, Edge, Яндекс Браузер и другие на Chromium (ПК):** откройте страницу, нажмите
  **F12**, затем **правой кнопкой мыши** по кнопке «Обновить» рядом с адресной строкой →
  **«Очистка кэша и жёсткая перезагрузка»**. Пункт появляется, только пока открыты
  инструменты разработчика.
- **Firefox (ПК):** **Ctrl+Shift+R** (или **Ctrl+F5**). Если не помогло:
  замок в адресной строке → «Удалить куки и данные сайта».
- **Телефон (Chrome и др.):** замок или значок слева от адреса → «Настройки сайта» →
  «Удалить данные» (или откройте роутер в режиме инкогнито).

Удаление (оригинальные файлы восстанавливаются автоматически):

```sh
opkg remove luci-i18n-modemwebui-ru luci-i18n-quickstart-ru luci-i18n-qmodem-next-ru luci-i18n-overlay-ru luci-i18n-smsforward-ru
```

## Как это работает

- **QModem** использует стандартный механизм LuCI: в нём английские msgid, поэтому хватает
  обычного `luci-app-qmodem-next.ru.lmo`.
- **QuickStart** грузит словарь `/luci-static/quickstart/i18n/<язык>.json` (vue3-gettext);
  пакет добавляет `ru.json`. Несколько строк, вшитых прямо в код, правятся байтовым патчем.
- **SmsForward** — скомпилированная программа `/usr/bin/smsforward`. Её строки заменяются
  на месте: русский текст не длиннее китайского в байтах, остаток добивается нулями, формат
  `printf` не меняется. После установки служба перезапускается.
- **Modem WebUI** — это собранный UmiJS/React-бандл, в котором китайский вшит прямо в код
  (переключатель языка там — нерабочая заглушка шаблона). Пакет патчит бандлы на месте.

В репозитории **нет** чужого кода: только словари и байтовые патчи
(`смещение, длина, новая строка, исходная строка`). При установке
`files/ru-patch.uc` (ucode, есть в любой 24.10) сверяет md5 каждого файла с ожидаемым
оригиналом и только тогда применяет патч. При удалении пакета выполняется обратный
патч до байта, резервные копии не нужны.

Проверить состояние:

```sh
ucode /usr/share/hiveton-i18n/luci-i18n-modemwebui-ru/ru-patch.uc status /usr/share/hiveton-i18n/luci-i18n-modemwebui-ru/patches
```

`ru` — переведено, `original` — оригинал (например, после обновления пакета),
`unknown` — другая версия файла, патч к ней не подходит.

## Ограничения

- Патчи привязаны к конкретным версиям файлов (см. md5 в `patches/`). Если обновится
  `luci-app-modemwebui` или `luci-app-quickstart`, перевод этих частей слетит, а файлы
  с неизвестной контрольной суммой просто не тронутся. Пересоберите патчи (ниже)
  и пришлите PR.
- Переведён только интерфейс для модулей Quectel/FM350 (`/www/webui/webui000`).
  Отдельная копия интерфейса для MT5700M (`webui5700`) пока не переведена.
- Не переведены: текст под нерабочим переключателем языка, демо-страницы шаблона,
  которые не открываются из меню, и ответы самого модема.

## Для разработчиков

```
translations/
  qmodem-next/ru.po            перевод QModem (msgid на английском)
  quickstart/ru.json           словарь vue3-gettext для QuickStart
  quickstart/hardcoded.json    строки, вшитые в index.js
  quickstart/raw.json          мелкие правки шаблонных строк (пробелы)
  modemwebui/dict.json         китайский → русский для Modem WebUI (null = не трогать)
  modemwebui/loading.json      экран загрузки Modem WebUI
  overlay/                     заставка: словарь JS, правки страницы настроек и контроллера
  system-monitor/binary.json   строки программы system-monitor (оповещения, время работы, операторы)
patches/                       сгенерированные байтовые патчи
files/ru-patch.uc              применение/откат патчей на роутере
  smsforward/binary.json       строки программы smsforward (целиком, с \n)
tools/
  mkbinpatch.py                патч строк в бинарнике с проверкой длины и printf
  i18n.js                      extract / mkpatch на базе acorn
  mkpatches.sh                 пересборка patches/ из оригинальных файлов
  build.py, mkipk.py           сборка .ipk без SDK
```

Обновить перевод под новую версию:

1. Снимите оригиналы с роутера (до установки пакета или после `opkg remove`):
   `tar czf /tmp/src.tar.gz /www/webui/webui000/web /www/luci-static/quickstart`.
2. Распакуйте архив в каталог `dump/` и выполните `tools/mkpatches.sh dump`.
3. Найдите непереведённые строки в `/tmp/strings.json`, допишите их в
   `translations/modemwebui/dict.json` и повторите шаг 2.
4. Соберите пакеты: `python3 tools/build.py --po2lmo /path/to/po2lmo`.
   CI собирает их на каждый push; релиз создаётся автоматически, когда в файле `RELEASE` появляется новый тег (или при push тега `v*`).

## Лицензия

MIT. `translations/qmodem-next/ru.po` распространяется под MPL-2.0 (лицензия QModem).

---

*English:* Russian translation packages for the Hiveton H5000M stock firmware (Modem WebUI on
:8001, iStoreOS QuickStart, QModem Next). Web bundles are patched on the device by md5-verified,
fully reversible byte patches. No third-party code is redistributed.
