#!/usr/bin/env bash
#
# dry-run.sh — safe host-side tests. Exercises the boot-partition writers against
# a throwaway fake bootfs in a temp dir. Touches NO real device. Run: make test
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export GADGET_PI_ASSUME_YES=1

pass=0
fail=0
check() { # check "desc" "expected-substring" file
  if grep -qF "$2" "$3"; then
    printf '  \033[32mok\033[0m   %s\n' "$1"; pass=$((pass + 1))
  else
    printf '  \033[31mFAIL\033[0m %s (missing: %s)\n' "$1" "$2"; fail=$((fail + 1))
  fi
}

# Portable across GNU and BSD/macOS mktemp (BSD needs an explicit template).
tmp="$(mktemp -d "${TMPDIR:-/tmp}/gadget-pi.XXXXXX")"
trap 'rm -rf "${tmp}"' EXIT

echo "== write-user-data.sh (password) =="
bootfs="${tmp}/boot-pw"; mkdir -p "${bootfs}"; : > "${bootfs}/user-data"
BOOTFS="${bootfs}" PI_HOSTNAME="test-pi" PI_USER="tester" \
  PI_PASSWORD="s3cret" PI_TIMEZONE="UTC" \
  "${ROOT}/scripts/host/write-user-data.sh" >/dev/null
check "cloud-config header" "#cloud-config"            "${bootfs}/user-data"
check "hostname set"        "hostname: test-pi"         "${bootfs}/user-data"
check "gadget enabled"      "enable_usb_gadget: true"   "${bootfs}/user-data"
check "ssh enabled"         "enable_ssh: true"          "${bootfs}/user-data"
check "chpasswd module"     "chpasswd:"                 "${bootfs}/user-data"
check "chpasswd list block"  "list: |"                  "${bootfs}/user-data"
check "user:password line"  "tester:s3cret"             "${bootfs}/user-data"
# Catch both the real (unreliable) cloud-init key 'plain_text_passwd' and the
# invalid 'plain_text_password' typo, as an actual YAML key (line start, not in
# a '#' comment) via the shared 'plain_text_pass' prefix.
if grep -qE '^[[:space:]]*plain_text_pass' "${bootfs}/user-data"; then
  printf '  \033[31mFAIL\033[0m still uses a plain_text_pass* key\n'; fail=$((fail + 1))
else
  printf '  \033[32mok\033[0m   no plain_text_pass* key\n'; pass=$((pass + 1))
fi
check "sudo requires pw"    "sudo: ALL=(ALL) ALL"       "${bootfs}/user-data"
if grep -q 'NOPASSWD:ALL' "${bootfs}/user-data"; then
  printf '  \033[31mFAIL\033[0m password mode still grants NOPASSWD sudo\n'; fail=$((fail + 1))
else
  printf '  \033[32mok\033[0m   password mode requires sudo password\n'; pass=$((pass + 1))
fi

echo "== write-user-data.sh (password preserved verbatim in list block) =="
bootfs="${tmp}/boot-pw2"; mkdir -p "${bootfs}"; : > "${bootfs}/user-data"
# A password with a double-quote and a backslash is preserved verbatim in the
# chpasswd list literal block (no escaping needed).
BOOTFS="${bootfs}" PI_HOSTNAME="t" PI_USER="u" \
  PI_PASSWORD='a"b\c' PI_TIMEZONE="UTC" \
  "${ROOT}/scripts/host/write-user-data.sh" >/dev/null
check "verbatim password" 'u:a"b\c' "${bootfs}/user-data"

echo "== write-user-data.sh (rejects newline in password) =="
bootfs="${tmp}/boot-pw3"; mkdir -p "${bootfs}"; : > "${bootfs}/user-data"
if BOOTFS="${bootfs}" PI_HOSTNAME="t" PI_USER="u" \
     PI_PASSWORD="$(printf 'a\nb')" PI_TIMEZONE="UTC" \
     "${ROOT}/scripts/host/write-user-data.sh" >/dev/null 2>&1; then
  printf '  \033[31mFAIL\033[0m accepted a password containing a newline\n'; fail=$((fail + 1))
