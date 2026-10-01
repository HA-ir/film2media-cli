# ⚡ f2m — Film2Media Terminal Client

Search, browse, download and stream movies & series from Film2Media — right inside your terminal.

> 🇮🇷 نسخه‌ی فارسی: [README.fa.md](README.fa.md)

---

## 📸 Screenshots

![Main menu](assets/screenshot-1.png)
![Search results](assets/screenshot-2.png)
![Quality selection](assets/screenshot-3.png)

---

## ✨ Features

- 🔍 **Instant search** — search by English or Persian title, with IMDb rating and dub/hardsub badges
- 🗂 **Browse** — movies, series, genres and Top-250 lists
- ⬇ **Download** — multi-connection downloads with aria2c (fallback: curl)
- 🤖 **Auto aria2c** — if aria2c is missing, f2m installs it for you (package manager on Linux, official binary on Windows)
- ▶ **Stream** — watch instantly in mpv, VLC or PotPlayer without downloading
- 🌐 **Auto domain update** — when the site moves to a new domain, f2m detects it and updates itself
- 🧩 **Single file** — pure Python 3.8+, zero dependencies

---

## 📦 Install

### Option A — Ready binaries (no Python needed)

Grab `f2m-windows-x64.exe` or `f2m-linux-x64` from the
[**Releases**](https://github.com/lombalo/film2media-cli/releases) page and run it.

### Option B — From source

Requires Python 3.8+:

```bash
python f2m.py
```

Optional companions:

- **aria2c** — fast downloads
- **mpv** or **VLC** — streaming

---

## 🚀 Usage

Run without arguments for the interactive menu:

```
f2m
```

Or use commands:

| Command | Description |
|---|---|
| `f2m search "breaking bad"` | Search |
| `f2m categories` | Browse categories |
| `f2m url <post-url>` | Open a post directly |
| `f2m test` | Connectivity test |
| `f2m config` | Show config |

Inside menus you can pick items like `1`, ranges like `1,3,5-8`, or `all`.

---

## ⚙️ Configuration

A `f2m.conf` file is created next to the program on first run.

**If the site domain changes:**

```bash
f2m config set base_url https://www.new-domain.tld
```

In most cases you don't need this — f2m follows redirects automatically.

Other keys:

| Key | Description |
|---|---|
| `mirrors` | Fallback domains |
| `proxy` | Proxy for requests & downloads |
| `player` | `auto` / `mpv` / `vlc` / `potplayer` |
| `download_dir` | Downloads folder |

---

## 🛠 Development & Testing

Set up the development environment and run automated tests:

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -e ".[dev]"

# Run offline automated test suite
pytest
```

---

## 🛠 Troubleshooting

- **Nothing found** → run `f2m test`
- **Cannot connect** → the domain may be filtered; set a proxy or the new `base_url`
- **No player found** → install mpv or VLC, or copy links manually

---

## ⚠️ Disclaimer

This tool only indexes publicly available links and is provided for personal use.
Users are responsible for complying with the laws of their region.

---

## 📄 License

MIT — see [LICENSE](LICENSE)
