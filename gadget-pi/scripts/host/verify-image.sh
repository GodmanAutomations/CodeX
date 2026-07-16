#!/usr/bin/env bash
#
# verify-image.sh — verify a downloaded Raspberry Pi OS image against the known
# SHA256 values from the image matrix (docs/01-bom-and-images.md).
#
# Runs on the HOST.
#
# Usage:
#   ./verify-image.sh /path/to/image.img.xz
#   ./verify-image.sh --list                 # print the known-good hashes
#
# The known hashes below are a convenience baseline dated 2026-04. ALWAYS treat
# the official Raspberry Pi downloads page as ground truth — if your file does
# not match any known hash, this script prints the computed hash so you can
# compare it to the site yourself. A mismatch is not automatically "corrupt": it
# may simply be a newer official release.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../common.sh
. "${SCRIPT_DIR}/../common.sh"

# label | sha256   (keep in sync with docs/01-bom-and-images.md)
KNOWN_IMAGES=(
  "Trixie 64-bit Full  (2026-04-21)|a6f48a832b965f3b25c9654578ea6056af4001390e85ef9953f7c011cd68d692"
  "Trixie 64-bit Lite  (2026-04-21)|4cd31df026fd82243805a326dc0cafd7383f7e3d30c9413e7044d507aae281e2"
  "Trixie 32-bit Full  (2026-04-21)|eb22fa387c8bf8b2666e66c59ceea63de2bd7610b611b79926c91f839528c241"
  "Trixie 32-bit Lite  (2026-04-21)|f393b8bc3fc49aef49ddc5d5af124333002f34e4b23ede439789145e5280d210"
  "Bookworm 64-bit Lite (Legacy, 2026-04-13)|9bba9c625dd4dd4e1b326dd2551e37a2029db9090bf19ea300649b78c054de6f"
  "Bookworm 32-bit Lite (Legacy, 2026-04-13)|265dfcd2a032ef01c224e8f9fc03b5fd0e31d3a5038f7e578cc5f01e22bc74a9"
)

list_known() {
  printf '%s\n' "Known-good Raspberry Pi OS images (baseline 2026-04):"
  local entry label hash
  for entry in "${KNOWN_IMAGES[@]}"; do
    label="${entry%%|*}"
    hash="${entry##*|}"
    printf '  %-42s %s\n' "${label}" "${hash}"
  done
}

sha256_of() {
  local file="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "${file}" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "${file}" | awk '{print $1}'
  else
    die "Neither sha256sum nor shasum is available."
  fi
}

case "${1:-}" in
  --list | -l)
    list_known
    exit 0
    ;;
  "" | -h | --help)
    printf 'Usage: %s /path/to/image.img.xz | --list\n' "$(basename "$0")" >&2
    exit 1
    ;;
esac

img="$1"
[ -f "${img}" ] || die "File not found: ${img}"

log "Computing SHA256 of ${img} ..."
got="$(sha256_of "${img}")"
log "Computed: ${got}"

for entry in "${KNOWN_IMAGES[@]}"; do
  label="${entry%%|*}"
  hash="${entry##*|}"
  if [ "${got}" = "${hash}" ]; then
    log "MATCH: ${label}"
    log "Image verified against the known baseline."
    exit 0
  fi
done

warn "No match in the known baseline (this may be a newer official release)."
warn "Compare the computed hash above to the official Raspberry Pi downloads page."
exit 2
