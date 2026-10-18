' Flash-free launcher for HuntezPatch: no cmd window at all, straight to GUI.
' Run this instead of start_program.bat. Needs pythonw (ships with CPython).
Option Explicit
Dim sh, fso, here
Set sh = CreateObject("Wscript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
here = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = here
sh.Run "pythonw main.py", 0, False
