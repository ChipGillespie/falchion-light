#!/bin/bash
set -euo pipefail
source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
rule=/etc/udev/rules.d/70-falchion-light.rules
if [[ -e "$rule" ]]; then
  echo "Refusing to overwrite existing $rule" >&2
  exit 1
fi
install -m 0644 "$source_dir/70-falchion-light.rules" "$rule"
udevadm control --reload-rules
udevadm trigger --action=change --subsystem-match=hidraw --property-match=ID_VENDOR_ID=0b05 --property-match=ID_MODEL_ID=1b04 --property-match=ID_USB_INTERFACE_NUM=01
udevadm settle --timeout=5
