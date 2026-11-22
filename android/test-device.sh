#!/usr/bin/env bash
set -euo pipefail
adb install -r -g Karta-2.3-test.apk
adb install -r Karta-device-test.apk
adb shell pm grant local.karta.preview23 android.permission.READ_CALL_LOG
now=$(date +%s)
seed() {
 adb shell content insert --uri content://call_log/calls --bind number:s:+12025550137 --bind type:i:"$1" --bind duration:l:"$2" --bind date:l:"$(($3*1000))" --bind new:i:0
}
seed 1 60 "$now"
seed 2 21 "$now"
seed 3 0 "$now"
seed 2 0 "$now"
seed 1 120 "$((now-95*86400))"
adb shell am instrument -w local.karta.qa/local.karta.qa.DeviceTest | tee device-result.txt
grep -F 'PASS: native consent' device-result.txt
