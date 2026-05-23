"""Публичные функции для проверки IFC моделей по IDS.

Модуль содержит бизнес-логику, которая не зависит от графического интерфейса.
Его функции можно использовать как из `tkinter`-интерфейса, так и из
ноутбуков или внешних Python-скриптов.
"""

from __future__ import annotations

import logging
import os
import shutil
from collections.abc import Callable, Iterable

from ifc_checker_script import confighelper
from ifc_checker_script.htmlparser import Parser_html
from ifc_checker_script.ifchelper import Ifc_help
from ifc_checker_script.simple_logger import Logger


StatusCallback = Callable[[str], None]


def _emit_status(callback: StatusCallback | None, message: str) -> None:
    """Передает текстовое сообщение во внешний обработчик статуса.

    :param callback: Функция обратного вызова для вывода статуса пользователю.
        Если значение равно ``None``, сообщение никуда не передается.
    :param message: Текст сообщения о текущем состоянии проверки.
    :returns: ``None``.
    """

    if callback is not None:
        callback(message)


def _normalize_ids_paths(files_path_ids: Iterable[str]) -> list[str]:
    """Преобразует набор путей к IDS в обычный список.

    :param files_path_ids: Коллекция путей к файлам ``.ids``.
    :returns: Список путей, пригодный для повторного прохода в циклах.
    """

    return [path for path in files_path_ids]


def _prepare_report_directory(folder_path_report: str) -> None:
    """Подготавливает папку отчетов перед запуском проверки.

    Если папка уже существует, она полностью очищается. После этого папка
    создается заново, чтобы в ней не осталось отчетов от прошлых запусков.

    :param folder_path_report: Путь к папке, в которую будут записаны отчеты.
    :returns: ``None``.
    """

    if os.path.exists(folder_path_report):
        shutil.rmtree(folder_path_report)
    os.makedirs(folder_path_report, exist_ok=True)


def _configure_logger(folder_path_report: str) -> None:
    """Настраивает файловый логгер для текущего запуска проверки.

    :param folder_path_report: Путь к папке отчетов, где должен быть создан
        файл лога.
    :returns: ``None``.
    """

    log_path = os.path.join(folder_path_report, "ifc_checker.log")
    Logger.configure(log_file=log_path, level=logging.DEBUG)
    Logger.init("IFC_Checker")


def _is_check_allowed(
    ids_file_name: str,
    ifc_file_name: str,
    configuration: dict | None,
) -> bool:
    """Определяет, нужно ли выполнять проверку IFC файла по выбранному IDS.

    :param ids_file_name: Имя IDS файла без расширения.
    :param ifc_file_name: Имя IFC файла без расширения.
    :param configuration: Словарь конфигурации сопоставления IDS и IFC.
        Если значение равно ``None``, проверка всегда разрешена.
    :returns: ``True``, если проверку нужно выполнять, иначе ``False``.
    """

    if configuration is None:
        return True
    return confighelper.ifc_exist_in_ids_dict(
        ids_file_name,
        ifc_file_name,
        configuration,
    )


def _count_checks(
    folder_path_ifc: str,
    files_path_ids: list[str],
    configuration: dict | None,
) -> int:
    """Подсчитывает общее количество будущих проверок.

    :param folder_path_ifc: Корневая папка с IFC файлами.
    :param files_path_ids: Список путей к IDS файлам.
    :param configuration: Словарь конфигурации сопоставления IDS и IFC.
    :returns: Общее количество проверок, которое будет выполнено.
    """

    counter_sum = 0
    for root, _, files in os.walk(folder_path_ifc):
        for ifc_file in files:
            if not ifc_file.endswith(".ifc"):
                continue
            ifc_file_name = os.path.basename(ifc_file).replace(".ifc", "")
            for path_ids_file in files_path_ids:
                ids_file_name = os.path.basename(path_ids_file).replace(".ids", "")
                if _is_check_allowed(ids_file_name, ifc_file_name, configuration):
                    counter_sum += 1
    return counter_sum


