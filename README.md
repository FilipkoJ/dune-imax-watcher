# Dune IMAX watcher

Sleduje Cinema City **Praha Flora** a pošle správu na Telegram, keď sa objaví
**IMAX** predstavenie filmu *Duna: část třetí* alebo sa uvoľní čo i len
jedno miesto. IMAX 70 mm predstavenia nemajú atribút „imax“, preto sa
rozpoznávajú podľa sály IMAX. Beží cez GitHub Actions každých ~5 minút.

## Nastavenie

1. **Telegram bot**
   - V Telegrame napíš `@BotFather` → `/newbot` → skopíruj token.
   - Napíš svojmu novému botovi ľubovoľnú správu.
   - Otvor `https://api.telegram.org/bot<TOKEN>/getUpdates` a nájdi `"chat":{"id": ...}`.
2. **GitHub**
   - Vytvor verejné repo a pushni tento priečinok.
   - Settings → Secrets and variables → Actions → pridaj
     `TELEGRAM_BOT_TOKEN` a `TELEGRAM_CHAT_ID`.
3. **Test**
   - Actions → *Watch Dune IMAX tickets* → *Run workflow* → zaškrtni *test*.

## Lokálne spustenie

```bash
cp .env.example .env   # vyplň hodnoty
set -a; source .env; set +a
python3 watcher.py --test       # testovacia správa
python3 watcher.py --dry-run    # len vypíše, čo by poslal
```
