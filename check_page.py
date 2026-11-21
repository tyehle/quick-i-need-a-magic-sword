"""Load index.html in headless Chromium and check it draws a sword, and a new one on click.

Needs Playwright (pip install playwright; playwright install chromium). Serves this directory
itself, prints the page's console and errors, saves a screenshot and exits non-zero on failure.

    python check_page.py [screenshot.png]
"""
from __future__ import annotations

import functools
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
        first = page.inner_html("#sword")
        page.mouse.click(20, 20)
        page.wait_for_function("old => document.querySelector('#sword').innerHTML !== old", arg=first, timeout=30_000)
        n = page.locator("#sword svg").count()
        page.screenshot(path=shot)
        browser.close()
    if n != 1:
        print(f"FAIL: {n} svgs after a click, expected 1")
        return 1
    if errors:
        print("FAIL: page errors")
        return 1
    print(f"OK: drew a sword, redrew it on click; screenshot in {shot}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
