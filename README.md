# Dune IMAX watcher

Sleduje Cinema City **Praha Flora** a pošle správu na Telegram, keď sa objaví
**IMAX** predstavenie filmu *Duna: část třetí* alebo sa uvoľní čo i len
jedno miesto. IMAX 70 mm predstavenia nemajú atribút „imax“, preto sa
rozpoznávajú podľa sály IMAX. Sledujú sa len predstavenia od
`EARLIEST_DATE` (10. 1. 2027) v `watcher.py`. Beží cez GitHub Actions každých ~5 minút.

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

## Spoľahlivé spúšťanie (cron-job.org)

GitHub `schedule` pri */5 spúšťa bota len občas, preto ho každých 5 minút
spúšťa cron-job.org cez GitHub API:

- URL: `https://api.github.com/repos/FilipkoJ/dune-imax-watcher/actions/workflows/watch.yml/dispatches`
- Metóda: `POST`, body: `{"ref":"main"}`
- Hlavičky: `Authorization: Bearer <TOKEN>`, `Accept: application/vnd.github+json`,
  `X-GitHub-Api-Version: 2022-11-28`, `Content-Type: application/json`
- Token: fine-grained, len toto repo, oprávnenie **Actions: Read and write**.
- Úspešné volanie vráti `204 No Content`.
