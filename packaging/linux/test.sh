#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
root=$PWD
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
mkdir "$tmp/bin" "$tmp/deb" "$tmp/rpm"
cat > "$tmp/bin/xdg-open" <<'LAUNCHER'
#!/bin/sh
printf '%s\n' "$1"
LAUNCHER
chmod 755 "$tmp/bin/xdg-open"
export PATH="$tmp/bin:$PATH" XDG_DATA_HOME="$tmp/user data"
page="$XDG_DATA_HOME/karta/Karta-2.1.html"

if [[ -f dist/Karta-2.5.0-all.deb ]]; then
    dpkg-deb -x dist/Karta-2.5.0-all.deb "$tmp/deb"
    [[ $(KARTA_APPDIR="$tmp/deb/usr/share/karta" "$tmp/deb/usr/bin/karta") == "$page" ]]
    cmp "$page" Karta-2.1.html
fi
if [[ -f dist/Karta-2.5.0-noarch.rpm ]]; then
    (cd "$tmp/rpm" && rpm2cpio "$root/dist/Karta-2.5.0-noarch.rpm" | cpio -idm --quiet)
    [[ $(KARTA_APPDIR="$tmp/rpm/usr/share/karta" "$tmp/rpm/usr/bin/karta") == "$page" ]]
    cmp "$page" Karta-2.1.html
fi
if [[ -f dist/Karta-2.5.0-x86_64.AppImage ]]; then
    [[ $(dist/Karta-2.5.0-x86_64.AppImage --appimage-extract-and-run) == "$page" ]]
    cmp "$page" Karta-2.1.html
fi
printf 'PASS: packaged launchers open the same offline editor at a stable URL\n'
