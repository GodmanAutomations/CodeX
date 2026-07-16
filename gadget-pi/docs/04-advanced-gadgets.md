# 04 — Advanced gadget modes

These are **optional** and not the recommended path for controlling the Pi from an
iPad. For that, use `g_ether` (the Trixie path). This page covers the other kernel
gadget functions and a configfs composite gadget.

| Mode | Host sees | Best use | Fit for iPad control | Main caution |
|---|---|---|---|---|
| `g_ether` | USB Ethernet | SSH/SCP/VNC/apt | **Best choice** | Needs correct port + stable power |
| `g_serial` | USB serial (CDC ACM) | Recovery console | Fallback only | No network/desktop by itself |
| `g_hid` | Keyboard/mouse | Inject input into another host | **Wrong direction** | Doesn't let the iPad drive the Pi |
| `g_multi` | Ethernet + serial + storage | Lab/demo | Advanced only | Storage export can corrupt data |

## g_serial — serial console

```bash
sudo ./scripts/pi/usb-gserial.sh            # loads g_serial; device side = /dev/ttyGS0
sudo ./scripts/pi/usb-gserial.sh --console  # also start a login prompt on ttyGS0
```

The host connects to the new USB serial port (e.g.
`screen /dev/tty.usbmodem* 115200`). Handy when networking is broken; not a
substitute for SSH-over-Ethernet.

## g_multi — composite ECM + serial + read-only storage (configfs)

`scripts/pi/usb-gmulti.sh` builds a composite gadget under
`/sys/kernel/config/usb_gadget` with three functions: ECM Ethernet, an ACM serial
port, and a **read-only** mass-storage LUN backed by a dedicated image file
(`/pi-share.img`).

Run manually:

```bash
sudo ./scripts/pi/usb-gmulti.sh start
sudo ./scripts/pi/usb-gmulti.sh stop
sudo ./scripts/pi/usb-gmulti.sh restart
```

Run at boot via systemd:

```bash
sudo install -m 0755 scripts/pi/usb-gmulti.sh /usr/local/sbin/usb-gmulti.sh
sudo cp systemd/usb-gmulti.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable usb-gmulti.service
```

> **Storage-corruption warning.** The LUN is exported **read-only** on purpose.
> Never back a *writable* LUN with a filesystem that the Pi is also mounting — the
> host and the Pi writing the same blocks concurrently corrupts data. If you need
> host↔Pi file transfer, use SCP/SFTP over the ECM link instead (see
> [06-security.md](06-security.md)).

The configfs flow the script follows: create the gadget dir → set vendor/product
IDs and strings → create functions → set the ECM MAC addresses and the mass-storage
backing file → symlink functions into `configs/c.1` → bind by writing the UDC name
to `UDC`. Teardown reverses it (unbind by writing `""` to `UDC`, then remove links
and dirs).

## g_hid — Pi emulates a keyboard (wrong direction)

Included only for completeness. This makes the **Pi type into the host** — it does
*not* help you control the Pi from an iPad.

```bash
sudo ./scripts/pi/usb-hid-keyboard.sh       # creates /dev/hidg0
```

Writing 8-byte HID boot-keyboard reports to `/dev/hidg0` injects keystrokes into
whatever host the Pi is plugged into. The script installs the standard
boot-keyboard report descriptor. Optional systemd unit:
`systemd/usb-hid-keyboard.service`.

Next: [05-ssd.md](05-ssd.md).
