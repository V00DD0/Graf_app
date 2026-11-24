Unicode True
Name "Карта связей Standalone"
OutFile "Karta-Standalone-2.5.2-Windows.exe"
InstallDir "$LOCALAPPDATA\KartaStandalone"
RequestExecutionLevel user
SetCompressor /SOLID lzma

Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Карта связей Standalone"
  SetShellVarContext current
  SetOutPath "$INSTDIR"
  File "..\..\Karta.exe"
  File "..\..\Karta-2.1.html"
  CreateShortCut "$SMPROGRAMS\Карта связей Standalone.lnk" "$INSTDIR\Karta.exe"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\KartaStandalone" "DisplayName" "Карта связей Standalone"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\KartaStandalone" "DisplayVersion" "2.5.2"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\KartaStandalone" "UninstallString" '$\"$INSTDIR\Uninstall.exe$\"'
SectionEnd

Section "Uninstall"
  SetShellVarContext current
  Delete "$SMPROGRAMS\Карта связей Standalone.lnk"
  Delete "$INSTDIR\Karta.exe"
  Delete "$INSTDIR\Karta-2.1.html"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\KartaStandalone"
SectionEnd
