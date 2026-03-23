#define MyAppName "AI Assistant"
#define MyAppVersion "3.3"
#define MyAppPublisher "zoott28354"
#define MyAppURL "https://github.com/zoott28354/ai_assistant"
#define MyAppExeName "AI_Assistant_v3.3.exe"
#define MyAppDistDir "dist\\AI_Assistant_v3.3"
#define MyAppId "{{D24A7F21-9271-4B6E-BD3E-4F9C7A46B1D2}"
#define MyAppDataDir "{userappdata}\\AI Assistant"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE
OutputDir=installer_output
OutputBaseFilename=AI_Assistant_Setup_v3.3
SetupIconFile=ai_assistant.ico
WizardStyle=modern
Compression=lzma
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Local desktop AI assistant with screenshots, translations and persistent chat.
VersionInfoCopyright=Copyright (c) 2026 zoott28354

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"

[Tasks]
Name: "desktopicon"; Description: "Crea un collegamento sul desktop"; GroupDescription: "Collegamenti aggiuntivi:"; Flags: unchecked
Name: "portablemode"; Description: "Salva i dati accanto all'app (modalita portable)"; Flags: unchecked

[Files]
Source: "{#MyAppDistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\Disinstalla {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Avvia {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
var
  RemoveUserData: Boolean;

procedure CurStepChanged(CurStep: TSetupStep);
var
  MarkerPath: string;
begin
  if CurStep = ssPostInstall then
  begin
    MarkerPath := ExpandConstant('{app}\portable_mode.flag');
    if WizardIsTaskSelected('portablemode') then
    begin
      SaveStringToFile(MarkerPath, 'portable', False);
    end
    else if FileExists(MarkerPath) then
    begin
      DeleteFile(MarkerPath);
    end;
  end;
end;

procedure InitializeUninstallProgressForm();
begin
  RemoveUserData :=
    MsgBox(
      'Vuoi rimuovere anche i dati utente di AI Assistant?' + #13#10#13#10 +
      'Se scegli "Sì", verranno eliminati cronologia chat, configurazione e file legacy.' + #13#10 +
      'Se scegli "No", i dati verranno conservati per una futura reinstallazione.',
      mbConfirmation,
      MB_YESNO
    ) = IDYES;

  if RemoveUserData then
  begin
    Log('User chose to remove application data.');
  end
  else
  begin
    Log('User chose to keep application data.');
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  MarkerPath: string;
begin
  if (CurUninstallStep = usPostUninstall) and RemoveUserData then
  begin
    DelTree(ExpandConstant('{#MyAppDataDir}'), True, True, True);

    DeleteFile(ExpandConstant('{app}\config.json'));
    DeleteFile(ExpandConstant('{app}\chat_history.db'));
    DeleteFile(ExpandConstant('{app}\history_db.json'));

    MarkerPath := ExpandConstant('{app}\portable_mode.flag');
    if FileExists(MarkerPath) then
    begin
      DeleteFile(MarkerPath);
    end;
  end;
end;