else
  printf '  \033[32mok\033[0m   rejected password containing a newline\n'; pass=$((pass + 1))
fi
if BOOTFS="${tmp}/boot-pw3" PI_HOSTNAME="$(printf 'a\nb')" PI_USER="u" \
     PI_PASSWORD="x" PI_TIMEZONE="UTC" \
     "${ROOT}/scripts/host/write-user-data.sh" >/dev/null 2>&1; then
  printf '  \033[31mFAIL\033[0m accepted a hostname containing a newline\n'; fail=$((fail + 1))
else
  printf '  \033[32mok\033[0m   rejected hostname containing a newline\n'; pass=$((pass + 1))
fi
if BOOTFS="${tmp}/boot-pw3" PI_HOSTNAME="a:b # c" PI_USER="u" \
     PI_PASSWORD="x" PI_TIMEZONE="UTC" \
     "${ROOT}/scripts/host/write-user-data.sh" >/dev/null 2>&1; then
  printf '  \033[31mFAIL\033[0m accepted a hostname with YAML-significant chars\n'; fail=$((fail + 1))
else
  printf '  \033[32mok\033[0m   rejected hostname with YAML-significant chars\n'; pass=$((pass + 1))
fi

echo "== write-user-data.sh (ssh key) =="
bootfs="${tmp}/boot-key"; mkdir -p "${bootfs}"; : > "${bootfs}/user-data"
# Include a comment line and a blank line, as an authorized_keys file might have.
key="${tmp}/id.pub"
printf '# my keys\n\nssh-ed25519 AAAATESTKEY tester@host\n' > "${key}"
BOOTFS="${bootfs}" PI_HOSTNAME="test-pi" PI_USER="tester" \
  "${ROOT}/scripts/host/write-user-data.sh" --ssh-key "${key}" >/dev/null
check "authorized key"   "ssh-ed25519 AAAATESTKEY" "${bootfs}/user-data"
check "pwauth disabled"  "ssh_pwauth: false"        "${bootfs}/user-data"
check "passwd locked"    "lock_passwd: true"        "${bootfs}/user-data"
check "key mode NOPASSWD" "sudo: ALL=(ALL) NOPASSWD:ALL" "${bootfs}/user-data"
check "gadget enabled"   "enable_usb_gadget: true"  "${bootfs}/user-data"
if grep -qE '^[[:space:]]*-[[:space:]]*#' "${bootfs}/user-data"; then
  printf '  \033[31mFAIL\033[0m comment line emitted as a null YAML list item\n'; fail=$((fail + 1))
else
  printf '  \033[32mok\033[0m   comment/blank key lines skipped\n'; pass=$((pass + 1))
fi

echo "== patch-bookworm-bootfs.sh =="
bootfs="${tmp}/boot-bw"; mkdir -p "${bootfs}"
echo "console=serial0,115200 rootwait quiet" > "${bootfs}/cmdline.txt"
echo "# base config" > "${bootfs}/config.txt"
printf '#!/bin/bash\nrm -f /boot/firstrun.sh\n' > "${bootfs}/firstrun.sh"
BOOTFS="${bootfs}" "${ROOT}/scripts/host/patch-bookworm-bootfs.sh" >/dev/null
check "dwc2 overlay"     "dtoverlay=dwc2"              "${bootfs}/config.txt"
check "modules-load"     "modules-load=dwc2,g_ether"   "${bootfs}/cmdline.txt"
check "usb0-dhcp conn"   "usb0-dhcp"                    "${bootfs}/firstrun.sh"
check "nm-unmanaged fix" "85-nm-unmanaged.rules"        "${bootfs}/firstrun.sh"
check "udev dir mkdir"   "mkdir -p /etc/udev/rules.d"   "${bootfs}/firstrun.sh"
check "sed -i ordering"  "sed -i "                      "${bootfs}/firstrun.sh"
check "nm dir mkdir"     "mkdir -p /etc/NetworkManager/system-connections" "${bootfs}/firstrun.sh"
check "portable uuid"    "/proc/sys/kernel/random/uuid" "${bootfs}/firstrun.sh"
check "config.txt bak"   "# base config"                "${bootfs}/config.txt.bak"
check "firstrun bak"     "rm -f /boot/firstrun.sh"      "${bootfs}/firstrun.sh.bak"

echo "== patch-bookworm-bootfs.sh (rootwait as last token) =="
bootfs="${tmp}/boot-bw2"; mkdir -p "${bootfs}"
echo "console=serial0,115200 root=/dev/mmcblk0p2 rootwait" > "${bootfs}/cmdline.txt"
echo "# base config" > "${bootfs}/config.txt"
printf '#!/bin/bash\nrm -f /boot/firstrun.sh\n' > "${bootfs}/firstrun.sh"
BOOTFS="${bootfs}" "${ROOT}/scripts/host/patch-bookworm-bootfs.sh" >/dev/null
check "modules-load appended" "modules-load=dwc2,g_ether" "${bootfs}/cmdline.txt"
if [ "$(wc -l < "${bootfs}/cmdline.txt")" -eq 1 ]; then
  printf '  \033[32mok\033[0m   cmdline.txt stays single-line\n'; pass=$((pass + 1))
else
  printf '  \033[31mFAIL\033[0m cmdline.txt became multi-line\n'; fail=$((fail + 1))
fi
if grep -q 'uuid -v4' "${bootfs}/firstrun.sh"; then
  printf '  \033[31mFAIL\033[0m firstrun.sh still uses non-portable uuid -v4\n'; fail=$((fail + 1))
else
  printf '  \033[32mok\033[0m   no non-portable uuid -v4\n'; pass=$((pass + 1))
fi

echo "== patch idempotency (second run must not double-apply) =="
BOOTFS="${bootfs}" "${ROOT}/scripts/host/patch-bookworm-bootfs.sh" >/dev/null
n="$(grep -c 'dtoverlay=dwc2' "${bootfs}/config.txt")"
if [ "${n}" -eq 1 ]; then
  printf '  \033[32mok\033[0m   dwc2 applied exactly once\n'; pass=$((pass + 1))
else
  printf '  \033[31mFAIL\033[0m dwc2 applied %s times\n' "${n}"; fail=$((fail + 1))
fi

echo "== cmdline idempotency (existing modules-load, reverse order + extra) =="
bootfs="${tmp}/boot-ml"; mkdir -p "${bootfs}"
echo "console=serial0,115200 modules-load=g_ether,dwc2,foo rootwait" > "${bootfs}/cmdline.txt"
echo "# base config" > "${bootfs}/config.txt"
printf '#!/bin/bash\nrm -f /boot/firstrun.sh\n' > "${bootfs}/firstrun.sh"
BOOTFS="${bootfs}" "${ROOT}/scripts/host/patch-bookworm-bootfs.sh" >/dev/null
m="$(grep -oE 'modules-load=' "${bootfs}/cmdline.txt" | wc -l | tr -d ' ')"
if [ "${m}" -eq 1 ]; then
  printf '  \033[32mok\033[0m   no duplicate modules-load token appended\n'; pass=$((pass + 1))
else
  printf '  \033[31mFAIL\033[0m modules-load tokens: %s (expected 1)\n' "${m}"; fail=$((fail + 1))
fi

