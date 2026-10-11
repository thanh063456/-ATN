$path = "dataset\annotations\annotation_new_pseudo.txt"
while ($true) {
    $count = 0
    try {
        $fs = [System.IO.File]::Open($path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        $reader = New-Object System.IO.StreamReader($fs)
        while ($reader.ReadLine() -ne $null) { $count++ }
        $reader.Close()
    } catch {}
    
    if ($count -ge 30880) {
        Write-Output "Monitoring finished. Lines reached $count."
        break
    }
    
    # Also check if the python script has crashed/stopped running and we haven't reached the count
    $py = Get-Process -Name "python" -ErrorAction SilentlyContinue
    if (-not $py) {
        # Python is not running anymore, exit monitor so we can notify user it stopped
        Write-Output "Python process not found. Monitoring aborted at line $count."
        break
    }
    
    Start-Sleep -Seconds 60
}
