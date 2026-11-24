Name: karta-svyazey-standalone
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
/usr/bin/karta-standalone
/usr/share/karta-standalone
/usr/share/applications/karta-standalone.desktop
/usr/share/icons/hicolor/128x128/apps/karta-standalone.png
