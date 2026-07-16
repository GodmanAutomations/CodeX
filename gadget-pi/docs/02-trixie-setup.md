# 02 — Trixie setup (recommended end-to-end path)

This is the happy path: Raspberry Pi OS Trixie + `rpi-usb-gadget` + cloud-init,
controlled from an iPad over SSH (and optionally VNC).

## 0. Configure once

```bash
cp config/gadget.env.example config/gadget.env
$EDITOR config/gadget.env    # PI_HOSTNAME, PI_USER, PI_PASSWORD or PI_SSH_PUBKEY_FILE, BOOTFS
```

## 1. Back up the current card (optional)

If the card already holds anything you care about:

```bash
./scripts/host/backup-sd.sh          # interactive; lists disks, confirms target
```

Produces `~/pi-backups/<date>-pi-sd.img` plus a `.sha256`.

## 2. Download & verify the image

Download the right image from [01-bom-and-images.md](01-bom-and-images.md), then:

```bash
./scripts/host/verify-image.sh ~/Downloads/2026-04-21-raspios-trixie-arm64.img.xz
```

Exit 0 = matched the baseline. Exit 2 = unknown hash (compare it to the official
downloads page — likely just a newer release).

## 3. Flash with balenaEtcher

1. Open **balenaEtcher** → **Flash from file** → pick the `.img.xz`.
2. Select the target (microSD, or SSD on a boot-capable board).
3. **Flash**, and let validation finish.
4. Reinsert/remount the card so the **boot partition** mounts (e.g. `/Volumes/bootfs`
   on macOS, `/media/$USER/bootfs` on Linux). Set `BOOTFS` to that path.

## 4. Enable gadget mode + SSH before first boot

Password auth (from `PI_PASSWORD`):

```bash
./scripts/host/write-user-data.sh
```

Key auth (recommended — uses `PI_SSH_PUBKEY_FILE`, disables password login):

```bash
./scripts/host/write-user-data.sh --ssh-key
# or an explicit key path:
./scripts/host/write-user-data.sh --ssh-key ~/.ssh/id_ed25519.pub
```

This writes `${BOOTFS}/user-data` containing `rpi.enable_usb_gadget: true` and
`enable_ssh: true`. (Templates: [`cloud-init/`](../cloud-init/).)

## 5. Cable correctly and boot

- Insert the card (or attach the flashed SSD).
- Connect the Pi's **correct USB port** to the iPad with a **data-capable** cable
  (see the port table in [01-bom-and-images.md](01-bom-and-images.md)).
- If a Pi 4/5 won't stay powered from the iPad, put a **powered hub/dock** between
  them.
- First boot takes longer than usual and may reboot once — be patient.

## 6. First connection from the iPad

Use any SSH client app. Try, in order:

```bash
ssh stephen@stephen-pi.local
ssh stephen@10.12.194.1        # Trixie fallback IP when the host isn't doing ICS
```

If the iPad keeps preferring Wi-Fi, temporarily turn Wi-Fi off while testing the
direct cable link. More on the iPad side: [07-ipad-client.md](07-ipad-client.md).

## 7. Verify on the Pi

```bash
./scripts/pi/verify-gadget.sh
```

Look for: a `usb0` address, a bound UDC under `/sys/class/udc`, gadget modules
loaded, and `sshd` listening on 22.

## 8. Converting an existing Trixie Lite install

If you flashed Lite without pre-configuring gadget mode:

```bash
sudo ./scripts/pi/enable-trixie-gadget.sh   # apt install rpi-usb-gadget; rpi-usb-gadget on
sudo reboot
```

## 9. Desktop access (optional)

Want the touch desktop? Use a **Desktop/Full** image, then enable VNC — see
[06-security.md](06-security.md#vnc). SSH remains the guaranteed path regardless.

Next: [05-ssd.md](05-ssd.md) for SSD strategy, or
[06-security.md](06-security.md) to lock things down.
