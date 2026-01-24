import logging
import os
from typing import Optional  # type: ignore
import inspect


class NonLockingFileHandler(logging.FileHandler):
    """
    FileHandler который открывает файл только на время записи.

    После каждой записи файл закрывается, что позволяет удалять/перемещать
    файл лога без ошибок блокировки.
    """

    def emit(self, record):
        """Записать лог-сообщение, открывая и закрывая файл для каждой записи."""
        # Открываем файл
        if self.stream is None:
            self.stream = self._open()

        try:
            # Записываем
            logging.StreamHandler.emit(self, record)
            # Сбрасываем буфер
            self.flush()
        finally:
            # Закрываем файл после записи
            self.close()


class Logger:
    """
    Фасад для удобного статического логирования без необходимости создания экземпляров.

    Использует модуль `logging` и автоматически инициализирует файловый обработчик
    при первом вызове любого метода логирования, если не был инициализирован ранее.
    По умолчанию логи записываются в 'AppData\\Local\\Temp\\Pynamo/app.log' относительно корня проекта.

    Класс поддерживает настройку пути к файлу и уровня логирования через метод `configure`.
    Также предоставляет метод `clear` для безопасной очистки лог-файла даже под Windows.

    Example:
        >>> Logger.info("Приложение запущено")
        >>> Logger.error("Произошла ошибка", name="db")
    """

    _initialized: bool = False
    _log_file: str = "log/app.log"
    _level: int = logging.DEBUG
    _logger: Optional[logging.Logger] = None

    @staticmethod
    def get_temp_path() -> str:
        """
        Возвращает путь к файлу app.log в системной временной папке.
        Использует переменные окружения TMP, TEMP, TMPDIR.
        Если не найдены — использует:
            - '/tmp' на Unix-системах
            - 'AppData\\Local\\Temp' на Windows
        """
        tmp_dir = '/tmp' if os.name != 'nt' else os.path.expanduser('~/AppData/Local/Temp')
        
        return tmp_dir

    @classmethod
    def _ensure_initialized(cls) -> None:
        """
        Гарантирует, что логгер инициализирован ровно один раз.

        Создаёт директорию для логов, настраивает форматтер и файловый обработчик,
        а также отключает распространение логов выше по иерархии (чтобы избежать дублирования).

        :raises OSError: Если не удаётся создать директорию для логов.
        """
        if cls._initialized:
            return

        cls._log_file = os.path.abspath(cls._log_file)

        log_dir = os.path.dirname(cls._log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(name)s%(funcName)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # NonLockingFileHandler закрывает файл после каждой записи
        file_handler = NonLockingFileHandler(cls._log_file, encoding='utf-8', delay=True)
        file_handler.setLevel(cls._level)
        file_handler.setFormatter(formatter)

        cls._logger = logging.getLogger()
        if cls._logger.hasHandlers():
            cls._logger.handlers.clear()
        cls._logger.setLevel(cls._level)
        cls._logger.addHandler(file_handler)
        cls._logger.propagate = False  # избегаем дублирования

        cls._initialized = True


    @classmethod
    def configure(cls, log_file: str = "app.log", level: int = logging.INFO) -> None:
        """
        Настраивает параметры логирования до первого использования.

        Сбрасывает флаг инициализации, чтобы при следующем вызове логирования
        применить новые настройки.

        :param log_file: Абсолютный или относительный путь к файлу лога. Будет преобразован в абсолютный путь.
        :param level: Уровень логирования (например, `logging.DEBUG`, `logging.INFO`).
        :raises ValueError: Если `log_file` — пустая строка или не строка.
        :raises TypeError: Если `level` не является целым числом.
        """
        if not isinstance(log_file, str) or not log_file.strip():
            raise ValueError("log_file must be a non-empty string.")
        if not isinstance(level, int):
            raise TypeError("level must be an integer.")
        cls._log_file = os.path.abspath(log_file)
        cls._level = level
        cls._initialized = False  # сброс для переинициализации

    @classmethod
    def init(cls, script_name: str) -> None:
        """
        Инициализирует логгер и записывает заголовок в начало лог-файла.

        Заголовок содержит имя скрипта и текущее время запуска.
        Если файл уже существует — он очищается.

        :param script_name: Название скрипта для отображения в логе.
        :raises ValueError: Если script_name — пустая строка.
        :raises OSError: Если не удаётся записать в файл.
        """
        if not script_name or not isinstance(script_name, str):
            raise ValueError("script_name must be a non-empty string.")

        # Гарантируем, что путь инициализирован
        cls._ensure_initialized()

        import datetime
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = (
            f"{'='*50}\n"
            f"СКРИПТ: {script_name}\n"
            f"ЗАПУСК: {timestamp}\n"
            f"{'='*50}\n"
        )

        # Закрываем обработчики, чтобы можно было перезаписать файл
        if cls._logger is not None:
            for handler in cls._logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
            cls._logger.handlers.clear()
        cls._initialized = False  # Перезапустим инициализацию позже

        # Записываем заголовок в файл
        log_dir = os.path.dirname(cls._log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        with open(cls._log_file, 'w', encoding='utf-8') as f:
            f.write(header)

        # Перезапускаем инициализацию, чтобы восстановить обработчики
        cls._ensure_initialized()

    @classmethod
    def separator(cls, sep:str='-'):
        cls._ensure_initialized()
        with open(cls._log_file, 'a', encoding='utf-8') as f:
            f.write(f'{sep*80}\n')

    @classmethod
    def _get_logger(cls, name: str) -> logging.Logger:
        """
        Возвращает дочерний логгер с заданным именем.

        Гарантирует инициализацию основного логгера при необходимости.

        :param name: Имя дочернего логгера (отображается в поле `%(name)s`).
        :return: Экземпляр `logging.Logger`.
        """
        cls._ensure_initialized()
        return cls._logger.getChild(name)  # создаёт дочерний логгер   

    @classmethod
    def debug(cls, message:str = '', name:str='') -> None:
        """
        Записывает сообщение уровня INFO.

        :param name: Имя подсистемы или модуля (отображается в логе).
        :param message: Текст сообщения.
        """
        
        cls._get_logger(name).debug(message, stacklevel=2)

    @classmethod
    def info(cls, message:str = '', name:str='') -> None:
        """
        Записывает сообщение уровня WARNING.

        :param name: Имя подсистемы или модуля (отображается в логе).
        :param message: Текст сообщения.
        """
        cls._ensure_initialized()
        cls._get_logger(name).info(message, stacklevel=2)

    @classmethod
    def warning(cls, message:str = '', name:str='') -> None:
        """
        Записывает сообщение уровня WARNING.

        :param name: Имя подсистемы или модуля (отображается в логе).
        :param message: Текст сообщения.
        """
        cls._ensure_initialized()
        cls._get_logger(name).warning(message, stacklevel=2)

    @classmethod
    def error(cls, message:str = '', name:str='') -> None:
        """
        Записывает сообщение уровня ERROR.

        :param name: Имя подсистемы или модуля (отображается в логе).
        :param message: Текст сообщения.
        """
        cls._ensure_initialized()
        cls._get_logger(name).error(message, stacklevel=2)

    @classmethod
    def critical(cls, message:str = '', name:str='') -> None:
        """
        Записывает сообщение уровня CRITICAL.

        :param name: Имя подсистемы или модуля (отображается в логе).
        :param message: Текст сообщения.
        """
        cls._ensure_initialized()
        cls._get_logger(name).critical(message, stacklevel=2)

    @classmethod
    def path(cls):
        return cls._log_file
    
    @classmethod
    def data(cls, data:list|tuple|dict, label:str='', name:str='data.', max_items=20):
        """
        Логировать структуру данных для отладки.

        :param name: Имя модуля
        :param label: Описание данных
        :param data: Данные (dict, list, или любой объект)
        :param max_items: Максимум элементов для вывода
        """
        cls._ensure_initialized()
        cls._get_logger(name).debug(msg=f"ДАННЫЕ [{label}]:", stacklevel=2)

        if isinstance(data, dict):
            cls._get_logger(name).debug(msg=f"Тип: dict, Кол-во: {len(data)}", stacklevel=2)
            for i, (k, v) in enumerate(data.items()):
                if i >= max_items:
                    cls._get_logger(name).debug(msg=f"... и ещё {len(data) - max_items}", stacklevel=2)
                    break
                v_str = str(v)
                if len(v_str) > 50:
                    v_str = v_str[:50] + "..."
                cls._get_logger(name).debug(msg=f"   [{k}] = {v_str}", stacklevel=2)

        elif isinstance(data, (list, tuple)):
            cls._get_logger(name).debug(msg=f"Тип: {type(data).__name__}, Кол-во: {len(data)}", stacklevel=2)
            for i, item in enumerate(data):
                if i >= max_items:
                    cls._get_logger(name).debug(msg=f"... и ещё {len(data) - max_items}", stacklevel=2)
                    break
                item_str = str(item)
                if len(item_str) > 50:
                    item_str = item_str[:50] + "..."
                cls._get_logger(name).debug(msg=f"   [{i}] {item_str}", stacklevel=2)

        else:
            cls._get_logger(name).debug(msg=f"Тип: {type(data).__name__}", stacklevel=2)
            cls._get_logger(name).debug(msg=f"  Значение: {data}", stacklevel=2)

if __name__ == '__main__':
    def run():
        Logger.info('as', "Тест логирования")
    run()