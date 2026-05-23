import tkinter as tk
from tkinter import filedialog
import os
import webbrowser
from ifc_checker_script import (
    check_ifc,
    read_json_config,
    save_json_config_template,
)

class Program():
    configuration = None

    def __init__(self):
        ...

    def open_link_github(self, event=None):
        webbrowser.open("https://github.com/i-savelev/ifc_checker")

    def open_report_folder(self):
        """Открыть папку с отчетами в проводнике."""
        if not hasattr(self, "folder_path_report") or not self.folder_path_report:
            self.list_box.insert(tk.END, "Папка отчетов не указана")
            return
        if os.path.exists(self.folder_path_report):
            os.startfile(self.folder_path_report)
        else:
            self.list_box.insert(tk.END, "Папка отчетов не существует")

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
            self.configuration = read_json_config(self.files_path_config)
    
    def save_config_sample(self):
        self.folder_path_save_config = filedialog.asksaveasfilename(
            title="Выберите папку сохранения",
            filetypes=[("JSON Files", "*.json")]
            )
        save_json_config_template(self.folder_path_save_config)
        self.file_label_config_save.config(text=f'Файл сохранен{self.folder_path_save_config}')

    def check_ifc(self):
        """Запускает проверку из UI через публичную функцию модуля."""
        self.list_box.delete(0, tk.END)
        try:
            check_ifc(
                folder_path_ifc=self.folder_path_ifc,
                files_path_ids=self.files_path_ids,
                folder_path_report=self.folder_path_report,
                configuration=self.configuration,
                status_callback=self._append_status,
                delete_empty_checks=self.delete_empty_checks_var.get(),
            )
        except Exception as error:
            self.list_box.insert(tk.END, f'!Ошибка: {error}')

    def _append_status(self, message):
        """Добавляет сообщение о прогрессе в текстовое поле интерфейса."""
        self.list_box.insert(tk.END, message)

    def inicialize(self):
        self.root = tk.Tk()
        self.root.title("Проверка IFC")
        self.delete_empty_checks_var = tk.BooleanVar(value=False)

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

        # Галочка очистки пропущенных проверок
        self.checkbox_delete_empty_checks = tk.Checkbutton(
            self.root,
            text="Удалять пропущенные проверки из отчетов",
            variable=self.delete_empty_checks_var,
        )
        self.checkbox_delete_empty_checks.grid(row=5, column=0, padx=(10, 0), pady=10, sticky="w")

        # Фрейм для кнопок запуска и открытия папки
        self.frame_buttons = tk.Frame(self.root)
        self.frame_buttons.grid(row=6, column=0, padx=(10, 0), pady=10)

        # Кнопка для запуска функции
        self.button_function = tk.Button(self.frame_buttons, text="Запустить проверку", command=self.check_ifc)
        self.button_function.pack(side=tk.TOP, pady=(0, 5))

        # Кнопка открытия папки отчетов
        self.button_open_folder = tk.Button(self.frame_buttons, text="Открыть папку отчетов", command=self.open_report_folder)
        self.button_open_folder.pack(side=tk.TOP)

        # Текстовое поле
        self.list_box = tk.Listbox(self.root, height=5, width=100)
        self.list_box.grid(row=6, column=1, padx=(10, 0), pady=10)

        # Ссылка на github
        self.github_link  = tk.Label(self.root, text="Источник: github.com/i-savelev/ifc_checker", fg="blue", cursor="hand2")
        self.github_link.grid(row=7, column=0)
        self.github_link.bind("<Button-1>", self.open_link_github)


        self.root.mainloop()

if __name__ == '__main__':
    interface = Program()
    interface.folder_path_ifc = r''
    interface.files_path_ids = [r'']
    interface.folder_path_report = r''
    root = tk.Tk()
    interface.list_box = tk.Listbox(root, height=5, width=100)
    interface.configuration = read_json_config(r'')
    interface.check_ifc()
