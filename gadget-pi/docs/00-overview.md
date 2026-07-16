# 00 — Overview & design conclusions

## The goal

Run a Raspberry Pi headlessly from an iPad (or laptop) over a single USB cable —
no keyboard, mouse, or monitor. The reliable way to do this is to make the Pi a
**USB Ethernet gadget** and then control it over **SSH** (terminal) and **VNC**
(desktop).

## Why gadget networking, not "iPad as a monitor"

A USB Ethernet link is a real network interface, so everything normal works over
it: SSH, SCP/SFTP, VNC, package installs, port forwarding, automation. That is
*control*.

Using the iPad as the Pi's literal display is a different, weaker thing. A
standard iPad HDMI adapter is for **output from the iPad**, not input into it. To
show the Pi's HDMI on the iPad you need a **UVC-compatible HDMI capture device**
plus a capture app — a picture, but no control. Treat HDMI-on-iPad as an optional
add-on, never the primary path. Details in
[07-ipad-client.md](07-ipad-client.md).

## The recommended stack

**Raspberry Pi OS Trixie + `rpi-usb-gadget` + cloud-init.** On Trixie images dated
2025-10-20 or later, gadget mode is a first-class feature: enable it from
Raspberry Pi Imager, or set it in `user-data` before first boot:

```yaml
rpi:
  enable_usb_gadget: true
enable_ssh: true
```

This avoids the older Bookworm-era dance of `dwc2` + `g_ether` in `cmdline.txt`,
`firstrun.sh` surgery, and NetworkManager unmanaged-device edge cases. Bookworm
still works and is documented as a **legacy fallback** in
[03-bookworm-fallback.md](03-bookworm-fallback.md), but it is no longer the path
of least resistance.

## Why `g_ether` specifically

The USB gadget subsystem can present the Pi to the host as many things. For
controlling the Pi from an iPad, the network function is the only one that gives
you a control plane:

- **`g_ether`** — USB Ethernet. SSH/SCP/VNC/apt all work. **This is the choice.**
- **`g_serial`** — a serial console only. Fine for recovery, not for real work.
- **`g_hid`** — makes the Pi *type into the host*. Wrong direction entirely.
- **`g_multi`** — Ethernet + serial + storage. Powerful, but adds complexity and a
  storage-corruption footgun. Advanced use only.

See [04-advanced-gadgets.md](04-advanced-gadgets.md) for the non-`g_ether` modes.

## SSH is the control plane; VNC is a convenience

- **SSH** is the non-negotiable, always-available way in. Make it work first.
- **VNC** gives you the graphical desktop, but modern Raspberry Pi OS uses
  **WayVNC**, which attaches to a *running Wayland session*. That means VNC is
  reliable on a **Desktop/Full** image that boots into a graphical session — and
  flaky or absent on a Lite image with no session. Choose a Desktop image if you
  want the GUI. See [06-security.md](06-security.md) and
  [02-trixie-setup.md](02-trixie-setup.md).

## Model notes

- **Pi 4 / 5 / 500 / CM5 / Zero 2 W** — full Trixie gadget path; can boot from SSD.
- **Original Pi Zero / Zero W** — gadget mode yes, but use a **32-bit** image and
  keep the **OS on microSD**, SSD as data only (USB mass-storage boot support in
  the Zero family starts at Zero 2 W). See [05-ssd.md](05-ssd.md).

Continue to [01-bom-and-images.md](01-bom-and-images.md).
