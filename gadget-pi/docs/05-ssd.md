# 05 — SSD strategy

Two strategies; the right one depends on the board.

## Decision

| Board | Strategy |
|---|---|
| Pi 4 / 5 / 500 / CM5 / Zero 2 W | Flash the SSD directly and boot from it, **or** use it as a data disk. |
| Original Pi Zero / Zero W | Keep the **OS on microSD**; use the SSD as a **data volume only**. |

USB mass-storage boot in the Zero family starts at **Zero 2 W**; the original
Zero/Zero W is not on the boot-from-USB support list. External disks may also need
extra power — use a powered hub/dock if the disk misbehaves.

## SSD as a data volume (any board)

`scripts/pi/setup-ssd-data.sh` partitions (GPT), formats ext4 (label `pidata`),
mounts at `$SSD_MOUNT` (default `/srv/data`) with a `nofail` fstab entry, and
symlinks `~/projects` and `~/transfers` into it.

```bash
# Set SSD_DEV / SSD_PART / SSD_MOUNT in config/gadget.env first.
sudo ./scripts/pi/setup-ssd-data.sh
```

> **Destructive:** it erases `$SSD_DEV`. The script prints the target layout and
> requires an explicit confirmation before touching anything.

The `nofail,x-systemd.device-timeout=10s` mount options mean the Pi still boots if
the SSD is absent — important for a headless box you can't see.

## Boot from SSD (supported boards only)

Cleanest approach: **flash the SSD directly** with the same Trixie image, remove
the SD card, and boot. If it doesn't boot, update the bootloader and set the boot
order:

```bash
sudo apt update && sudo apt full-upgrade -y
sudo rpi-eeprom-update -a
sudo raspi-config
#   Advanced Options -> Boot Order -> USB Boot (or storage-first for your board)
sudo reboot
```

That matches Raspberry Pi's bootloader guidance for Pi 4-class devices.

## Transferring files

Once the SSD is mounted and the gadget link is up, copy over the USB Ethernet link
like any network host:

```bash
# From the iPad/host to the Pi:
scp ./bigfile "$PI_USER@$PI_HOSTNAME.local:~/transfers/"
```

Next: [06-security.md](06-security.md).
