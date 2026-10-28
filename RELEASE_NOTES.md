Русский перевод стоковой прошивки Hiveton H5000M (ImmortalWrt 24.10-SNAPSHOT, Build By Snowflakes 20251231).

| Пакет | Что переводит |
|---|---|
| `luci-i18n-modemwebui-ru` | Панель модема на :8001 |
| `luci-i18n-quickstart-ru` | Главная LuCI (QuickStart) |
| `luci-i18n-qmodem-next-ru` | Раздел Modem (QModem Next 3.0.0) |

```sh
scp -O luci-i18n-*-ru_*.ipk root@192.168.88.1:/tmp/
ssh root@192.168.88.1 'opkg install /tmp/luci-i18n-*-ru_*.ipk && rm /tmp/luci-i18n-*-ru_*.ipk'
```

**После установки сбросьте кэш браузера** (Chromium: F12 → правой кнопкой по «Обновить» → «Очистка кэша и жёсткая перезагрузка»; Firefox: Ctrl+Shift+R), отдельно для LuCI и для панели :8001.

Подробности — в [README](https://github.com/dontbass/hiveton-h5000m-ru#readme).

**v1.2.0:** новый пакет `luci-i18n-overlay-ru` — заставка при бездействии, системные оповещения и страница *Система → Заставка*.

**v1.3.0:** новый пакет `luci-i18n-smsforward-ru` — пересылаемые SMS приходят с русскими подписями («От / Текст / Время / №»).
