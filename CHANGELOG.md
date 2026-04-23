# Changelog

All notable changes to Sirius AI Tray Assistant are documented here.

## v3.6.0

- Renamed the project from AI Assistant to Sirius AI Tray Assistant.
- Updated application metadata, installer output name, About panel, README links, and GitHub repository references for the new project identity.
- Changed the project license from MIT to GNU GPL v3 or later and added a NOTICE file.
- Added safe migration from the legacy `%AppData%\AI Assistant` data folder to `%AppData%\Sirius AI Tray Assistant`.
- Updated uninstall cleanup so choosing to remove user data also removes the legacy data folder when present.
- Replaced native browser-style chat confirm/prompt popups with an integrated in-chat modal for rename/delete actions.
- Harmonized dialog buttons with a lighter text-style layout across confirmation, configuration, and About dialogs.

## v3.5.2

- Refined the About dialog with a more consistent update-check button layout.
- Moved update checking into the About panel instead of the main tray menu.
- Improved chat rendering to reduce visible refresh/flicker on slower PCs.
- Renamed the tray area action from rectangle wording to screenshot wording.
- Kept the installer safer for upgrades by supporting current-user/all-users installation and previous-path reuse.

## v3.5.1

- Added chat attachments from the composer: images are sent as multimodal inputs, while readable documents are added as text context.
- Original attached documents are preserved in chat history and included in ZIP exports.
- Added scanned PDF fallback: PDFs without extractable text are rendered as page images and sent to compatible vision/OCR models.
- Added a Maintenance tab in Configure to open the local data folder and compact the SQLite history database.
- Database compaction now permanently purges already-deleted sessions before running VACUUM, so large deleted chats actually release disk space.
- Added friendly display names for Custom OpenAI-compatible endpoints, reflected in the tray, chat header, and session sidebar.
- Persisted the active tray backend and model selection across app restarts.
- Changed the Windows installer to support current-user or all-users installation, keep user data in `%AppData%`, remove the portable-mode checkbox, reuse previous install paths when detected, and offer optional startup with Windows.
- Added a `Check for updates` button in the About panel that checks GitHub Releases and opens the release page when a newer version is available.
- Completed multilingual strings for the updated configuration dialog and attachment UI.
- Updated documentation for custom endpoints, API keys, attachments, and the v3.5.1 installer.

## v3.5

- Added per-chat export from the sidebar menu as PDF or ZIP with Markdown and original image assets.
- Improved PDF export using the WebEngine print pipeline for better layout, images, tables, code blocks, and readable A4 margins.
- Added right-click copy support inside the chat window.
- Improved session updates: edited chats move correctly in the sidebar and refresh their visible timestamp.
- The active tray model/backend now becomes the runtime context when continuing an older chat, so the chat header and exported metadata reflect the latest model used.
- Clarified documentation around custom tray prompts, local persistence, and backend-managed context limits.

## v3.4

- Conservative internal refactor from a single-file app toward a clearer modular structure.
- Full multilingual foundation for the interface and installer.
- Multilingual `About` dialog in the tray, with clickable GitHub link.
- English-first public documentation and improved Windows installer flow.

## v3.3

- Major UI and installer upgrade, with a new English-capable interface.
- Webview-based chat redesign with improved sidebar and session handling.
- Native Windows snipping flow for screen analysis.
- More reliable persistence, search, rename, delete, and better installer metadata.

## v3.2

- Modernized desktop UI and persistent backend configuration.
- Better separation between runtime configuration and the main application flow.

## v2.1.1

- Portable historical baseline built around a monolithic `main.py`.
- Italian-first interface and workflow.
- EXE icon fixes and repository cleanup for the portable line.
