; JamDeck kurulum betiği (Inno Setup 6)
; Derleme: build_release.ps1 çağırır → ISCC /DMyAppVersion=X.Y.Z installer.iss
; ÖNEMLİ: Kurulum yeri {localappdata}\JamDeck (yönetici izni YOK) — otomatik
; güncelleyici kendi klasörüne yazdığı için Program Files KULLANILMAZ.

#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif
#define MyAppName "JamDeck"
#define MyAppExeName "JamDeck.exe"

[Setup]
AppId={{B7E26C5A-9A1B-4F0E-8C3D-2A47D1E5F9B4}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher=tarikyzco
AppPublisherURL=https://github.com/tarikyzco/JamDeck
DefaultDirName={localappdata}\JamDeck
DisableProgramGroupPage=yes
DisableDirPage=auto
PrivilegesRequired=lowest
OutputDir=release
OutputBaseFilename=JamDeck-Setup-v{#MyAppVersion}
SetupIconFile=JamDeck.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
; NOT: LAN güvenlik duvarı görevi KALDIRILDI — oylama artık online (tünel/localhost),
; gelen-bağlantı (inbound) kuralına gerek yok → kurulumda UAC izni istenmez.

[Files]
Source: "dist\JamDeck\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
