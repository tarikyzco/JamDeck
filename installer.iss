; JamDeck kurulum betiği (Inno Setup 6)
; Derleme: build_release.ps1 çağırır → ISCC /DMyAppVersion=X.Y.Z installer.iss
; ÖNEMLİ: Kurulum yeri {localappdata}\JamDeck (yönetici izni YOK) — otomatik
; güncelleyici kendi klasörüne yazdığı için Program Files KULLANILMAZ.

#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif
#define MyAppName "JamDeck"
#define MyAppExeName "Ayazjam Manager.exe"

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
SetupIconFile=AyazJam Logo.ico
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

[Files]
Source: "dist\Ayazjam Manager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
