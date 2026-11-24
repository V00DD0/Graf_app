#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
version=2.5.1
case ${1:-all} in
  all|deb|appimage|rpm) format=${1:-all} ;;
  *) printf 'Usage: %s [all|deb|appimage|rpm]\n' "$0" >&2; exit 2 ;;
esac
out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT
mkdir -p dist
app="$out/Karta.AppDir"
install -Dm755 packaging/linux/launch.sh "$app/usr/bin/karta-standalone"
install -Dm644 Karta-2.1.html "$app/usr/share/karta-standalone/Karta-2.1.html"
install -Dm644 packaging/linux/karta.desktop "$app/usr/share/applications/karta-standalone.desktop"
install -Dm644 packaging/karta.png "$app/usr/share/icons/hicolor/128x128/apps/karta-standalone.png"
find "$app" -type d -exec chmod 755 {} +
desktop-file-validate "$app/usr/share/applications/karta-standalone.desktop"

if [[ $format == all || $format == deb ]]; then
    install -d -m755 "$app/DEBIAN"
    cat > "$app/DEBIAN/control" <<CONTROL
Package: karta-svyazey-standalone
Version: $version
Section: utils
Priority: optional
Architecture: all
Maintainer: Graf_app contributors <https://github.com/V00DD0/Graf_app>
Depends: xdg-utils
Description: Offline relationship map editor
 Open and edit relationship maps in the default graphical browser.
CONTROL
    chmod 644 "$app/DEBIAN/control"
    dpkg-deb --root-owner-group --build "$app" "dist/Karta-Standalone-$version-all.deb"
    rm -r "$app/DEBIAN"
fi

if [[ $format == all || $format == rpm ]]; then
    mkdir -p "$out/rpm"
    rpmbuild -bb --define "_topdir $out/rpm" --define "karta_version $version" \
        --define "karta_files $app" "$PWD/packaging/linux/karta.spec"
    cp "$out/rpm/RPMS/noarch/"*.rpm "dist/Karta-Standalone-$version-noarch.rpm"
fi

if [[ $format == all || $format == appimage ]]; then
    install -m755 packaging/linux/AppRun "$app/AppRun"
    ln -s usr/share/applications/karta-standalone.desktop "$app/karta-standalone.desktop"
    ln -s usr/share/icons/hicolor/128x128/apps/karta-standalone.png "$app/karta-standalone.png"
    ln -s karta-standalone.png "$app/.DirIcon"
    : "${APPIMAGETOOL:?Set APPIMAGETOOL to the verified AppImage tool path}"
    ARCH=x86_64 "$APPIMAGETOOL" --appimage-extract-and-run --no-appstream \
        "$app" "dist/Karta-Standalone-$version-x86_64.AppImage"
fi
