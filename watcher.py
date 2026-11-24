"""Watches Cinema City Praha Flora for IMAX screenings of Dune: Part Three
and sends a Telegram message when new ones appear or seats free up.

IMAX 70mm screenings are not tagged "imax"; they are recognised by the IMAX hall."""

import argparse
import json
import os
import sys
import unicodedata
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

API = "https://www.cinemacity.cz/cz/data-api-service/v1/quickbook/10101"
CINEMA_ID = "1052"  # Praha Flora
UNTIL = "2027-12-31"
STATE_FILE = Path(__file__).with_name("state.json")
USER_AGENT = "Mozilla/5.0 (dune-imax-watcher)"
IMAX_SEATS = 385  # derived from availabilityRatio steps (1 seat ~ 0.0026)


def normalize(text: str) -> str:
    stripped = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return stripped.lower()


def is_target_film(name: str) -> bool:
    n = normalize(name)
    return "duna" in n and "tret" in n


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def fetch_screenings(attribute: str) -> dict[str, dict]:
    today = date.today().isoformat()
    dates_url = f"{API}/dates/in-cinema/{CINEMA_ID}/until/{UNTIL}?attr=&lang=cs_CZ"
    dates = [d for d in get_json(dates_url)["body"]["dates"] if d >= today]

    screenings: dict[str, dict] = {}
    for day in dates:
        url = f"{API}/film-events/in-cinema/{CINEMA_ID}/at-date/{day}?attr=&lang=cs_CZ"
        body = get_json(url)["body"]
        films = {f["id"]: f["name"] for f in body["films"]}
        for event in body["events"]:
            name = films.get(event["filmId"], "")
            in_imax_hall = attribute == "imax" and event.get("auditoriumTinyName") == "IMAX"
            if not is_target_film(name) or not (in_imax_hall or attribute in event["attributeIds"]):
                continue
            screenings[event["id"]] = {
                "film": name,
                "time": event["eventDateTime"],
                "soldOut": event["soldOut"],
                "free_seats": round(event.get("availabilityRatio", 0) * IMAX_SEATS),
                "link": event["bookingLink"],
                "attributes": event["attributeIds"],
            }
    return screenings


def load_state() -> dict[str, dict]:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict[str, dict]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def format_screening(s: dict) -> str:
    day, time = s["time"].split("T")
    extras = ", ".join(a for a in s["attributes"] if a in ("2d", "3d", "70-mm", "dolby-atmos", "4dx"))
    status = "VYPREDANÉ" if s["soldOut"] else f"voľné ~{s['free_seats']} miest"
    return f"• {day} {time[:5]} ({extras}) – {status}\n  {s['link']}"


def send_telegram(text: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("[telegram not configured] would send:\n" + text)
        return
    data = urllib.parse.urlencode(
        {"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"}
    ).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data)
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Telegram API returned {resp.status}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="send a test Telegram message and exit")
    parser.add_argument("--attr", default="imax", help="screening attribute to watch (default: imax)")
    parser.add_argument("--dry-run", action="store_true", help="do not save state or send messages")
    args = parser.parse_args()

    if args.test:
        send_telegram("✅ Dune IMAX watcher je nastavený a funguje.")
        return 0

    current = fetch_screenings(args.attr)
    previous = load_state()

    new = [s for sid, s in current.items() if sid not in previous]
    freed = [
        s for sid, s in current.items()
        if sid in previous and not s["soldOut"] and (
            previous[sid]["soldOut"]
            or s["free_seats"] > previous[sid].get("free_seats", 0)
        )
    ]
    print(f"Found {len(current)} matching screenings ({len(new)} new, {len(freed)} freed up).")

    lines: list[str] = []
    if new:
        lines.append(f"🎬 Nové {args.attr.upper()} predstavenia Duna: část třetí – Flora!")
        lines += [format_screening(s) for s in sorted(new, key=lambda s: s["time"])]
    if freed:
        lines.append("🎟 Uvoľnili sa miesta v IMAXe na Dunu 3:")
        lines += [format_screening(s) for s in sorted(freed, key=lambda s: s["time"])]

    if args.dry_run:
        print("\n".join(lines) or "Nothing to notify.")
        return 0

    if lines:
        send_telegram("\n".join(lines))
    if current != previous:
        save_state(current)
    return 0


if __name__ == "__main__":
    sys.exit(main())
