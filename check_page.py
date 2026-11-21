"""Load index.html in headless Chromium and check it draws a sword, and a new one on click,
going through every inscription before repeating one, and none of a round's last five among
the next round's first five.

Needs Playwright (pip install playwright; playwright install chromium). Serves this directory
itself, prints the page's console and errors, saves a screenshot and exits non-zero on failure.

    python check_page.py [screenshot.png]
"""
from __future__ import annotations

import functools
import json
import http.server
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
TIMEOUT = 180_000   # ms: Pyodide, shapely and scipy take a while on a cold load


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args) -> None:
        pass


def serve() -> http.server.ThreadingHTTPServer:
    handler = functools.partial(Quiet, directory=str(HERE))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def main() -> int:
    shot = sys.argv[1] if len(sys.argv) > 1 else "sword.png"
    server = serve()
    url = f"http://127.0.0.1:{server.server_port}/index.html"
    errors: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 600, "height": 900})
        page.on("console", lambda m: print(f"[console.{m.type}] {m.text}"))
        page.on("pageerror", lambda e: (errors.append(str(e)), print(f"[pageerror] {e}")))
        page.goto(url)
        try:
            page.wait_for_selector("#sword svg polyline", timeout=TIMEOUT)
        except Exception:
            print("FAIL: no sword drawn")
            page.screenshot(path=shot)
            return 1
        # the sword's name: its title's lines after the first (TAKE THIS)
        name = lambda: " ".join(page.eval_on_selector_all("#sword text", "ts => ts.map(t => t.textContent)")[1:])
        names = [name()]
        rounds = 2 * len(json.loads((HERE / "sword_parts.json").read_text())["phrases"])
        for _ in range(rounds - 1):
            old = page.inner_html("#sword")
            page.mouse.click(20, 20)
            page.wait_for_function("old => document.querySelector('#sword').innerHTML !== old", arg=old, timeout=30_000)
            names.append(name())
            n = page.locator("#sword svg").count()
            if n != 1:
                print(f"FAIL: {n} svgs after a click, expected 1")
                return 1
        page.screenshot(path=shot)
        browser.close()
    k = rounds // 2
    first, second = names[:k], names[k:]
    if len(set(first)) != k or len(set(second)) != k:
        print(f"FAIL: an inscription repeated within a round: {names}")
        return 1
    if set(first[-5:]) & set(second[:5]):
        print(f"FAIL: a round's last five and the next's first five share {set(first[-5:]) & set(second[:5])}")
        return 1
    if errors:
        print("FAIL: page errors")
        return 1
    print(f"OK: drew a sword, redrew it on {rounds - 1} clicks, every inscription once a round; screenshot in {shot}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
