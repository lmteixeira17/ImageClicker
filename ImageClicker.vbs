Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

strScriptPath = objFSO.GetParentFolderName(WScript.ScriptFullName)
strAppPath = objFSO.BuildPath(strScriptPath, "app_qt.py")

objShell.CurrentDirectory = strScriptPath
objShell.Run "pythonw """ & strAppPath & """", 0, False
