#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tools="$ANDROID_HOME/build-tools/35.0.0"
jar="$ANDROID_HOME/platforms/android-35/android.jar"
if [[ ! -x "$tools/aapt2" || ! -f "$jar" ]]; then
  "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" 'platforms;android-35' 'build-tools;35.0.0'
fi
out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT
mkdir -p "$out/classes" "$out/dex" "$out/assets"
cp Karta-2.1.html "$out/assets/index.html"
javac -encoding UTF-8 -source 8 -target 8 -bootclasspath "$jar:$tools/core-lambda-stubs.jar" -d "$out/classes" android/MainActivity.java
"$tools/d8" --lib "$jar" --min-api 26 --output "$out/dex" "$out"/classes/local/karta/app/*.class
if [[ -n "${KARTA_KEYSTORE:-}" ]]; then
  sed 's/local.karta.preview24/local.karta.app/g' android/AndroidManifest.xml > "$out/manifest.xml"
else
  cp android/AndroidManifest.xml "$out/manifest.xml"
fi
"$tools/aapt2" link -I "$jar" --manifest "$out/manifest.xml" -A "$out/assets" -o "$out/raw.apk"
(cd "$out/dex" && zip -q "$out/raw.apk" classes.dex)
"$tools/zipalign" -f 4 "$out/raw.apk" "$out/aligned.apk"
if [[ -n "${KARTA_KEYSTORE:-}" ]]; then
  : "${KARTA_PASSFILE:?}"
  key="$KARTA_KEYSTORE"
  pass="$KARTA_PASSFILE"
  apk=Karta-2.5.0.apk
else
  key="$out/test.p12"
  pass="$out/pass"
  openssl rand -hex 24 > "$out/pass"
  keytool -genkeypair -keystore "$out/test.p12" -storepass:file "$out/pass" -alias karta -keyalg RSA -keysize 3072 -validity 3650 -dname "CN=Karta 2.4 Test"
  apk=Karta-2.4-test.apk
fi
sign_args=(--ks "$key" --ks-pass "file:$pass")
if [[ -n "${KARTA_KEY_ALIAS:-}" ]]; then
  sign_args+=(--ks-key-alias "$KARTA_KEY_ALIAS")
fi
if [[ -n "${KARTA_KEY_PASSFILE:-}" ]]; then
  sign_args+=(--key-pass "file:$KARTA_KEY_PASSFILE")
fi
"$tools/apksigner" sign "${sign_args[@]}" --v4-signing-enabled false --out "$out/signed.apk" "$out/aligned.apk"
"$tools/apksigner" verify --verbose "$out/signed.apk"
"$tools/zipalign" -c 4 "$out/signed.apk"
unzip -p "$out/signed.apk" assets/index.html | cmp Karta-2.1.html -
"$tools/aapt" dump permissions "$out/signed.apk"

if [[ -n "${KARTA_KEYSTORE:-}" ]]; then
  cert_digest() { "$tools/apksigner" verify --print-certs "$1" | sed -n 's/^Signer #1 certificate SHA-256 digest: //p'; }
  previous=$(cert_digest downloads/Karta-2.4-test.apk)
  actual=$(cert_digest "$out/signed.apk")
  if [[ -z "$previous" || "$actual" != "$previous" ]]; then
    printf 'Android signature differs from the distributed local.karta.app APK. Expected SHA-256: %s\n' "$previous" >&2
    exit 1
  fi
  mv "$out/signed.apk" "$apk"
  exit 0
fi
mv "$out/signed.apk" "$apk"

# Separately installed instrumentation lives only on the disposable emulator.
mkdir -p "$out/testclasses" "$out/testdex"
javac -encoding UTF-8 -source 8 -target 8 -bootclasspath "$jar:$tools/core-lambda-stubs.jar" -d "$out/testclasses" android/DeviceTest.java
"$tools/d8" --lib "$jar" --min-api 26 --output "$out/testdex" "$out"/testclasses/local/karta/qa/*.class
printf '%s' '<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="local.karta.qa"><uses-sdk android:minSdkVersion="26" android:targetSdkVersion="35"/><application/><instrumentation android:name="local.karta.qa.DeviceTest" android:targetPackage="local.karta.preview24"/></manifest>' > "$out/testmanifest.xml"
"$tools/aapt2" link -I "$jar" --manifest "$out/testmanifest.xml" -o "$out/raw-test.apk"
(cd "$out/testdex" && zip -q "$out/raw-test.apk" classes.dex)
"$tools/zipalign" -f 4 "$out/raw-test.apk" "$out/aligned-test.apk"
"$tools/apksigner" sign --ks "$key" --ks-pass "file:$pass" --out Karta-device-test.apk "$out/aligned-test.apk"

# Build the previous editor with the same disposable identity for install -r testing.
base=bd64b47dd67e07e6284ceb569907b783f00d626c
git show "$base:Karta-2.1.html" > "$out/assets/index.html"
git show "$base:android/AndroidManifest.xml" | sed 's/local.karta.preview23/local.karta.preview24/g' > "$out/previous.xml"
git show "$base:android/MainActivity.java" > "$out/MainActivity.java"
mkdir "$out/oldclasses" "$out/olddex"
javac -encoding UTF-8 -source 8 -target 8 -bootclasspath "$jar:$tools/core-lambda-stubs.jar" -d "$out/oldclasses" "$out/MainActivity.java"
"$tools/d8" --lib "$jar" --min-api 26 --output "$out/olddex" "$out"/oldclasses/local/karta/app/*.class
"$tools/aapt2" link -I "$jar" --manifest "$out/previous.xml" -A "$out/assets" -o "$out/base.apk"
(cd "$out/olddex" && zip -q "$out/base.apk" classes.dex)
"$tools/zipalign" -f 4 "$out/base.apk" "$out/base-aligned.apk"
"$tools/apksigner" sign --ks "$key" --ks-pass "file:$pass" --out Karta-upgrade-base.apk "$out/base-aligned.apk"
