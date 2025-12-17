; Inno Setup installer for Clustering-Visualizer-Game
; Publisher: Nour Ltaief
; Icon source: Assets/logo.png (converted to build/logo.ico by tools/make_icon.py)

#define AppName "ClusteringVisualizerGame"
#define AppPublisher "Nour Ltaief"
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#define AppExeName "ClusteringVisualizerGame.exe"

[Setup]
AppId={{6F94884C-9AE9-49E0-A8D7-7F09E4F2A1C1}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=dist-installer
OutputBaseFilename={#AppName}-Setup-{#AppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=build\logo.ico
UninstallDisplayIcon={app}\{#AppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
; Bundle the PyInstaller one-folder output
Source: "dist\ClusteringVisualizerGame\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent


