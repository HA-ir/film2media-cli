# ⚡ f2m — Film2Media Terminal Client

Search, browse, download and stream movies & series from Film2Media, right inside your terminal.

جست‌وجو، دانلود و پخش مستقیم فیلم و سریال از فیلم‌تو‌مدیا، داخل ترمینال.

| | |
|---|---|
| ![Main menu](assets/screenshot-1.png) | ![Search](assets/screenshot-2.png) |
| ![Quality](assets/screenshot-3.png) | |

---

## ✨ Features / امکانات

- 🔍 **Instant search** — search by English or Persian title, with IMDb rating, dub/hardsub badges
  جست‌وجوی سریع با عنوان فارسی یا انگلیسی، همراه امتیاز IMDb و نشان دوبله/زیرنویس
- 🗂 **Browse** — movies, series, genres and Top-250 lists
  مرور دسته‌بندی‌ها، ژانرها و لیست ۲۵۰ فیلم/سریال برتر
- ⬇ **Download** — multi-connection downloads with aria2c (fallback: curl)
  دانلود چند-اتصاله با aria2c (در نبودش: curl)
- 🤖 **Auto aria2c** — if aria2c is missing, f2m installs it for you (package manager on Linux, official binary on Windows)
  اگه aria2c نصب نباشه، خودکار نصبش می‌کنه (لینوکس: پکیج‌منیجر، ویندوز: دانلود باینری رسمی کنار برنامه)
- ▶ **Stream** — watch instantly in mpv, VLC or PotPlayer without downloading
  پخش مستقیم در mpv یا VLC یا PotPlayer بدون نیاز به دانلود
- 🌐 **Auto domain update** — when the site moves to a new domain, f2m detects it and updates itself
  وقتی دامنه‌ی سایت عوض شه، خودکار تشخیص داده و به‌روز می‌شه
- 🧩 **Single file** — pure Python 3.8+, no dependencies
  تک‌فایل و بدون هیچ وابستگی، فقط پایتون ۳.۸ به بالا

---

## 📦 Install / نصب

### Option A — Ready binaries (no Python needed) / نسخه‌ی آماده (بدون نیاز به پایتون)

Grab `f2m-windows-x64.exe` or `f2m-linux-x64` from the
[**Releases**](../../releases) page and run it.

فایل اجرایی ویندوز یا لینوکس را از صفحه‌ی [Releases](../../releases) دانلود و اجرا کنید.

### Option B — From source / اجرا از سورس

Requires Python 3.8+ / نیازمند پایتون ۳.۸ به بالا:

```bash
python f2m.py
```

Recommended companions (optional) / پیشنهادی (اختیاری):

- **aria2c** — fast downloads / دانلود سریع
- **mpv** or **VLC** — streaming / پخش مستقیم

---

## 🚀 Usage / استفاده

Run without arguments for the interactive menu / بدون آرگومان اجرا کنید تا منوی تعاملی باز شود:

```
f2m
```

Or use commands / یا از دستورات استفاده کنید:

| Command / دستور | Description / توضیح |
|---|---|
| `f2m search "breaking bad"` | Search / جست‌وجو |
| `f2m categories` | Browse categories / مرور دسته‌بندی‌ها |
| `f2m url <post-url>` | Open a post directly / باز کردن مستقیم صفحه‌ی یک فیلم |
| `f2m test` | Connectivity test / تست اتصال |
| `f2m config` | Show config / نمایش تنظیمات |

Inside the menus you can pick items like `1`, ranges like `1,3,5-8`, or `all`.
داخل منوها می‌توانید مثل `1`، بازه‌ای مثل `1,3,5-8` یا `all` انتخاب کنید.

---

## ⚙️ Configuration / تنظیمات

A `f2m.conf` file is created next to the program on first run.
فایل `f2m.conf` در اولین اجرا کنار برنامه ساخته می‌شود.

**If the site domain changes / اگر دامنه‌ی سایت عوض شد:**

```bash
f2m config set base_url https://www.new-domain.tld
```

In most cases you don't need this — f2m follows redirects automatically.
در اکثر مواقع لازم نیست؛ f2m ریدایرکت دامنه را خودکار دنبال می‌کند.

Other keys / سایر کلیدها:

| Key / کلید | Description / توضیح |
|---|---|
| `mirrors` | Fallback domains / دامنه‌های جایگزین |
| `proxy` | Proxy for requests & downloads / پروکسی برای دریافت و دانلود |
| `player` | `auto` / `mpv` / `vlc` / `potplayer` |
| `download_dir` | Downloads folder / پوشه‌ی دانلود |

---

## 🛠 Troubleshooting / رفع اشکال

- **Nothing found / چیزی پیدا نشد** → run `f2m test` / دستور `f2m test` را اجرا کنید
- **Cannot connect / اتصال برقرار نشد** → the domain may be filtered; set a proxy or the new `base_url`
  ممکن است دامنه فیلتر شده باشد؛ پروکسی تنظیم کنید یا `base_url` جدید بدهید
- **No player found / پخش‌کننده پیدا نشد** → install mpv or VLC, or copy links manually
  mpv یا VLC نصب کنید یا لینک‌ها را دستی کپی کنید

---

## ⚠️ Disclaimer / سلب مسئولیت

This tool only indexes publicly available links and is provided for personal use.
Users are responsible for complying with the laws of their region.

این ابزار فقط لینک‌های عمومی را فهرست می‌کند و برای استفاده‌ی شخصی ارائه شده است.
مسئولیت رعایت قوانین محلی بر عهده‌ی کاربر است.

## 📄 License / مجوز

MIT — see [LICENSE](LICENSE)
