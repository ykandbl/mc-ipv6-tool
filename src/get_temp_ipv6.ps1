Get-NetIPAddress -AddressFamily IPv6 | Where-Object {$_.SuffixOrigin -eq 5} | Select-Object -ExpandProperty IPAddress
