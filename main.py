"""
Проверка ifc файлов по требования IDS с помощью ifcopenshell и ifctester

Для формирования исполняемого exe файла необходимо ввеести в консоль слудующую команду:
pyinstaller --onefile --collect-all ifctester --collect-all ifcopenshell --collect-all bs4 --name ifc_checker main.py
"""

from ifc_checker_script.interface import Program


interface = Program()
interface.inicialize()
