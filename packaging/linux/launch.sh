#!/bin/sh
set -eu

app_dir=${KARTA_APPDIR:-/usr/share/karta-standalone}
data_dir=${XDG_DATA_HOME:-"$HOME/.local/share"}/karta-standalone
page=$data_dir/Karta-2.1.html
umask 077
mkdir -p "$data_dir"

# Keep one file URL so the browser keeps the same IndexedDB origin after upgrades.
if ! cmp -s "$app_dir/Karta-2.1.html" "$page"; then
    staged=$(mktemp "$data_dir/.karta-html-XXXXXX")
    trap 'rm -f "$staged"' EXIT HUP INT TERM
    cp "$app_dir/Karta-2.1.html" "$staged"
    mv -f "$staged" "$page"
    trap - EXIT HUP INT TERM
fi
exec xdg-open "$page"
