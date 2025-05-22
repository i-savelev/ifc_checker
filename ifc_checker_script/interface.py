import tkinter as tk
from tkinter import filedialog
import os


class Interface():
    """
    Интерфейс программы
    """
    def __init__(self, func):
        self.func = func
        self.files = []
        self.folder_path_1 = ''
        self.folder_path_2 = ''
        self.file_path = ''

    def select_folder_1(self):
        self.folder_path_1 = filedialog.askdirectory(title="Выберите папку с ifc")
        self.folder_label_1.config(text=self.folder_path_1)
        self.files = os.listdir(self.folder_path_1)  # Получение списка файлов

    def select_folder_2(self):
        self.folder_path_2 = filedialog.askdirectory(title="Выберите папку для отчетов")
        self.folder_label_2.config(text=self.folder_path_2)

    def select_files(self):
        self.files_path = filedialog.askopenfilenames(title="Выберите файл")
        self.file_label.config(text=self.files_path)

    def set_button_function(self):
        self.func(self.files, self.folder_path_1, self.files_path, self.folder_path_2, self.file_list_box)

    def inicialize(self):
        self.root = tk.Tk()
        self.root.title("Проверка IFC")

        # Кнопка выбора папки с файлами ifc
        self.folder_button_1 = tk.Button(self.root, text="Выбрать папку ifc", command=self.select_folder_1)
        self.folder_button_1.grid(row=0, column=0, padx=(10, 0), pady=10)  # Размещение объекта в сетке

        # Текст для передачи пути к папке ifc
        self.folder_label_1 = tk.Label(self.root, text="", width=80)
        self.folder_label_1.grid(row=0, column=1, padx=(10, 10))

        # Кнопка выбора файла ids
        self.file_button = tk.Button(self.root, text="Выбрать файлы ids", command=self.select_files)
        self.file_button.grid(row=1, column=0, padx=(10, 0), pady=10)

        # Текст для передачи пути к файлу
        self.file_label = tk.Label(self.root, text="", width=80)
        self.file_label.grid(row=1, column=1, padx=(10, 10))

        # Кнопка выбора папки для отчетов
        self.folder_button_2 = tk.Button(self.root, text="Выбрать папку отчетов", command=self.select_folder_2)
        self.folder_button_2.grid(row=2, column=0, padx=(10, 0), pady=10)

        # Текст для передачи пути к папке ids
        self.folder_label_2 = tk.Label(self.root, text="", width=80)
        self.folder_label_2.grid(row=2, column=1, padx=(10, 10))

        # Кнопка для запуска функции
        self.function_button = tk.Button(self.root, text="Запустить проверку", command=self.set_button_function)
        self.function_button.grid(row=3, column=0, padx=(10, 0), pady=10)

        # Текстовое поле
        self.file_list_box = tk.Listbox(self.root, height=5, width=100)
        self.file_list_box.grid(row=3, column=1, padx=(10, 0), pady=10)

        self.root.mainloop()
