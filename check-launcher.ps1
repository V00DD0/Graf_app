$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$root = Join-Path $env:TEMP ("Карта тест " + [guid]::NewGuid())
$work = Join-Path $root 'другая рабочая папка'
New-Item -ItemType Directory -Path $work -Force | Out-Null
Copy-Item (Join-Path $PSScriptRoot 'Karta.exe') $root
Copy-Item (Join-Path $PSScriptRoot 'Karta-2.1.html') $root
# A unique page title identifies exactly this copy if another map is already open.
$page = Join-Path $root 'Karta-2.1.html'
$token = "Karta QA " + [guid]::NewGuid()
$html = [IO.File]::ReadAllText($page)
if (!$html.Contains('<title>Карта связей 2.1</title>')) { throw 'Unexpected HTML title' }
[IO.File]::WriteAllText($page,$html.Replace('<title>Карта связей 2.1</title>',"<title>$token</title>"))
$launcher = Start-Process -FilePath (Join-Path $root 'Karta.exe') -WorkingDirectory $work -PassThru
if (!$launcher.WaitForExit(20000)) { throw 'Launcher did not exit. Check for an error or application choice dialog.' }
if ($launcher.ExitCode -ne 0) { throw "Launcher returned $($launcher.ExitCode)" }
$deadline = [datetime]::UtcNow.AddSeconds(35)
do {
    $windows = [System.Windows.Automation.AutomationElement]::RootElement.FindAll(
        [System.Windows.Automation.TreeScope]::Children,
        [System.Windows.Automation.Condition]::TrueCondition)
    foreach ($win in $windows) {
        if ($win.Current.Name -like "*$token*") {
            $owner = Get-Process -Id $win.Current.ProcessId
            if ($owner.ProcessName -in @('msedge','chrome','firefox','brave','opera','vivaldi')) {
                Write-Output "PASS: launcher opened the expected local HTML in $($owner.ProcessName)."
                exit 0
            }
        }
    }
    Start-Sleep -Milliseconds 400
} while ([datetime]::UtcNow -lt $deadline)
throw 'Launcher returned zero, but opening the expected browser document was not verified.'
