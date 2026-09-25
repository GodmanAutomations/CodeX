# 06 — Security, VNC & remote access

## SSH hardening

Baseline: prefer **public-key auth**, then disable password and root login.

Do this **only after** confirming key login works — otherwise you can lock
yourself out.

```bash
sudo ./scripts/pi/harden-ssh.sh
```

The script (`scripts/pi/harden-ssh.sh`) writes
`/etc/ssh/sshd_config.d/99-hardening.conf`:

```
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication no
UsePAM yes
AllowUsers <PI_USER>
```

Safety features: it refuses to run if `~/.ssh/authorized_keys` is missing for the
user (override with `--force`), runs `sshd -t` before reloading, and rolls back the
drop-in if validation fails. Keep your current session open and verify a *new* key
login before disconnecting.

## Firewall (optional): control traffic on usb0 only

`scripts/pi/setup-ufw.sh` installs `ufw` and allows SSH/VNC **only** on the gadget
interface, with an optional trusted-LAN allowance:

```bash
sudo ./scripts/pi/setup-ufw.sh
# also allow a LAN subnet:
sudo TRUSTED_LAN=192.168.0.0/16 ./scripts/pi/setup-ufw.sh
# different gadget iface name:
sudo GADGET_IFACE=usb0 ./scripts/pi/setup-ufw.sh
```

Resulting policy: default-deny inbound, default-allow outbound, plus
`allow in on usb0` for ports 22 and 5900.

It first prompts to **reset** `ufw` to a clean state — this discards any existing
rules so the final policy is exactly the gadget-only one described (otherwise a
stale `allow` rule could keep SSH/VNC reachable on another interface). It also
warns and asks for confirmation if your current SSH session is on a non-`usb0`
interface, to avoid locking yourself out.

## <a id="vnc"></a>VNC (desktop access)

VNC is a convenience layer on top of SSH, not a replacement. Modern Raspberry Pi
OS ships **WayVNC**, which attaches to a **running Wayland session** — so it's
reliable on a **Desktop/Full** image that auto-logs into a graphical session, and
unreliable/absent on Lite.

Official enable path:

```bash
sudo raspi-config
#   Interface Options -> VNC -> Yes
sudo reboot
```

Common shortcut (fall back to `raspi-config` if it fails on your build):

```bash
sudo systemctl enable --now wayvnc.service
sudo systemctl status wayvnc.service --no-pager
```

Connect from the iPad with a VNC client (the TigerVNC-compatible family works) to
`stephen-pi.local:5900` or `10.12.194.1:5900`.

## Remote access beyond the LAN

If you need a shell/screen from outside the local link, **Raspberry Pi Connect**
(browser-based) is the supported option. It's an optional add-on, not a replacement
for the gadget link.

Next: [07-ipad-client.md](07-ipad-client.md).
