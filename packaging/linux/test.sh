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
page="$XDG_DATA_HOME/karta-standalone/Karta-2.1.html"
legacy="$XDG_DATA_HOME/karta/Karta-2.1.html"
mkdir -p "$(dirname "$legacy")"
printf '%s\n' 'Previous installation' > "$legacy"

if [[ -f dist/Karta-Standalone-2.5.3-all.deb ]]; then
    [[ $(dpkg-deb -f dist/Karta-Standalone-2.5.3-all.deb Package) == karta-svyazey-standalone ]]
    dpkg-deb -x dist/Karta-Standalone-2.5.3-all.deb "$tmp/deb"
    [[ $(KARTA_APPDIR="$tmp/deb/usr/share/karta-standalone" "$tmp/deb/usr/bin/karta-standalone") == "$page" ]]
    cmp "$page" Karta-2.1.html
fi
if [[ -f dist/Karta-Standalone-2.5.3-noarch.rpm ]]; then
    [[ $(rpm -qp --qf '%{NAME}' dist/Karta-Standalone-2.5.3-noarch.rpm) == karta-svyazey-standalone ]]
    (cd "$tmp/rpm" && rpm2cpio "$root/dist/Karta-Standalone-2.5.3-noarch.rpm" | cpio -idm --quiet)
    [[ $(KARTA_APPDIR="$tmp/rpm/usr/share/karta-standalone" "$tmp/rpm/usr/bin/karta-standalone") == "$page" ]]
    cmp "$page" Karta-2.1.html
fi
if [[ -f dist/Karta-Standalone-2.5.3-x86_64.AppImage ]]; then
    [[ $(dist/Karta-Standalone-2.5.3-x86_64.AppImage --appimage-extract-and-run) == "$page" ]]
    cmp "$page" Karta-2.1.html
fi
[[ $(cat "$legacy") == 'Previous installation' ]]
printf 'PASS: packaged launchers use a separate stable data path\n'
