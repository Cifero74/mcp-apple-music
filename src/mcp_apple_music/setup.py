"""
Apple Music MCP — One-time Setup Wizard
========================================
Run this script ONCE to:
  1. Enter your Apple Developer credentials (Team ID, Key ID, .p8 path).
  2. Authorise your Apple Music account via a local browser page.
  3. Save everything to ~/.config/mcp-apple-music/config.json

Usage:
    python setup_auth.py
    # or, after installation:
    mcp-apple-music-setup
"""

import json
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

import jwt

CONFIG_DIR = Path.home() / ".config" / "mcp-apple-music"
CONFIG_PATH = CONFIG_DIR / "config.json"
PORT = 8888

# ------------------------------------------------------------------ #
#  HTML page served to the browser                                    #
# ------------------------------------------------------------------ #

_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Apple Music MCP — Setup</title>
  <script src="https://js-cdn.music.apple.com/musickit/v3/musickit.js"
          data-web-components async></script>
  <style>
    * { box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f5f5f7;
      display: flex; justify-content: center; align-items: center;
      min-height: 100vh; margin: 0; padding: 20px;
    }
    .card {
      background: white; border-radius: 18px; padding: 48px 40px;
      max-width: 480px; width: 100%; text-align: center;
      box-shadow: 0 4px 30px rgba(0,0,0,0.08);
    }
    .logo { font-size: 56px; margin-bottom: 16px; }
    h1 { font-size: 22px; font-weight: 600; margin: 0 0 8px; }
    p  { color: #6e6e73; font-size: 15px; line-height: 1.5; margin: 0 0 32px; }
    button {
      background: #fc3c44; color: white; border: none;
      padding: 14px 32px; border-radius: 980px;
      font-size: 16px; font-weight: 500; cursor: pointer;
      transition: background .2s;
    }
    button:hover:not(:disabled) { background: #d92e35; }
    button:disabled { background: #c7c7cc; cursor: default; }
    #status {
      margin-top: 24px; font-size: 14px; color: #6e6e73; min-height: 20px;
    }
    .ok   { color: #34c759 !important; font-weight: 600; }
    .err  { color: #ff3b30 !important; }
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">🎵</div>
    <h1>Apple Music MCP</h1>
    <p>Click the button below to authorise Claude to access your Apple Music library.</p>
    <button id="btn">Authorise Apple Music</button>
    <div id="status">Waiting…</div>
  </div>

  <script>
    document.addEventListener('musickitloaded', async () => {
      try {
        await MusicKit.configure({
          developerToken: '{{DEVELOPER_TOKEN}}',
          app: { name: 'MCP Apple Music', build: '1.0.0' }
        });
        document.getElementById('status').textContent = 'Ready — click the button to continue.';
      } catch (e) {
        document.getElementById('status').textContent = 'Error configuring MusicKit: ' + e.message;
        document.getElementById('status').className = 'err';
        document.getElementById('btn').disabled = true;
      }
    });

    document.getElementById('btn').addEventListener('click', async () => {
      const btn    = document.getElementById('btn');
      const status = document.getElementById('status');
      btn.disabled = true;
      status.textContent = 'Authorising… (sign in with your Apple ID if prompted)';
      status.className   = '';

      try {
        const music     = MusicKit.getInstance();
        const userToken = await music.authorize();

        status.textContent = 'Saving token…';
        const res = await fetch('/save_token', {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify({ token: userToken })
        });

        if (res.ok) {
          status.textContent = '✅  All done! You can close this tab and return to the terminal.';
          status.className   = 'ok';
        } else {
          throw new Error('Server responded with ' + res.status);
        }
      } catch (e) {
        status.textContent = 'Error: ' + e.message;
        status.className   = 'err';
        btn.disabled       = false;
      }
    });
  </script>
</body>
</html>
"""

# ------------------------------------------------------------------ #
#  Local HTTP server                                                  #
# ------------------------------------------------------------------ #

_token_event: threading.Event = threading.Event()
_received_token: list[str] = []


class _Handler(BaseHTTPRequestHandler):
    """Minimal HTTP handler: serves the auth page and receives the token."""

    html: str = ""  # set on the class before starting the server

    def do_GET(self) -> None:
        if urlparse(self.path).path == "/":
            body = self.html.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:
        if urlparse(self.path).path == "/save_token":
            length = int(self.headers.get("Content-Length", 0))
            data   = json.loads(self.rfile.read(length))
            _received_token.append(data["token"])

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')

            _token_event.set()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *_) -> None:  # silence access logs
        pass


# ------------------------------------------------------------------ #
#  Config helpers                                                     #
# ------------------------------------------------------------------ #


def _load_existing() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}


def _save_config(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)
    CONFIG_PATH.chmod(0o600)  # owner read/write only


def _ask(prompt: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    value = input(f"{prompt}{hint}: ").strip()
    return value or default


def _generate_developer_token(cfg: dict) -> str:
    key_path = Path(cfg["private_key_path"]).expanduser()
    with open(key_path) as f:
        private_key = f.read()
    now = int(time.time())
    return jwt.encode(
        {"iss": cfg["team_id"], "iat": now, "exp": now + 15_777_000},
        private_key,
        algorithm="ES256",
        headers={"kid": cfg["key_id"]},
    )


# ------------------------------------------------------------------ #
#  Main                                                               #
# ------------------------------------------------------------------ #


def main() -> None:
    print("\n🎵  Apple Music MCP — Setup Wizard\n" + "─" * 42 + "\n")

    cfg = _load_existing()
    if cfg:
        print(f"Found existing config at {CONFIG_PATH}")
        choice = input("  (r) Refresh token only  |  (u) Update all fields  |  (q) Quit  > ").strip().lower()
        if choice == "q":
            sys.exit(0)
        if choice != "r":
            cfg = {}

    # --- Gather credentials ---------------------------------------- #
    if not cfg.get("team_id"):
        print("\n📋  Apple Developer credentials")
        print("    (Find these at developer.apple.com → Account → Membership)\n")
        cfg["team_id"]          = _ask("  Team ID")
        cfg["key_id"]           = _ask("  MusicKit Key ID")
        cfg["private_key_path"] = _ask("  Path to .p8 file (e.g. ~/Downloads/AuthKey_XXXXXX.p8)")
        cfg["storefront"]       = _ask("  Storefront country code", default="it")

    # Validate the .p8 path
    p8 = Path(cfg["private_key_path"]).expanduser()
    if not p8.exists():
        print(f"\n❌  .p8 file not found: {p8}")
        sys.exit(1)

    # --- Generate Developer Token ----------------------------------- #
    print("\n🔑  Generating Developer Token…")
    try:
        developer_token = _generate_developer_token(cfg)
        print("    ✅  Developer Token OK")
    except Exception as exc:
        print(f"\n❌  Failed to generate Developer Token: {exc}")
        sys.exit(1)

    # --- Start local HTTP server ------------------------------------ #
    _Handler.html = _HTML.replace("{{DEVELOPER_TOKEN}}", developer_token)
    server = HTTPServer(("localhost", PORT), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    url = f"http://localhost:{PORT}"
    print(f"\n🌐  Opening browser → {url}")
    print("    If it doesn't open automatically, paste the URL into your browser.\n")
    webbrowser.open(url)

    print("⏳  Waiting for you to authorise in the browser (timeout: 5 minutes)…\n")
    granted = _token_event.wait(timeout=300)

    server.shutdown()

    if not granted or not _received_token:
        print("❌  Timed out waiting for authorisation. Run the script again.")
        sys.exit(1)

    cfg["music_user_token"] = _received_token[0]
    _save_config(cfg)

    print(f"✅  Config saved to {CONFIG_PATH}")
    print("\n─" * 42)
    print("All done! Add the server to your Claude Desktop config:")
    print("""
  {
    "mcpServers": {
      "apple-music": {
        "command": "uv",
        "args": ["run", "--directory", "/path/to/mcp-apple-music", "mcp-apple-music"]
      }
    }
  }
""")


if __name__ == "__main__":
    main()
