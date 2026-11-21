$ErrorActionPreference = 'Stop'
$root = Join-Path $env:TEMP ("Карта тест " + [guid]::NewGuid())
$work = Join-Path $root 'другая рабочая папка'
New-Item -ItemType Directory -Path $work -Force | Out-Null
Copy-Item (Join-Path $PSScriptRoot 'Karta.exe') $root
Copy-Item (Join-Path $PSScriptRoot 'Karta-2.1.html') $root
# The temporary HTML copy reports readiness by navigating to a one-use loopback address.
$page = Join-Path $root 'Karta-2.1.html'
$token = [guid]::NewGuid().ToString()
$listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,0)
$listener.Start()
try {
    $port = $listener.LocalEndpoint.Port
    $html = [IO.File]::ReadAllText($page)
    $probe = "<script>const qaTimer=setInterval(()=>{const editor=document.getElementById('kv2');if(editor?.dataset.initialized && !editor.inert && document.querySelector('[data-act=more]')){clearInterval(qaTimer);location.replace('http://127.0.0.1:$port/$token');}},100);</script>"
    [IO.File]::WriteAllText($page,$html.Insert($html.LastIndexOf('</body>'),$probe))
    $launcher = Start-Process -FilePath (Join-Path $root 'Karta.exe') -WorkingDirectory $work -PassThru
    if (!$launcher.WaitForExit(20000)) { throw 'Launcher did not exit' }
    if ($launcher.ExitCode -ne 0) { throw "Launcher returned $($launcher.ExitCode)" }
    $deadline=[datetime]::UtcNow.AddSeconds(45)
    while ([datetime]::UtcNow -lt $deadline) {
        if (!$listener.Pending()) { Start-Sleep -Milliseconds 200; continue }
        $client=$listener.AcceptTcpClient()
        try {
            $stream=$client.GetStream()
            $stream.ReadTimeout=4000
            $reader=[IO.StreamReader]::new($stream)
            $request=$reader.ReadLine()
            $agent=''
            while ($line=$reader.ReadLine()) { if ($line -like 'User-Agent:*') {$agent=$line} }
            $bytes=[Text.Encoding]::ASCII.GetBytes("HTTP/1.1 200 OK`r`nContent-Length: 2`r`nConnection: close`r`n`r`nOK")
            $stream.Write($bytes,0,$bytes.Length)
            if ($request -match "^GET /$token HTTP/" -and $agent -match 'Chrome/|Firefox/|Edg/') {
                Write-Output "PASS: the shipped EXE opened the editor, which initialized and reported readiness. $agent"
                exit 0
            }
        } finally { $client.Dispose() }
    }
    Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'chrome|msedge|firefox|OpenWith' } | Select-Object Name,ProcessId,SessionId | Format-Table
    throw 'The launched document did not report readiness'
} finally { $listener.Stop() }
