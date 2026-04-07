#define MyProjectRoot ".."
#include "app_meta.iss"
#define MyAppDistDir MyProjectRoot + "\\dist\\AI_Assistant"
#define MyOutputDir MyProjectRoot + "\\installer_output"
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
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Local desktop AI assistant with screenshots, translations and persistent chat.
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

[CustomMessages]
italian.DesktopIcon=Crea un collegamento sul desktop
english.DesktopIcon=Create a desktop shortcut
spanish.DesktopIcon=Crear un acceso directo en el escritorio
french.DesktopIcon=Creer un raccourci sur le bureau
german.DesktopIcon=Desktopverknuepfung erstellen
portuguese.DesktopIcon=Criar um atalho na area de trabalho
russian.DesktopIcon=Создать ярлык на рабочем столе
japanese.DesktopIcon=デスクトップにショートカットを作成

italian.AdditionalIcons=Collegamenti aggiuntivi:
english.AdditionalIcons=Additional shortcuts:
spanish.AdditionalIcons=Accesos directos adicionales:
french.AdditionalIcons=Raccourcis supplementaires :
german.AdditionalIcons=Zusaetzliche Verknuepfungen:
portuguese.AdditionalIcons=Atalhos adicionais:
russian.AdditionalIcons=Дополнительные ярлыки:
japanese.AdditionalIcons=追加ショートカット:

italian.PortableMode=Salva i dati accanto all'app (modalita portable)
english.PortableMode=Store data next to the app (portable mode)
spanish.PortableMode=Guardar los datos junto a la app (modo portable)
french.PortableMode=Enregistrer les donnees a cote de l'application (mode portable)
german.PortableMode=Daten neben der App speichern (Portable-Modus)
portuguese.PortableMode=Salvar os dados ao lado do app (modo portable)
russian.PortableMode=Сохранять данные рядом с приложением (portable mode)
japanese.PortableMode=アプリの横にデータを保存する（ポータブルモード）

italian.RunApp=Avvia {#MyAppName}
english.RunApp=Launch {#MyAppName}
spanish.RunApp=Iniciar {#MyAppName}
french.RunApp=Lancer {#MyAppName}
german.RunApp={#MyAppName} starten
portuguese.RunApp=Iniciar {#MyAppName}
russian.RunApp=Запустить {#MyAppName}
japanese.RunApp={#MyAppName} を起動

italian.RemoveUserDataPrompt=Vuoi rimuovere anche i dati utente di AI Assistant?%n%nSe scegli "Sì", verranno eliminati cronologia chat, configurazione e file legacy.%nSe scegli "No", i dati verranno conservati per una futura reinstallazione.
english.RemoveUserDataPrompt=Do you also want to remove AI Assistant user data?%n%nIf you choose "Yes", chat history, configuration and legacy files will be deleted.%nIf you choose "No", the data will be kept for a future reinstall.
spanish.RemoveUserDataPrompt=Deseas eliminar tambien los datos de usuario de AI Assistant?%n%nSi eliges "Si", se eliminaran el historial del chat, la configuracion y los archivos heredados.%nSi eliges "No", los datos se conservaran para una futura reinstalacion.
french.RemoveUserDataPrompt=Voulez-vous aussi supprimer les donnees utilisateur de AI Assistant ?%n%nSi vous choisissez "Oui", l'historique du chat, la configuration et les fichiers herites seront supprimes.%nSi vous choisissez "Non", les donnees seront conservees pour une future reinstallation.
german.RemoveUserDataPrompt=Moechtest du auch die Benutzerdaten von AI Assistant entfernen?%n%nWenn du "Ja" waehlst, werden Chatverlauf, Konfiguration und Legacy-Dateien geloescht.%nWenn du "Nein" waehlst, bleiben die Daten fuer eine spaetere Neuinstallation erhalten.
portuguese.RemoveUserDataPrompt=Deseja remover tambem os dados do usuario do AI Assistant?%n%nSe escolher "Sim", o historico do chat, a configuracao e os arquivos legados serao removidos.%nSe escolher "Nao", os dados serao mantidos para uma futura reinstalacao.
russian.RemoveUserDataPrompt=Вы также хотите удалить пользовательские данные AI Assistant?%n%nЕсли выбрать "Да", будут удалены история чата, конфигурация и устаревшие файлы.%nЕсли выбрать "Нет", данные будут сохранены для будущей переустановки.
japanese.RemoveUserDataPrompt=AI Assistant のユーザーデータも削除しますか？%n%n「はい」を選ぶと、チャット履歴、設定、旧形式ファイルが削除されます。%n「いいえ」を選ぶと、データは今後の再インストール用に保持されます。

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "portablemode"; Description: "{cm:PortableMode}"; Flags: unchecked

[Files]
Source: "{#MyAppDistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:RunApp}"; Flags: nowait postinstall skipifsilent

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
