#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TGZ_NAME="${1:-ids-peak_2.11.0.0-178_amd64.tgz}"
TGZ_PATH="${SCRIPT_DIR}/${TGZ_NAME}"
PKG_DIR=""

if [ ! -f "$TGZ_PATH" ]; then
  echo "Missing ${TGZ_NAME}."
  echo "Download it manually from IDS (license required) and place it in:"
  echo "  ${SCRIPT_DIR}"
  exit 1
fi

tar -xvzf "$TGZ_PATH" -C "$SCRIPT_DIR"

PKG_DIR="$(find "$SCRIPT_DIR" -maxdepth 1 -type d -name "ids-peak_*_amd64" | sort | tail -n1)"
if [ -z "$PKG_DIR" ]; then
  echo "Could not find extracted IDS peak folder under ${SCRIPT_DIR}"
  exit 1
fi

UDEV_RULE="${PKG_DIR}/lib/udev/rules.d/99-ids-usb-access.rules"
if [ -f "$UDEV_RULE" ]; then
  sudo cp "$UDEV_RULE" /etc/udev/rules.d/
  sudo udevadm control --reload-rules
  sudo udevadm trigger
else
  echo "Warning: udev rule not found at ${UDEV_RULE}"
fi
python3 -m pip install ids_peak_ipl
python3 -m pip install ids_peak
python3 -m pip install ids_peak_afl

# Replace any existing IDS block in .bashrc, then append the new one.
if grep -qF "IDS camera library paths" ~/.bashrc; then
    awk '
        BEGIN {skip=0}
        /# IDS camera library paths/ {skip=1}
        skip==0 {print}
        skip==1 && /^$/ {skip=0}
    ' ~/.bashrc > ~/.bashrc.ids_tmp
    mv ~/.bashrc.ids_tmp ~/.bashrc
fi
cat <<EOF >> ~/.bashrc
# IDS camera library paths
IDS_PEAK_ROOT="${PKG_DIR}"
export LD_LIBRARY_PATH="\${IDS_PEAK_ROOT}/lib/x86_64-linux-gnu:\${LD_LIBRARY_PATH}"
export GENICAM_GENTL64_PATH="\${IDS_PEAK_ROOT}/lib/x86_64-linux-gnu/ids-peak/cti:\${GENICAM_GENTL64_PATH}"

EOF
echo "iDS peak library paths updated in .bashrc"

echo "Finished installation for iDS camera."
