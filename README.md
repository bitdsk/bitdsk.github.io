# Bitdsk miners — products, firmware and docs

Product and support site for the Bitdsk miner line.

This site replaces the old WordPress installation at [bitdsk.org](https://bitdsk.org). That
installation is being retired: the product pages, firmware, manuals, guides and the flash tool have
all been migrated here, so nothing depends on the old host any more. It is a plain static site — no
backend, no database — served from GitHub Pages.

---

## Models

| Model | ASIC | Hashrate | Power | Display |
|---|---|---|---|---|
| **N8-T** | 1 | 200 G | ≈8.9 W | 0.91″ mono |
| **U1 Touch** | 1 | 200 G | ≈10 W | 2.8″ touch |
| **U2 Touch** | 1 | 1100–1500 G | ≈22–27 W | 2.8″ touch |
| **D12 / D12-T** | 1 | 200 G | ≈8.9 W | 1.9″ colour |
| **S1** | none (ESP32) | 600k–800k H/s | USB powered | 2.8″ touch |

Older boards (N5.Rex, N5.Rexi-T, D9, Q2, N5.Lite) are still listed under **legacy** on the
[firmware page](firmware.html).

Full side-by-side specs: [Version comparison](docs/version-comparison.html).

---

## Where to start

| I want to… | Go to |
|---|---|
| See what each board does and what it costs to run | [products.html](products.html) |
| Download firmware for my model | [firmware.html](firmware.html) |
| Flash a board over USB from the browser | [flash.html](flash.html) |
| Read the user manual (PDF, EN/CN) | [docs/docs.html](docs/docs.html) |
| Fix a problem (hotspot, static IP, frequency) | [guides/index.html](guides/index.html) |
| Talk to the miner over HTTP | [docs/api.html](docs/api.html) |
| Compare hardware between models | [docs/version-comparison.html](docs/version-comparison.html) |

---

## Updating firmware

**OTA upgrade** is what you want almost always. Download the `.zip` for your model, open the miner's
web UI, go to **Settings → Firmware** and upload it. Your settings are preserved.

**Full erase and reflash** is for a bricked board, a device that will not boot, or a U1/U2 whose
CD KEY was wiped. It needs a USB cable and a Chromium-based browser (Chrome or Edge) — the flasher
talks to the ESP32 over Web Serial and runs entirely in the page.

### The CD KEY only exists on U1 and U2

| Model | CD KEY |
|---|---|
| **U1 Touch**, **U2 Touch** | Yes — shown under **Settings → System** |
| **N8-T**, **D12 / D12-T**, **N5 series**, legacy boards | No |
| **S1** | No — open-source firmware, no key at all |

On a U1 or U2 the key is stored in the device's NVS partition. An OTA upgrade keeps it, a full erase
wipes it. **Copy it down before you flash.** Once lost it cannot be recovered from the firmware, and
typing the backup back in is the only way to bring the board back after a full erase.

On every other model there is no key to save, so a full reflash is just a full reflash — nothing to
restore afterwards.

---

## Where the files live

The site is split across repositories so that binaries and page content can be updated independently:

| Repository | Contents |
|---|---|
| [bitdsk.github.io](https://github.com/bitdsk/bitdsk.github.io) | This site: index pages, docs, guides, PDF manuals |
| [Bitdsk_Miner_Archive](https://github.com/bitdsk/Bitdsk_Miner_Archive) | All firmware binaries (OTA zips, legacy builds, PC tools, Gerber files) |
| [Bitdsk-Flash_For_U1U2](https://github.com/bitdsk/Bitdsk-Flash_For_U1U2) | Browser flash tool and the S1 / U1 / U2 flash images |
| [Bitdsk-s1-Miner](https://github.com/bitdsk/Bitdsk-s1-Miner) | S1 firmware source code (MIT) |

No firmware binaries are stored in this repository. The firmware page reads `data/firmware.json`
(names, sizes, SHA256) and builds download links against the archive repository, so the same file is
reachable from GitHub, from the jsDelivr CDN, or straight from a clone.

---

## A note on version dates

This content was migrated from the old WordPress site. **Version numbers are accurate; the dates
next to them may be off by a few days**, because they were taken from the original download tables
rather than from the build timestamps. Treat the version string as the source of truth.

---

## S1 is open source

The S1 is built on off-the-shelf ESP32 hardware (a CYD board), so the firmware is published in full:
sources, build instructions and the partition layout are in
[Bitdsk-s1-Miner](https://github.com/bitdsk/Bitdsk-s1-Miner) under the MIT licence. Build it yourself,
modify it, or use it as a starting point.

---

## Licence & attribution

Site content and documentation © Bitdsk Lab. The S1 firmware is MIT licensed — see the
[Bitdsk-s1-Miner](https://github.com/bitdsk/Bitdsk-s1-Miner) repository for the full text.
Third-party components keep their own licences; the flash tool bundles
[esp-web-tools](https://github.com/esphome/esp-web-tools) (Apache-2.0) locally rather than loading it
from a CDN, so it works offline once the page is cached.
