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
; Oylama/sayaç sunucuları için gelen-bağlantı izni: kurulumda BİR KEZ UAC onayı
; ister, jam günü Windows güvenlik duvarı penceresi hiç çıkmaz.
Name: "fwrule"; Description: "Güvenlik duvarı izni ekle (LAN oylaması/sayaç için önerilir)"

[Files]
Source: "dist\JamDeck\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[Code]
// Güvenlik duvarı kuralı: netsh yönetici ister -> 'runas' ile tek UAC onayı.
// Kullanıcı UAC'yi iptal ederse sessizce geçilir (kurulum hatasız sürer);
// o durumda izin penceresi ilk sunucu başlatmada her zamanki gibi çıkar.
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  Params: String;
begin
  if (CurStep = ssPostInstall) and WizardIsTaskSelected('fwrule') then
  begin
    Params := 'advfirewall firewall add rule name="JamDeck" dir=in action=allow program="'
              + ExpandConstant('{app}') + '\{#MyAppExeName}" enable=yes profile=any';
    ShellExec('runas', 'netsh.exe', Params, '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usPostUninstall then
    ShellExec('runas', 'netsh.exe',
      'advfirewall firewall delete rule name="JamDeck"',
      '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;
