import tkinter as tk
from tkinter import filedialog
import os
from ifchelper import Ifc_help
from htmlparser import Parser_html
import shutil
import confighelper
import webbrowser

class Program():
    configuration = None

    def __init__(self):
        ...

    def open_link_github(self, event=None):
        webbrowser.open("https://github.com/i-savelev/ifc_checker")


    def select_folder_ifc(self):
        self.folder_path_ifc = filedialog.askdirectory(title="Выберите папку с ifc")
        self.folder_label_ifc.config(text=self.folder_path_ifc)

    def select_folder_report(self):
        self.folder_path_report = filedialog.askdirectory(title="Выберите папку для отчетов")
        self.folder_label_report.config(text=self.folder_path_report)

    def select_files_ids(self):
        self.files_path_ids = filedialog.askopenfilenames(title="Выберите файлы ids")
        self.file_label_ids.config(text=self.files_path_ids)

    def select_file_config(self):
        self.files_path_config = filedialog.askopenfilename(title="Выберите файл json")
        self.file_label_config.config(text=self.files_path_config)
        if self.files_path_config != '':
            self.configuration = confighelper.read_json_config(self.files_path_config)
    
    def save_config_sample(self):
        self.folder_path_save_config = filedialog.asksaveasfilename(
            title="Выберите папку сохранения",
            filetypes=[("JSON Files", "*.json")]
            )
        confighelper.save_json_config_template(self.folder_path_save_config)
        self.file_label_config_save.config(text=f'Файл сохранен{self.folder_path_save_config}')

    def check_ifc(self):
        """
        Функция проверяет модели из указанной папки и выгружает отчеты по каждой модели а так же сводный отчет
        """
        html_files = []
        if os.path.exists(self.folder_path_report):
            shutil.rmtree(self.folder_path_report)
            os.makedirs(self.folder_path_report, exist_ok=True)
        self.list_box.delete(0, tk.END)  
        if self.configuration is not None: print(f'Конфигурация:\n{self.configuration}')
        counter = 0
        counter_sum = 0
        for root, dirs, files in os.walk(self.folder_path_ifc):
            for ifc_file in files:
                if ifc_file.endswith('.ifc'):
                    for path_ids_file in self.files_path_ids:
                        ids_file_name = os.path.basename(path_ids_file).replace('.ids', '')
                        ifc_file_name = os.path.basename(ifc_file).replace('.ifc', '')
                        if self.configuration is not None:
                            if not confighelper.ifc_exist_in_ids_dict(
                                ids_file_name, 
                                ifc_file_name, 
                                self.configuration
                                ):
                                continue
                        counter_sum += 1
        for root, dirs, files in os.walk(self.folder_path_ifc):
            relative_path = os.path.relpath(root, self.folder_path_ifc)
            target_path_for_report = os.path.join(self.folder_path_report, relative_path)
            os.makedirs(target_path_for_report, exist_ok=True)
            for ifc_file in files:
                path_ifc_file = os.path.join(root, ifc_file)
                if path_ifc_file.endswith('.ifc'):
                    for path_ids_file in self.files_path_ids:
                        ids_file_name = os.path.basename(path_ids_file).replace('.ids', '')
                        ifc_file_name = os.path.basename(path_ifc_file).replace('.ifc', '')
                        report_name = f'{ifc_file_name}({ids_file_name})'

                        if self.configuration is not None:
                            if not confighelper.ifc_exist_in_ids_dict(
                                ids_file_name, 
                                ifc_file_name, 
                                self.configuration
                                ):
                                continue
                        counter += 1
                        try:
                            Ifc_help.check_ifc_file(
                                path_ifc_file, 
                                path_ids_file, 
                                target_path_for_report,
                                report_name
                                )
                            html_file_path = os.path.join(target_path_for_report.rstrip(r'\\.'), f'{report_name}.html')
                            html_files.append(html_file_path)
                            Parser_html.add_file_name_to_report(ifc_file_name, html_file_path)

                            self.list_box.insert(
                                tk.END, 
                                f'[{counter}/{counter_sum}]{report_name}.html - готово'
                                )  
                            print(f'[{counter}/{counter_sum}]{html_file_path} - готово')
                        except Exception as e:
                            self.list_box.insert(
                                tk.END, 
                                f'[{counter}/{counter_sum}]!Ошибка: {report_name}.html - {e}'
                                )
                            print(e)
        try:
            Parser_html.get_consolidated_html(html_files, self.folder_path_report, 'Сводный отчет')
            self.list_box.insert(tk.END, f'Сводный отчет.html - готово')
            self.list_box.insert(tk.END, f'Подготовлено отчетов: {counter} шт.')
            print(f'Сводный отчет.html - готово')
            print(f'Подготовлено отчетов: {counter} шт.')
        except Exception as e:
            self.list_box.insert(tk.END, f'!Ошибка: {e}')
            print(f'Ошибка: {e}')

    def inicialize(self):
        self.root = tk.Tk()
        self.root.title("Проверка IFC")

        # Кнопка выбора папки с файлами ifc
        self.button_folder_ifc = tk.Button(self.root, text="Выбрать папку ifc", command=self.select_folder_ifc)
        self.button_folder_ifc.grid(row=0, column=0, padx=(10, 0), pady=10)
        self.folder_label_ifc = tk.Label(self.root, text="", width=80)
        self.folder_label_ifc.grid(row=0, column=1, padx=(10, 10))

        # Кнопка выбора файла ids
        self.button_file_ids = tk.Button(self.root, text="Выбрать файлы ids", command=self.select_files_ids)
        self.button_file_ids.grid(row=1, column=0, padx=(10, 0), pady=10)
        self.file_label_ids = tk.Label(self.root, text="", width=80)
        self.file_label_ids.grid(row=1, column=1, padx=(10, 10))

        # Кнопка выбора папки для отчетов
        self.button_folder_report = tk.Button(self.root, text="Выбрать папку отчетов\n(файлы в папке удаляются перед записью)", command=self.select_folder_report)
        self.button_folder_report.grid(row=2, column=0, padx=(10, 0), pady=10)
        self.folder_label_report = tk.Label(self.root, text="", width=80)
        self.folder_label_report.grid(row=2, column=1, padx=(10, 10))

        # Кнопка выбора файла  конфигурации
        self.button_config = tk.Button(self.root, text="Выбрать файл конфигурации\n(не обязательно)", command=self.select_file_config)
        self.button_config.grid(row=3, column=0, padx=(10, 0), pady=10)
        self.file_label_config = tk.Label(self.root, text="", width=80)
        self.file_label_config.grid(row=3, column=1, padx=(10, 10))

        # Кнопка сохранения шаблона конфигурации
        self.button_config_save = tk.Button(self.root, text="Сохранить шаблон конфигурации", command=self.save_config_sample)
        self.button_config_save.grid(row=4, column=0, padx=(10, 0), pady=10)
        self.file_label_config_save = tk.Label(self.root, text="", width=80)
        self.file_label_config_save.grid(row=4, column=1, padx=(10, 10))

        # Кнопка для запуска функции
        self.button_function = tk.Button(self.root, text="Запустить проверку", command=self.check_ifc)
        self.button_function.grid(row=5, column=0, padx=(10, 0), pady=10)

        # Текстовое поле
        self.list_box = tk.Listbox(self.root, height=5, width=100)
        self.list_box.grid(row=5, column=1, padx=(10, 0), pady=10)

        # Ссылка на github
        self.github_link  = tk.Label(self.root, text="Источник: github.com/i-savelev/ifc_checker", fg="blue", cursor="hand2")
        self.github_link.grid(row=6, column=0)
        self.github_link.bind("<Button-1>", self.open_link_github)


        self.root.mainloop()

if __name__ == '__main__':
    interface = Program()
    interface.folder_path_ifc = r''
    interface.files_path_ids = [r'']
    interface.folder_path_report = r''
    root = tk.Tk()
    interface.list_box = tk.Listbox(root, height=5, width=100)
    interface.configuration = confighelper.read_json_config(r'')
    interface.check_ifc()