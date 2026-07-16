# 08 — Troubleshooting

## First: run the verifier

```bash
./scripts/pi/verify-gadget.sh
```

It prints OS/network/UDC/module/service state in one shot. Use its output to
locate yourself in the checklist below.

## Failure causes, most to least likely

1. **Wrong USB port.** Zero boards: the port **nearest HDMI**, not `PWR IN`.
   Pi 4/5-class: the **USB-C** port. This is the single most common mistake.
2. **Charge-only cable.** Gadget mode needs a **data-capable** cable. Swap it.
3. **Insufficient power.** Pi 4/5 can drop the USB link off a weak host port —
   use a powered hub/dock.
4. **VNC expectations too early.** SSH must work first. VNC needs a running
   graphical session (WayVNC → use a Desktop image).
5. **Standard HDMI adapter used as iPad input.** That's output-only; you need a
   UVC capture device (see [07-ipad-client.md](07-ipad-client.md)).
6. **Original Zero W boot expectations.** Keep the OS on microSD; SSD is data-only
   (see [05-ssd.md](05-ssd.md)).

## Command cookbook (run on the Pi)

```bash
# Network state
ip -br addr
ip route
nmcli -t con show --active || true

# Gadget and kernel state
ls /sys/class/udc
lsmod | grep -E 'dwc2|g_ether|g_serial|g_multi|libcomposite' || true
journalctl -k -b --no-pager | grep -iE 'dwc2|g_ether|usb0|configfs'

# SSH and VNC
systemctl status ssh --no-pager
systemctl status wayvnc.service --no-pager || true
ss -ltnp | grep -E ':(22|5900)\s' || true

# Hostname discovery
hostnamectl
```

## Symptom → check

| Symptom | Check |
|---|---|
| `usb0` has no IP, no UDC listed | Wrong port or charge-only cable (causes 1–2) |
| UDC present, `usb0` up, but no SSH from iPad | iPad on Wi-Fi — disable Wi-Fi and retry; try `10.12.194.1` |
| `.local` name won't resolve | Install/enable `avahi-daemon`; use the fallback IP |
| SSH works, VNC refused | Lite image / no Wayland session — use a Desktop image; enable VNC |
| Link drops under load | Power — use a powered hub/dock |
| Bookworm `usb0` unmanaged | NetworkManager unmanaged rule — re-run the bootfs patch (see [03](03-bookworm-fallback.md)) |

## Bookworm-specific

```bash
ip -br a
journalctl -u NetworkManager -b --no-pager | tail -n 100
journalctl -k -b --no-pager | grep -iE 'dwc2|g_ether|usb0'
```

If `usb0` shows as unmanaged, the `85-nm-unmanaged.rules` override didn't apply —
re-run `scripts/host/patch-bookworm-bootfs.sh` on the boot partition (or apply the
`sed` from [03-bookworm-fallback.md](03-bookworm-fallback.md) on the running Pi and
restart NetworkManager).
