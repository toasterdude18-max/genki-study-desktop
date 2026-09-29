; Genki Study — per-user installer (no admin/UAC required).
; Build: build_release.ps1 passes /DMyAppVersion=<ver> to override the default below.

#define MyAppName "Genki Study"
#define MyAppVersion "1.0.0"
#define MyAppExeName "Genki Study.exe"

[Setup]
AppId={{6E0B7F3A-4C9E-4D2B-A1E6-9F3C2D5B8A71}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=toasterdude18-max
AppPublisherURL=https://github.com/toasterdude18-max/genki-study-desktop
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\release
OutputBaseFilename=Genki-Study-Setup-v{#MyAppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupLogging=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "..\release\Genki Study\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