# Both modules present only in a LATER modules-load token must still be detected.
bootfs="${tmp}/boot-ml2"; mkdir -p "${bootfs}"
echo "modules-load=foo rootwait modules-load=dwc2,g_ether" > "${bootfs}/cmdline.txt"
echo "# base config" > "${bootfs}/config.txt"
printf '#!/bin/bash\nrm -f /boot/firstrun.sh\n' > "${bootfs}/firstrun.sh"
BOOTFS="${bootfs}" "${ROOT}/scripts/host/patch-bookworm-bootfs.sh" >/dev/null
m="$(grep -oE 'modules-load=' "${bootfs}/cmdline.txt" | wc -l | tr -d ' ')"
if [ "${m}" -eq 2 ]; then
  printf '  \033[32mok\033[0m   later modules-load token detected (no append)\n'; pass=$((pass + 1))
else
  printf '  \033[31mFAIL\033[0m modules-load tokens: %s (expected 2)\n' "${m}"; fail=$((fail + 1))
fi

echo "== patch-bookworm-bootfs.sh (missing firstrun anchor fails loudly) =="
bootfs="${tmp}/boot-noanchor"; mkdir -p "${bootfs}"
echo "console=serial0,115200 rootwait" > "${bootfs}/cmdline.txt"
echo "# base config" > "${bootfs}/config.txt"
# firstrun.sh without the expected self-delete anchor line.
printf '#!/bin/bash\necho hello\n' > "${bootfs}/firstrun.sh"
if BOOTFS="${bootfs}" "${ROOT}/scripts/host/patch-bookworm-bootfs.sh" >/dev/null 2>&1; then
  printf '  \033[31mFAIL\033[0m patcher reported success without injecting firstrun.sh\n'; fail=$((fail + 1))
else
  printf '  \033[32mok\033[0m   patcher fails when the firstrun anchor is missing\n'; pass=$((pass + 1))
fi

echo "== patch idempotency (dwc2 with existing parameters) =="
bootfs="${tmp}/boot-bw3"; mkdir -p "${bootfs}"
echo "console=serial0,115200 rootwait" > "${bootfs}/cmdline.txt"
printf '# base config\ndtoverlay=dwc2,dr_mode=peripheral\n' > "${bootfs}/config.txt"
printf '#!/bin/bash\nrm -f /boot/firstrun.sh\n' > "${bootfs}/firstrun.sh"
BOOTFS="${bootfs}" "${ROOT}/scripts/host/patch-bookworm-bootfs.sh" >/dev/null
n="$(grep -c '^dtoverlay=dwc2' "${bootfs}/config.txt")"
if [ "${n}" -eq 1 ]; then
  printf '  \033[32mok\033[0m   dwc2-with-params not duplicated\n'; pass=$((pass + 1))
else
  printf '  \033[31mFAIL\033[0m dwc2 lines: %s (expected 1)\n' "${n}"; fail=$((fail + 1))
fi

echo "== verify-image.sh =="
dummy="${tmp}/dummy.img"; echo "hello gadget-pi" > "${dummy}"
if command -v sha256sum >/dev/null 2>&1; then
  h="$(sha256sum "${dummy}" | awk '{print $1}')"
else
  h="$(shasum -a 256 "${dummy}" | awk '{print $1}')"
fi
# Non-matching file should exit 2 (unknown), not 0.
if "${ROOT}/scripts/host/verify-image.sh" "${dummy}" >/dev/null 2>&1; then
  printf '  \033[31mFAIL\033[0m unknown image unexpectedly matched\n'; fail=$((fail + 1))
else
  rc=$?
  if [ "${rc}" -eq 2 ]; then
    printf '  \033[32mok\033[0m   unknown image reported (exit 2), computed %s\n' "${h:0:12}..."; pass=$((pass + 1))
  else
    printf '  \033[31mFAIL\033[0m unexpected exit code %s\n' "${rc}"; fail=$((fail + 1))
  fi
fi

echo
printf 'Results: %d passed, %d failed\n' "${pass}" "${fail}"
[ "${fail}" -eq 0 ]
