# 07 — The iPad client side

The Pi side is high-confidence. The iPad side is where the caveats live, because
Apple and Raspberry Pi don't publish a named, productized "Pi gadget mode from
iPad" support matrix — it's well-supported *in practice* rather than officially
documented as a scenario.

## What you need on the iPad

- An **SSH client app** for terminal work (any will do).
- A **VNC client app** if you want the desktop (TigerVNC-compatible works).

USB-C iPads support hubs, docks, external storage, and USB-to-Ethernet adapters,
and a Pi gadget link typically appears to the iPad as an **Ethernet** device.

## Connecting

Try these endpoints in order:

```bash
ssh stephen@stephen-pi.local     # mDNS/.local
ssh stephen@10.12.194.1          # Trixie fallback IP when the host isn't doing ICS
```

**Wi-Fi preference gotcha:** if the iPad keeps routing over Wi-Fi and ignores the
cable, temporarily turn Wi-Fi off while you test the direct link.

## The HDMI-to-iPad reality

This trips people up:

- A **standard iPad HDMI adapter is for OUTPUT** — sending the iPad's screen to a
  monitor. It cannot take HDMI *in*.
- To display the Pi's HDMI **on** the iPad you need a **UVC-compatible HDMI
  capture device** plus an iPad app that does UVC video capture. That gives you a
  *picture* of the Pi's screen, but no control.

So HDMI-on-iPad is an **optional add-on**, never the primary path. SSH/VNC over the
gadget link is what actually lets you *drive* the Pi.

## Gadget networking + HDMI capture at the same time

Possible, but the iPad usually has one port, so you need a **USB-C hub/dock** to
run the Pi's gadget link and a UVC capture device simultaneously while keeping the
iPad powered. Apple documents hub/dock support; the exact accessory combination
still matters.

Next: [08-troubleshooting.md](08-troubleshooting.md).