def check_ifc(
    folder_path_ifc: str,
    files_path_ids: Iterable[str],
    folder_path_report: str,
    configuration: dict | None = None,
    status_callback: StatusCallback | None = None,
    delete_empty_checks: bool = False,
) -> dict:
    """Проверяет IFC модели по IDS и формирует отдельные и сводный HTML-отчеты.

    Функция повторяет поведение графического интерфейса, но не зависит от
    `tkinter`. Это позволяет вызывать ее из внешних скриптов и Jupyter
    notebooks, передавая пути и при необходимости собственный обработчик
    сообщений о прогрессе.

    :param folder_path_ifc: Путь к корневой папке с IFC файлами.
    :param files_path_ids: Набор путей к IDS файлам, по которым нужно
        выполнять проверку.
    :param folder_path_report: Путь к папке, куда нужно сохранить отчеты.
    :param configuration: Необязательный словарь сопоставления IDS и IFC,
        полученный через ``read_json_config``. Если значение равно ``None``,
        каждый IFC файл проверяется по всем IDS файлам.
    :param status_callback: Необязательная функция обратного вызова для
        передачи текстовых сообщений о прогрессе.
    :param delete_empty_checks: Если установлено значение ``True``, после
        генерации отчетов из HTML-файлов будут удалены секции со статусом
        ``skipped``.
    :returns: Словарь с итоговой информацией о запуске:
        ``report_count`` - количество подготовленных отдельных отчетов,
        ``summary_report`` - путь к сводному отчету,
        ``log_path`` - путь к лог-файлу,
        ``html_files`` - список путей к отдельным отчетам,
        ``deleted_skipped_sections`` - словарь с количеством удаленных секций
        ``skipped`` по каждому файлу либо ``None``, если очистка не запускалась.
    """

    normalized_ids_paths = _normalize_ids_paths(files_path_ids)
    html_files: list[str] = []
    deleted_items_by_file: dict[str, int] | None = None

    _prepare_report_directory(folder_path_report)
    _configure_logger(folder_path_report)

    Logger.info("Начало проверки IFC")
    Logger.separator()
    Logger.info(f"Папка IFC: {folder_path_ifc}")
    Logger.info(f"Папка отчетов: {folder_path_report}")
    Logger.info(f"Файлы IDS: {len(normalized_ids_paths)} шт.")
    for ids_file in normalized_ids_paths:
        Logger.info(f"  - {ids_file}")

    if configuration is not None:
        Logger.info("Конфигурация загружена")
        Logger.data(configuration, label="Конфигурация")
        print(f"Конфигурация:\n{configuration}")
    else:
        Logger.info("Конфигурация не указана (проверка всех файлов)")

    Logger.separator()
    Logger.info("Подсчет файлов для проверки...")
    counter_sum = _count_checks(folder_path_ifc, normalized_ids_paths, configuration)
    Logger.info(f"Найдено проверок: {counter_sum}")
    Logger.separator()
    Logger.info("Начало проверки файлов...")

    counter = 0
    for root, _, files in os.walk(folder_path_ifc):
        relative_path = os.path.relpath(root, folder_path_ifc)
        target_path_for_report = os.path.join(folder_path_report, relative_path)
        os.makedirs(target_path_for_report, exist_ok=True)

        for ifc_file in files:
            path_ifc_file = os.path.join(root, ifc_file)
            if not path_ifc_file.endswith(".ifc"):
                continue

            ifc_file_name = os.path.basename(path_ifc_file).replace(".ifc", "")
            for path_ids_file in normalized_ids_paths:
                ids_file_name = os.path.basename(path_ids_file).replace(".ids", "")
                report_name = f"{ifc_file_name}({ids_file_name})"

                if not _is_check_allowed(ids_file_name, ifc_file_name, configuration):
                    Logger.debug(f"Пропуск: {report_name} (не в конфигурации)")
                    continue

                counter += 1
                Logger.info(f"[{counter}/{counter_sum}] Проверка: {report_name}")
                Logger.debug(f"  IFC: {path_ifc_file}")
                Logger.debug(f"  IDS: {path_ids_file}")

                try:
                    Ifc_help.check_ifc_file(
                        path_ifc_file,
                        path_ids_file,
                        target_path_for_report,
                        report_name,
                    )
                    html_file_path = os.path.join(
                        target_path_for_report.rstrip(r"\\."),
                        f"{report_name}.html",
                    )
                    html_files.append(html_file_path)
                    Parser_html.add_file_name_to_report(ifc_file_name, html_file_path)

                    success_message = (
                        f"[{counter}/{counter_sum}]{report_name}.html - готово"
                    )
                    _emit_status(status_callback, success_message)
                    Logger.info(f"  Готово: {html_file_path}")
                    print(f"[{counter}/{counter_sum}]{html_file_path} - готово")
                except Exception as error:
                    error_message = (
                        f"[{counter}/{counter_sum}]!Ошибка: {report_name}.html - {error}"
                    )
                    _emit_status(status_callback, error_message)
                    Logger.error(f"  Ошибка: {report_name} - {error}")
                    print(error)

    Logger.separator()
    Logger.info("Формирование сводного отчета...")

    try:
        Parser_html.get_consolidated_html(
            html_files,
            folder_path_report,
            "Сводный отчет",
        )
        _emit_status(status_callback, "Сводный отчет.html - готово")
        _emit_status(status_callback, f"Подготовлено отчетов: {counter} шт.")
        Logger.info("Сводный отчет создан")
        Logger.info(f"Всего отчетов: {counter} шт.")
        print("Сводный отчет.html - готово")
        print(f"Подготовлено отчетов: {counter} шт.")
    except Exception as error:
        _emit_status(status_callback, f"!Ошибка: {error}")
        Logger.error(f"Ошибка создания сводного отчета: {error}")
        print(f"Ошибка: {error}")

    Logger.separator()
    Logger.info("Проверка завершена")
    log_path = Logger.path()
    Logger.info(f"Лог сохранен: {log_path}")

    if delete_empty_checks:
        Logger.separator()
        Logger.info("Удаление пропущенных проверок из HTML-отчетов...")
        deleted_items_by_file = Parser_html.delete_skipped(folder_path_report)
        for file_path, deleted_data in deleted_items_by_file.items():
            Logger.info(
                f"Очищен отчет: {file_path}. Удалено секций: {deleted_data['count']}"
            )
            for deleted_title in deleted_data['titles']:
                Logger.info(f"  Удалена пропущенная проверка: {deleted_title}")
        _emit_status(
            status_callback,
            "Пропущенные проверки удалены из HTML-отчетов",
        )

    _emit_status(status_callback, f"Лог: {log_path}")
    print(f"Лог: {log_path}")

    return {
        "report_count": counter,
        "summary_report": os.path.join(folder_path_report, "Сводный отчет.html"),
        "log_path": log_path,
        "html_files": html_files,
        "deleted_skipped_sections": (
            None
            if deleted_items_by_file is None
            else {
                file_path: deleted_data["count"]
                for file_path, deleted_data in deleted_items_by_file.items()
            }
        ),
    }
