from functools import partial

from PyQt6.QtWidgets import QMenu

from core.i18n import tr


def backend_display_name(backend_urls, backend):
    display_name = backend_urls.get("backend_display_names", {}).get(backend, "")
    return display_name.strip() or backend


def build_tray_menu(
    language,
    tray,
    active_backend,
    active_model,
    backend_urls,
    backend_names,
    openai_compatible_names,
    models,
    handlers,
):
    menu = QMenu()
    menu.addAction(tr("tray_analyze_area", language), handlers["start_vision"])
    menu.addAction(tr("tray_analyze_clipboard", language), handlers["start_text_grab"])
    menu.addSeparator()
    menu.addAction(tr("tray_open_chat", language), handlers["open_chat"])
    menu.addSeparator()
    menu.addAction(tr("tray_config_backend", language), handlers["open_config"])
    menu.addAction(tr("tray_about", language), handlers["open_about"])
    menu.addAction(tr("tray_check_updates", language), handlers["check_updates"])
    menu.addSeparator()

    backend_menu = menu.addMenu(tr("tray_engine", language))
    available_backends = list(backend_names)
    for backend in openai_compatible_names:
        custom_backend_url = backend_urls.get("backends", {}).get(backend, "").strip()
        if custom_backend_url:
            available_backends.append(backend)

    for backend in available_backends:
        action = backend_menu.addAction(backend_display_name(backend_urls, backend))
        action.setCheckable(True)
        action.setChecked(active_backend == backend)
        action.triggered.connect(partial(handlers["set_backend"], backend))

    models_menu = menu.addMenu(tr("tray_models", language))
    for model in models:
        action = models_menu.addAction(model)
        action.setCheckable(True)
        action.setChecked(active_model == model)
        action.triggered.connect(partial(handlers["set_model"], model))

    menu.addSeparator()
    menu.addAction(tr("tray_exit", language), handlers["quit_app"])
    tray.setContextMenu(menu)
    return menu
