import os
from bs4 import BeautifulSoup


class Parser_html:
    """
    Класс содержит методы для формирвоания сводного отчета html
    """

    def __init__(self):
        pass

    @staticmethod
    def parse_html(file_path):
        """
        Функция для получения файла html c помощью библиотеки BeautifulSoup

        :file_path -- путь к файлу html
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            return soup

    @staticmethod
    def save_html(soup, output_filename):
        """
        Функция для сохранения файла html

        :soup -- объект BeautifulSoup
        :output_filename -- папка для сохранения
        """
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(soup.prettify())

    @staticmethod
    def get_consolidated_html(input_filenames, output_dir, output_filename):
        """
        Функция для формирования сводного html документа из отчетов ids

        :input_filenames -- список путей к файлам html
        :output_dir -- папка для сохранения отчета
        :output_filename -- имя файла отчета
        """
        consolidated_soup = BeautifulSoup('<html lang="ru">', 'html.parser')
        head_tag = BeautifulSoup().new_tag('head')
        meta_tag = BeautifulSoup().new_tag('meta', charset='UTF-8')
        title_tag = BeautifulSoup().new_tag('title')
        body_tag = BeautifulSoup().new_tag('body')

        # Добавление тегов в документ
        head_tag.append(meta_tag)
        head_tag.append(title_tag)
        consolidated_soup.append(head_tag)
        title_tag.string = 'Сводный отчет'
        processed_styles = set()  # Множество для записи настроек стиля

        for input_filename in input_filenames:  # Цикл для обработки файлов отчетов
            soup = Parser_html.parse_html(input_filename)  # Получение файла html
            for style in soup.find_all('style'):  # Цикл для обработки элементов в теге <style>
                style_content = style.get_text(strip=True)
                if style_content not in processed_styles:
                    new_style = BeautifulSoup().new_tag('style')
                    new_style.string = style.get_text()
                    head_tag.append(new_style)
                    processed_styles.add(style_content)

            # Получение содержимого тегов <h2> <div> <p>
            h2_tag = soup.find('h2')
            container_div = soup.find('div', {'class': 'container'})
            p_tag = container_div.find_next('p')  # Тег <p>, который расположен после <div>

            # Доабавление имени файла отчета
            html_rel_file_path = os.path.relpath(input_filename, output_dir)

            # Создание ссылки на файл отчета
            link_tag = soup.new_tag('a')
            link_tag['href'] = html_rel_file_path
            link_tag.string = str(html_rel_file_path).replace('.html', '')
            h2_tag.clear()
            h2_tag.append(link_tag)

            # Горизонтальная черта для разделения отчетов
            hr_tag = soup.new_tag("hr")

            # Заполнение body данными из отчета
            body_tag.append(h2_tag)
            body_tag.append(container_div)
            if p_tag: body_tag.append(p_tag)
            body_tag.append(hr_tag)

        consolidated_soup.append(body_tag)

        # Сохранение сводного отчета
        output_file_path = f'{output_dir}/{output_filename}.html'
        Parser_html.save_html(consolidated_soup, output_file_path)

    def add_file_name_to_report(file_name, file_path):
        '''
        Добавления названия  файла ifc в заголовок html страницы

        :file_name -- имя файла ifc
        :file_path -- путь к файлу html
        '''
        soup = Parser_html.parse_html(file_path)
        h2_tag = soup.new_tag('h2')
        h2_tag.string = file_name
        h1_tag = soup.find('h1')
        h1_tag.insert_after(h2_tag)
        Parser_html.save_html(soup, file_path)


if __name__ == '__main__':
    # Проверка работы функции
    input_dir = r'c:\Users\...\reports'
    output_filename = 'Сводный отчет'
    Parser_html.get_consolidated_html(input_dir, output_filename)