"""
Проверка ifc файлов по требования IDS с помощью ifcopenshell и ifctester

Для формирования исполняемого exe файла необходимо ввеести в консоль слудующую команду:
pyinstaller --onefile --collect-all ifctester --collect-all ifcopenshell --collect-all bs4 --windowed --name ifc_checker main.py
"""

from interface import Interface
import tkinter as tk
from ifchelper import Ifc_help
from htmlparser import Parser_html


def check_ifc(ifc_folder_files, path_ifc_folder, path_ids_file, path_report_folder, list_box):
    """
    Функция проверяет модели иp указанной папки и выгружает отчеты покаждой модеели а так же сводный отчет
    """
    list_box.delete(0, tk.END)  # Очистка текстового поля
    for file in ifc_folder_files:
        if file.endswith('.ifc'):
            ifc_file_path = f'{path_ifc_folder}/{file}'
            try:
                Ifc_help.check_ifc_file(ifc_file_path, path_ids_file, path_report_folder)
                list_box.insert(tk.END, f'{file.replace('.ifc', '')}.html - готово')  # Вывод статуса
            except Exception as e:
                list_box.insert(tk.END, f'!Ошибка: {file} - {e}')  # Вывод ошибок
    try:
        Parser_html.get_consolidated_html(path_report_folder, 'Сводный отчет')
        list_box.insert(tk.END, f'Сводный отчет.html - готово')
    except Exception as e:
        list_box.insert(tk.END, f'!Ошибка: {e}')


interface = Interface(check_ifc)
interface.inicialize()
