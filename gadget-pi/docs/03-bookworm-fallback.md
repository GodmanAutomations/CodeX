# 03 — Bookworm fallback (legacy)

Use this **only** if you must stay on Bookworm. Raspberry Pi OS Bookworm is now
Legacy; the clean path is Trixie ([02-trixie-setup.md](02-trixie-setup.md)).
Bookworm has no default `pi` user and does not ship `rpi-usb-gadget`, so you
pre-configure the user, enable SSH, and hand-patch the boot partition for
`dwc2` + `g_ether`.

## 1. Pre-create the user + enable SSH

Set a username/password (and ideally an SSH key) in **Raspberry Pi Imager**, which
generates a `firstrun.sh` on the boot partition. If you prefer to do it by hand,
place a `userconf.txt` and an empty `ssh` file on the boot partition:

```bash
# From config/gadget.env: PI_USER, PI_PASSWORD, BOOTFS
HASH="$(echo "$PI_PASSWORD" | openssl passwd -6 -stdin)"
printf '%s:%s\n' "$PI_USER" "$HASH" > "$BOOTFS/userconf.txt"
touch "$BOOTFS/ssh"
sync
```

## 2. Patch the boot partition for gadget mode

```bash
./scripts/host/patch-bookworm-bootfs.sh              # uses BOOTFS from gadget.env
# or: ./scripts/host/patch-bookworm-bootfs.sh /path/to/bootfs
```

The patcher (`scripts/host/patch-bookworm-bootfs.sh`) does three idempotent things:

1. Appends `dtoverlay=dwc2` to `config.txt`.
2. Inserts `modules-load=dwc2,g_ether` into `cmdline.txt` (backs up to
   `cmdline.txt.bak`).
3. Injects two NetworkManager connections (`usb0-dhcp`, `usb0-ll`) into
   `firstrun.sh` and comments out the `gadget` line in the shipped
   `85-nm-unmanaged.rules`, so NetworkManager actually manages `usb0` instead of
   ignoring it.

It requires `config.txt`, `cmdline.txt`, and `firstrun.sh` to be present — set a
username/SSH in Imager first so `firstrun.sh` exists.

## 3. Boot and connect

Same as Trixie: correct USB port, data cable, then:

```bash
ssh "$PI_USER@$PI_HOSTNAME.local"
```

## 4. Verify on the Pi

```bash
ip -br a
journalctl -u NetworkManager -b --no-pager | tail -n 100
journalctl -k -b --no-pager | grep -iE 'dwc2|g_ether|usb0'
# or just:
./scripts/pi/verify-gadget.sh
```

## Why this is the fallback

The Bookworm approach spreads gadget setup across `config.txt`, `cmdline.txt`,
`firstrun.sh`, and NetworkManager rules — four places that must agree. Trixie's
`rpi.enable_usb_gadget: true` collapses all of that into one line. If you can move
to Trixie, do.

Next: [04-advanced-gadgets.md](04-advanced-gadgets.md).
