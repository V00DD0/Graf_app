Unicode True
Name "Карта связей"
OutFile "Karta-2.5.0-Windows.exe"
InstallDir "$LOCALAPPDATA\Karta"
RequestExecutionLevel user
SetCompressor /SOLID lzma

Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Карта связей"
  SetShellVarContext current
  SetOutPath "$INSTDIR"
  File "..\..\Karta.exe"
  File "..\..\Karta-2.1.html"
  CreateShortCut "$SMPROGRAMS\Карта связей.lnk" "$INSTDIR\Karta.exe"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Karta" "DisplayName" "Карта связей"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Karta" "DisplayVersion" "2.5.0"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Karta" "UninstallString" '$\"$INSTDIR\Uninstall.exe$\"'
SectionEnd

Section "Uninstall"
  SetShellVarContext current
  Delete "$SMPROGRAMS\Карта связей.lnk"
  Delete "$INSTDIR\Karta.exe"
  Delete "$INSTDIR\Karta-2.1.html"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Karta"
SectionEnd
