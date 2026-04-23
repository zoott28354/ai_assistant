#define MyProjectRoot ".."
#include "app_meta.iss"
#define MyAppDistDir MyProjectRoot + "\\dist\\" + MyAppDistName
#define MyOutputDir MyProjectRoot + "\\installer_output"
#define MyAppId "{{D24A7F21-9271-4B6E-BD3E-4F9C7A46B1D2}"
#define MyAppDataDir "{userappdata}\\Sirius AI Tray Assistant"
#define MyLegacyAppDataDir "{userappdata}\\AI Assistant"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile={#MyProjectRoot}\LICENSE
OutputDir={#MyOutputDir}
OutputBaseFilename={#MyOutputBaseFilename}
SetupIconFile={#MyProjectRoot}\ai_assistant.ico
WizardStyle=modern
Compression=lzma
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Local desktop tray AI assistant with screenshots, translations and persistent chat.
VersionInfoCopyright=Copyright (c) 2026 zoott28354
ShowLanguageDialog=yes
UsePreviousLanguage=no

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[CustomMessages]
italian.DesktopIcon=Crea un collegamento sul desktop
english.DesktopIcon=Create a desktop shortcut
spanish.DesktopIcon=Crear un acceso directo en el escritorio
french.DesktopIcon=Creer un raccourci sur le bureau
german.DesktopIcon=Desktopverknuepfung erstellen
portuguese.DesktopIcon=Criar um atalho na area de trabalho
russian.DesktopIcon=Создать ярлык на рабочем столе
japanese.DesktopIcon=デスクトップにショートカットを作成
chinesesimplified.DesktopIcon=创建桌面快捷方式

italian.AdditionalIcons=Collegamenti aggiuntivi:
english.AdditionalIcons=Additional shortcuts:
spanish.AdditionalIcons=Accesos directos adicionales:
french.AdditionalIcons=Raccourcis supplementaires :
german.AdditionalIcons=Zusaetzliche Verknuepfungen:
portuguese.AdditionalIcons=Atalhos adicionais:
russian.AdditionalIcons=Дополнительные ярлыки:
japanese.AdditionalIcons=追加ショートカット:
chinesesimplified.AdditionalIcons=其他快捷方式：

italian.StartWithWindows=Avvia {#MyAppName} all'avvio di Windows
english.StartWithWindows=Start {#MyAppName} when Windows starts
spanish.StartWithWindows=Iniciar {#MyAppName} al iniciar Windows
french.StartWithWindows=Lancer {#MyAppName} au demarrage de Windows
german.StartWithWindows={#MyAppName} beim Windows-Start ausfuehren
portuguese.StartWithWindows=Iniciar {#MyAppName} ao iniciar o Windows
russian.StartWithWindows=Запускать {#MyAppName} при запуске Windows
japanese.StartWithWindows=Windows 起動時に {#MyAppName} を起動
chinesesimplified.StartWithWindows=Windows 启动时启动 {#MyAppName}

italian.RunApp=Avvia {#MyAppName}
english.RunApp=Launch {#MyAppName}
spanish.RunApp=Iniciar {#MyAppName}
french.RunApp=Lancer {#MyAppName}
german.RunApp={#MyAppName} starten
portuguese.RunApp=Iniciar {#MyAppName}
russian.RunApp=Запустить {#MyAppName}
japanese.RunApp={#MyAppName} を起動
chinesesimplified.RunApp=启动 {#MyAppName}

italian.RemoveUserDataPrompt=Vuoi rimuovere anche i dati utente di {#MyAppName}?%n%nSe scegli "Sì", verranno eliminati cronologia chat, configurazione e file legacy.%nSe scegli "No", i dati verranno conservati per una futura reinstallazione.
english.RemoveUserDataPrompt=Do you also want to remove {#MyAppName} user data?%n%nIf you choose "Yes", chat history, configuration and legacy files will be deleted.%nIf you choose "No", the data will be kept for a future reinstall.
spanish.RemoveUserDataPrompt=Deseas eliminar tambien los datos de usuario de {#MyAppName}?%n%nSi eliges "Si", se eliminaran el historial del chat, la configuracion y los archivos heredados.%nSi eliges "No", los datos se conservaran para una futura reinstalacion.
french.RemoveUserDataPrompt=Voulez-vous aussi supprimer les donnees utilisateur de {#MyAppName} ?%n%nSi vous choisissez "Oui", l'historique du chat, la configuration et les fichiers herites seront supprimes.%nSi vous choisissez "Non", les donnees seront conservees pour une future reinstallation.
german.RemoveUserDataPrompt=Moechtest du auch die Benutzerdaten von {#MyAppName} entfernen?%n%nWenn du "Ja" waehlst, werden Chatverlauf, Konfiguration und Legacy-Dateien geloescht.%nWenn du "Nein" waehlst, bleiben die Daten fuer eine spaetere Neuinstallation erhalten.
portuguese.RemoveUserDataPrompt=Deseja remover tambem os dados do usuario do {#MyAppName}?%n%nSe escolher "Sim", o historico do chat, a configuracao e os arquivos legados serao removidos.%nSe escolher "Nao", os dados serao mantidos para uma futura reinstalacao.
russian.RemoveUserDataPrompt=Вы также хотите удалить пользовательские данные {#MyAppName}?%n%nЕсли выбрать "Да", будут удалены история чата, конфигурация и устаревшие файлы.%nЕсли выбрать "Нет", данные будут сохранены для будущей переустановки.
japanese.RemoveUserDataPrompt={#MyAppName} のユーザーデータも削除しますか？%n%n「はい」を選ぶと、チャット履歴、設定、旧形式ファイルが削除されます。%n「いいえ」を選ぶと、データは今後の再インストール用に保持されます。
chinesesimplified.RemoveUserDataPrompt=是否还要删除 {#MyAppName} 的用户数据？%n%n如果选择“是”，聊天记录、配置和旧版文件将被删除。%n如果选择“否”，这些数据将保留，以便将来重新安装时使用。

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startup"; Description: "{cm:StartWithWindows}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#MyAppDistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Registry]
Root: HKA; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: startup

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:RunApp}"; Flags: nowait postinstall skipifsilent

[Code]
var
  RemoveUserData: Boolean;

procedure InitializeUninstallProgressForm();
begin
  RemoveUserData :=
    MsgBox(
      ExpandConstant('{cm:RemoveUserDataPrompt}'),
      mbConfirmation,
      MB_YESNO
    ) = IDYES;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  MarkerPath: string;
begin
  if (CurUninstallStep = usPostUninstall) and RemoveUserData then
  begin
    DelTree(ExpandConstant('{#MyAppDataDir}'), True, True, True);
    DelTree(ExpandConstant('{#MyLegacyAppDataDir}'), True, True, True);

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
