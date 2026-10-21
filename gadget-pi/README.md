# Gadget-Pi

Run a Raspberry Pi **headlessly from an iPad** (or any host) over a single USB
cable, by turning the Pi into a **USB Ethernet gadget** and controlling it with
**SSH** (terminal) and **VNC** (desktop).

This is a runnable toolkit: host-side imaging helpers, Pi-side gadget/SSD/security
scripts, cloud-init and systemd templates, and a full set of docs. The
recommended path is **Raspberry Pi OS Trixie + `rpi-usb-gadget` + cloud-init**;
a legacy **Bookworm** fallback and advanced gadget modes (`g_multi`, `g_hid`,
`g_serial`) are included too.

> **Why gadget networking instead of an HDMI monitor?** A USB Ethernet link gives
> you *real* control — SSH, SCP/SFTP, VNC, package installs, automation. A standard
> HDMI adapter on an iPad is for *output from* the iPad, not input into it; using
> the iPad as the Pi's screen requires a separate UVC capture device. See
> [`docs/07-ipad-client.md`](docs/07-ipad-client.md).

## Quick start (Trixie happy path)

```bash
# 0. Configure once.
cp config/gadget.env.example config/gadget.env
$EDITOR config/gadget.env           # set hostname, user, password/SSH key, BOOTFS

# 1. (Optional) back up whatever is on the current card.
./scripts/host/backup-sd.sh

# 2. Download Raspberry Pi OS Trixie from the official site, then verify it.
./scripts/host/verify-image.sh ~/Downloads/*-trixie-*.img.xz

# 3. Flash it with balenaEtcher (validated write). Remount the boot partition.

# 4. Enable USB gadget mode + SSH on the freshly flashed boot partition.
./scripts/host/write-user-data.sh                 # password from gadget.env
#   or, key-only (recommended):
./scripts/host/write-user-data.sh --ssh-key

# 5. Insert the card, connect the correct USB port to the iPad, boot, then:
ssh "$PI_USER@$PI_HOSTNAME.local"                 # fallback: ssh user@10.12.194.1
```

Correct USB port per model (this is the #1 failure cause):

| Model | Gadget port |
|---|---|
| Zero / Zero W / Zero 2 W | micro-USB **nearest HDMI** (not `PWR IN`) |
| Pi 4 / 5 / 500 / 500+ | the **USB-C** power/data port |
| CM5 | the CM5 IO Board **USB-C** port |
| CM4 | possible, manual only (not auto-configured) |

## Repository map

```
gadget-pi/
├── README.md                 you are here
├── config/gadget.env.example one env file drives every script
├── Makefile                  make lint | syntax | check | test
├── scripts/
│   ├── common.sh             shared config-loading + logging helpers
│   ├── host/                 run on your Mac/Linux imaging machine
│   │   ├── backup-sd.sh
│   │   ├── verify-image.sh
│   │   ├── write-user-data.sh        (Trixie cloud-init)
│   │   └── patch-bookworm-bootfs.sh  (legacy fallback)
│   └── pi/                   run on the Pi itself
│       ├── enable-trixie-gadget.sh
│       ├── verify-gadget.sh
│       ├── setup-ssd-data.sh
│       ├── harden-ssh.sh
│       ├── setup-ufw.sh
│       ├── usb-gserial.sh
│       ├── usb-gmulti.sh             (ECM + serial + RO storage)
│       └── usb-hid-keyboard.sh
├── cloud-init/               Trixie user-data templates
├── systemd/                  units for the configfs gadgets
├── docs/                     the full guide (start at 00-overview.md)
└── tests/dry-run.sh          safe host-side tests, no device touched
```

## Documentation

| Doc | Contents |
|---|---|
| [00-overview](docs/00-overview.md) | Why gadget mode, why `g_ether`, SSH vs VNC |
| [01-bom-and-images](docs/01-bom-and-images.md) | Hardware, image matrix + SHA256, packages |
| [02-trixie-setup](docs/02-trixie-setup.md) | **Recommended** end-to-end path |
| [03-bookworm-fallback](docs/03-bookworm-fallback.md) | Legacy Bookworm gadget setup |
| [04-advanced-gadgets](docs/04-advanced-gadgets.md) | `g_serial`, `g_multi`, `g_hid`, configfs |
| [05-ssd](docs/05-ssd.md) | SSD as data volume vs boot-from-SSD |
| [06-security](docs/06-security.md) | SSH hardening, `ufw`, remote access |
| [07-ipad-client](docs/07-ipad-client.md) | iPad apps, HDMI/UVC reality |
| [08-troubleshooting](docs/08-troubleshooting.md) | Failure causes + verification cookbook |
| [diagrams](docs/diagrams.md) | Connection + setup-timeline diagrams |

## Gadget mode at a glance

| Mode | Host sees | Best use | Fit for iPad control |
|---|---|---|---|
| `g_ether` | USB Ethernet | SSH, SCP/SFTP, VNC | **Best choice** |
| `g_serial` | USB serial (CDC ACM) | Recovery console | Fallback only |
| `g_hid` | Keyboard/mouse | Inject input into another host | **Wrong direction** |
| `g_multi` | Ethernet + serial + storage | Lab/demo setups | Advanced only |

## Safety notes

- Scripts use `set -euo pipefail`, back up boot files before editing (`.bak`), and
  confirm destructive device operations. `usb-gmulti.sh` exports storage
  **read-only** by default — never export a live, writable root filesystem.
- The real `config/gadget.env` is git-ignored so a plaintext password never lands
  in version control. Prefer SSH keys (`--ssh-key`).
- SHA256 values in the docs are a convenience baseline dated April 2026 — always
  re-verify against the official Raspberry Pi downloads page.

## License

MIT — see [LICENSE](LICENSE).
