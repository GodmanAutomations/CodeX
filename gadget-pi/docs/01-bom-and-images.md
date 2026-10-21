# 01 — Bill of materials & image matrix

## Hardware

You need a short stack:

- A Raspberry Pi (Pi 4/5/500/CM5/Zero 2 W preferred; original Zero/Zero W works
  with caveats).
- A **data-capable** USB cable (charge-only cables are the #2 failure cause).
- A microSD card, and optionally an SSD (USB 3 or USB-to-SATA).
- Optionally a **powered hub or dock**. Pi 4/5-class boards can brown out or drop
  the USB link when powered from a weak host port — connect directly or power the
  link externally. iPads support hubs, docks, external storage, and USB-to-Ethernet
  adapters, which also matters if you want gadget networking + HDMI capture at once.

## Correct USB port per model

| Model | Gadget/device port |
|---|---|
| Zero / Zero W / Zero 2 W | micro-USB **nearest HDMI** (not `PWR IN`) |
| Pi 4 / 5 / 500 / 500+ | the **USB-C** port |
| CM5 | the CM5 IO Board **USB-C** port |
| CM4 | possible, manual only — not auto-configured by `rpi-usb-gadget` |

## Image matrix

Official images from the Raspberry Pi downloads page. As of mid-2026, **Trixie**
(Debian 13) is the stable branch and **Bookworm** is Legacy.

| Use case | Image | Release | SHA256 |
|---|---|---:|---|
| Pi 4/5/500/Zero 2 W/CM5, desktop (VNC) | Raspberry Pi OS **Full** 64-bit (Trixie) | 2026-04-21 | `a6f48a832b965f3b25c9654578ea6056af4001390e85ef9953f7c011cd68d692` |
| Pi 4/5/500/Zero 2 W/CM5, terminal-first | Raspberry Pi OS **Lite** 64-bit (Trixie) | 2026-04-21 | `4cd31df026fd82243805a326dc0cafd7383f7e3d30c9413e7044d507aae281e2` |
| Original Zero / Zero W, desktop | Raspberry Pi OS **Full** 32-bit (Trixie) | 2026-04-21 | `eb22fa387c8bf8b2666e66c59ceea63de2bd7610b611b79926c91f839528c241` |
| Original Zero / Zero W, terminal-first | Raspberry Pi OS **Lite** 32-bit (Trixie) | 2026-04-21 | `f393b8bc3fc49aef49ddc5d5af124333002f34e4b23ede439789145e5280d210` |
| Legacy on newer ARMv8 boards | Raspberry Pi OS **Lite** 64-bit (Bookworm Legacy) | 2026-04-13 | `9bba9c625dd4dd4e1b326dd2551e37a2029db9090bf19ea300649b78c054de6f` |
| Legacy on original Zero / Zero W | Raspberry Pi OS **Lite** 32-bit (Bookworm Legacy) | 2026-04-13 | `265dfcd2a032ef01c224e8f9fc03b5fd0e31d3a5038f7e578cc5f01e22bc74a9` |

> These SHA256 values are a convenience baseline dated April 2026 and are also
> encoded in [`scripts/host/verify-image.sh`](../scripts/host/verify-image.sh)
> (`--list`). **Always re-verify against the official downloads page** — a newer
> official release will have a different, equally-valid hash.

Which to pick, if the model is unknown:

- **Trixie 64-bit Full** — Pi 4/5/500/Zero 2 W/CM5, you want a desktop.
- **Trixie 64-bit Lite** — same boards, terminal only.
- **Trixie 32-bit Full/Lite** — original Zero / Zero W.

## Flashing tool

**balenaEtcher** — it writes byte-for-byte and **validates** the write after
flashing, which is exactly what you want for a Raspberry Pi OS image. Verify the
download's SHA256 first with `scripts/host/verify-image.sh`.

## Packages & components

| Package / component | Purpose | Required? |
|---|---|---|
| `rpi-usb-gadget` | Official Trixie gadget automation | Required (Trixie path) |
| `openssh-server` | Terminal control over the USB link | Required |
| `wayvnc` | Desktop access on modern images | Recommended for GUI |
| `avahi-daemon` | `.local` hostname resolution | Recommended |
| `ufw` | Host firewall on the Pi | Optional |
| `parted`, `e2fsprogs`, `rsync` | SSD partition/resize/copy | Recommended (SSD) |
| `libcomposite` | configfs composite gadgets | Advanced only |
| `g_ether` / `g_serial` / `g_multi` / `g_hid` | Kernel gadget functions | Advanced only |

Continue to [02-trixie-setup.md](02-trixie-setup.md).
