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

[Code]
// Eksik bağımlılıkları kurulum sırasında indirip kurar:
//  - WebView2 Runtime: yoksa PyWebView eski MSHTML motoruna düşer → modern JS
//    çalışmaz, arayüz siyah ekranda asılı kalır (özellikle Windows Sandbox / temiz
//    Windows). Evergreen bootstrapper per-user kurar (yönetici gerekmez).
//  - Tailscale: online oylama (Funnel) bunu kullanır. 64-bit ({pf64}) altına kurulur;
//    eksikse MSI indirilip /passive (GÖRÜNÜR ilerleme, sessiz red yok) kurulur.
var
  DownloadPage: TDownloadWizardPage;

function IsWebView2Installed: Boolean;
var v: String;
begin
  Result :=
    (RegQueryStringValue(HKLM, 'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', v) and (v <> '') and (v <> '0.0.0.0')) or
    (RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', v) and (v <> '') and (v <> '0.0.0.0')) or
    (RegQueryStringValue(HKCU, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', v) and (v <> '') and (v <> '0.0.0.0'));
end;

function IsTailscaleInstalled: Boolean;
begin
  Result := FileExists(ExpandConstant('{pf64}\Tailscale\tailscale.exe'));
end;

function OnDownloadProgress(const Url, FileName: String; const Progress, ProgressMax: Int64): Boolean;
begin
  Result := True;
end;

procedure InitializeWizard;
begin
  DownloadPage := CreateDownloadPage('Gerekli bileşenler', 'WebView2 / Tailscale indiriliyor...', @OnDownloadProgress);
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var needDl: Boolean;
begin
  Result := True;
  if CurPageID = wpReady then begin
    DownloadPage.Clear;
    needDl := False;
    if not IsWebView2Installed then begin
      DownloadPage.Add('https://go.microsoft.com/fwlink/p/?LinkId=2124703', 'MicrosoftEdgeWebview2Setup.exe', '');
      needDl := True;
    end;
    if not IsTailscaleInstalled then begin
      DownloadPage.Add('https://pkgs.tailscale.com/stable/tailscale-setup-latest-amd64.msi', 'tailscale-setup.msi', '');
      needDl := True;
    end;
    if needDl then begin
      DownloadPage.Show;
      try
        try
          DownloadPage.Download;
        except
          // indirme başarısızsa kurulumu engelleme; bileşen uygulama içinde de kurulabilir
        end;
      finally
        DownloadPage.Hide;
      end;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var rc: Integer;
begin
  if CurStep = ssPostInstall then begin
    // WebView2 bootstrapper'ı GÖRÜNÜR çalıştır (/silent YOK → kullanıcı ilerlemeyi görür,
    // arka planda 150 MB inerken donmuş sanılmaz). Per-user kurar, yönetici istemez.
    if (not IsWebView2Installed) and FileExists(ExpandConstant('{tmp}\MicrosoftEdgeWebview2Setup.exe')) then
      Exec(ExpandConstant('{tmp}\MicrosoftEdgeWebview2Setup.exe'), '', '', SW_SHOW, ewWaitUntilTerminated, rc);
    // Tailscale MSI: /passive (görünür ilerleme); yönetici gerektiği için 'runas' ile yükselt.
    if (not IsTailscaleInstalled) and FileExists(ExpandConstant('{tmp}\tailscale-setup.msi')) then
      ShellExec('runas', 'msiexec.exe',
        '/i "' + ExpandConstant('{tmp}\tailscale-setup.msi') + '" /passive /norestart',
        '', SW_SHOW, ewWaitUntilTerminated, rc);
  end;
end;
