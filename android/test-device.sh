#!/usr/bin/env bash
set -euo pipefail
pkg=local.karta.preview24
adb install -r Karta-upgrade-base.apk
adb install -r Karta-device-test.apk
test_mode(){
 adb shell am instrument -w -e mode "$1" local.karta.qa/local.karta.qa.DeviceTest | tee device-result.txt
 grep -F "PASS:" device-result.txt
}
test_mode seed
adb install -r Karta-2.4-test.apk
# Insert only fictional fixture data on the disposable emulator.
adb shell content insert --uri content://com.android.contacts/raw_contacts --bind account_type:s:local --bind account_name:s:karta-qa
raw=$(adb shell content query --uri content://com.android.contacts/raw_contacts --projection _id --where "account_name=\'karta-qa\'" | sed -n 's/.*_id=\([0-9]*\).*/\1/p' | tail -1)
test -n "$raw"
adb shell "content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:$raw --bind mimetype:s:vnd.android.cursor.item/name --bind 'data1:s:QA Contact'"
adb shell content insert --uri content://com.android.contacts/data --bind raw_contact_id:i:"$raw" --bind mimetype:s:vnd.android.cursor.item/phone_v2 --bind data1:s:+12025550137 --bind data2:i:2
adb shell pm set-permission-flags "$pkg" android.permission.READ_CALL_LOG user-fixed
test_mode denied
adb shell pm clear-permission-flags "$pkg" android.permission.READ_CALL_LOG user-fixed
adb shell pm grant "$pkg" android.permission.READ_CALL_LOG
now=$(date +%s)
seed() {
 adb shell content insert --uri content://call_log/calls --bind number:s:+12025550137 --bind type:i:"$1" --bind duration:l:"$2" --bind date:l:"$(($3*1000))" --bind new:i:0
}
seed 1 60 "$now"
seed 2 21 "$now"
seed 3 0 "$now"
seed 2 0 "$now"
seed 1 120 "$((now-95*86400))"
test_mode calls
python3 android/test-upgrade.py
