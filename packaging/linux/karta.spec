Name: karta-svyazey
Version: %{karta_version}
Release: 1
Summary: Offline relationship map editor
License: Unspecified
URL: https://github.com/V00DD0/Graf_app
BuildArch: noarch
Requires: xdg-utils

%description
Open and edit relationship maps in the default graphical browser.

%install
mkdir -p "%{buildroot}"
cp -a "%{karta_files}/usr" "%{buildroot}/"

%files
/usr/bin/karta
/usr/share/karta
/usr/share/applications/karta.desktop
/usr/share/icons/hicolor/128x128/apps/karta.png
