' reap-mcp.vbs - run tools\reap-mcp.ps1 with no console window.
' Task Scheduler launches powershell.exe directly as a console app, which flashes a
' cmd window every run. wscript is a GUI process, so window style 0 is actually hidden.
Dim sh, cmd
Set sh = CreateObject("WScript.Shell")
cmd = "powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass " & _
      "-File ""E:\AI\memory\ai-unlimited-memory\tools\reap-mcp.ps1"" " & _
      "-Apply -GuardMinutes 10 -KeepNewest 1"
sh.Run cmd, 0, False
