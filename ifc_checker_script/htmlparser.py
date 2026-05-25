import os
from collections import OrderedDict
from bs4 import BeautifulSoup


def _extract_summary_stats(soup: BeautifulSoup) -> tuple[str, str]:
    """
    Извлекает процент и текст Summary из HTML-отчета ifctester.
    Восстановлена надежная логика поиска, устойчивая к пробелам и структуре DOM.
    """
    percent_value = ''
    container_div = soup.find('div', {'class': 'container'})
    if container_div is not None:
        percent_div = container_div.find('div', class_='percent')
        if percent_div is not None:
            percent_value = percent_div.get_text(strip=True)

    summary_text = ''
    summary_h2 = None
    # Надежный поиск заголовка Summary (устойчив к пробелам и вложенным тегам)
    for h2_tag in soup.find_all('h2'):
        if h2_tag.get_text(strip=True) == 'Summary':
            summary_h2 = h2_tag
            break

    if summary_h2 is not None:
        summary_container = summary_h2.find_next_sibling('div', {'class': 'container'})
        if summary_container is not None:
            summary_paragraph = summary_container.find_next_sibling('p')
            if summary_paragraph is not None:
                summary_text = summary_paragraph.get_text(' ', strip=True)

    return summary_text, percent_value


def _extract_report_data_from_meta(meta: dict, output_dir: str) -> dict:
    """Формирует строку сводного отчёта из готовых метаданных."""
    soup = Parser_html.parse_html(meta["html_path"])
    summary_text, percent_value = _extract_summary_stats(soup)
    
    return {
        'model_name': meta['ifc_name'],
        'ids_name': meta['ids_name'],
        'link_path': meta['relative_path'],
        'summary_text': summary_text,
        'percent_value': percent_value,
    }


def _split_summary_items(summary_text):
    labels = ['Specifications passed:', 'Requirements passed:', 'Checks passed:']
    positions = []
    for label in labels:
        position = summary_text.find(label)
        if position != -1:
            positions.append((position, label))

    if not positions:
        return [summary_text] if summary_text else []

    positions.sort(key=lambda item: item[0])
    parts = []
    for index, (position, _) in enumerate(positions):
        next_position = positions[index + 1][0] if index + 1 < len(positions) else len(summary_text)
        parts.append(summary_text[position:next_position].strip())
    return parts


def _build_summary_badges(consolidated_soup, summary_text):
    badges_container = consolidated_soup.new_tag('div', attrs={'class': 'summary-badges'})
    for item_text in _split_summary_items(summary_text):
        badge_tag = consolidated_soup.new_tag('span', attrs={'class': 'summary-badge'})
        badge_tag.string = item_text
        badges_container.append(badge_tag)
    return badges_container


def _extract_percent_number(percent_value):
    normalized_value = percent_value.replace('%', '').strip()
    if not normalized_value.isdigit():
        return 0
    return max(0, min(100, int(normalized_value)))


def _get_percent_gradient(percent_number):
    if percent_number <= 0:
        return 'linear-gradient(90deg, hsl(0, 80%, 50%), hsl(0, 80%, 50%))'

    end_hue = int(percent_number * 1.2)
    return (
        'linear-gradient('
        f'90deg, hsl(0, 80%, 50%) 0%, hsl({end_hue}, 80%, 50%) 100%'
        ')'
    )


def _build_percent_cell(consolidated_soup, percent_value):
    percent_number = _extract_percent_number(percent_value)
    fill_gradient = _get_percent_gradient(percent_number)
    percent_wrapper = consolidated_soup.new_tag('div', attrs={'class': 'percent-cell'})
    percent_label = consolidated_soup.new_tag('div', attrs={'class': 'percent-label'})
    percent_label.string = percent_value

    percent_bar = consolidated_soup.new_tag('div', attrs={'class': 'percent-bar'})
    percent_fill = consolidated_soup.new_tag(
        'div',
        attrs={
            'class': 'percent-bar-fill',
            'style': f'width: {percent_number}%; background: {fill_gradient};',
        },
    )
    percent_bar.append(percent_fill)
    percent_wrapper.append(percent_label)
    percent_wrapper.append(percent_bar)
    return percent_wrapper


def _build_consolidated_table(consolidated_soup, table_rows):
    table_wrapper = consolidated_soup.new_tag('div', attrs={'class': 'summary-table-wrapper'})
    table_tag = consolidated_soup.new_tag('table', attrs={'class': 'summary-table'})
    thead_tag = consolidated_soup.new_tag('thead')
    tbody_tag = consolidated_soup.new_tag('tbody')
    header_row = consolidated_soup.new_tag('tr')

    for title in ['Модель', 'IDS', 'Ссылка', 'Статистика', 'Процент заполнения']:
        th_tag = consolidated_soup.new_tag('th')
        th_tag.string = title
        header_row.append(th_tag)

    thead_tag.append(header_row)

    grouped_rows = OrderedDict()
    for row_data in table_rows:
        grouped_rows.setdefault(row_data['model_name'], []).append(row_data)

    for model_name, rows in grouped_rows.items():
        for row_index, row_data in enumerate(rows):
            tr_tag = consolidated_soup.new_tag('tr')

            if row_index == 0:
                model_td = consolidated_soup.new_tag('td')
                model_td['rowspan'] = str(len(rows))
                model_td['class'] = 'model-cell'
                model_td.string = model_name
                tr_tag.append(model_td)

            ids_td = consolidated_soup.new_tag('td')
            ids_td['class'] = 'ids-cell'
            ids_td.string = row_data['ids_name']
            tr_tag.append(ids_td)

            link_td = consolidated_soup.new_tag('td')
            link_td['class'] = 'link-cell'
            link_tag = consolidated_soup.new_tag('a', href=row_data['link_path'])
            link_tag.string = 'Открыть'
            link_td.append(link_tag)
            tr_tag.append(link_td)

            summary_td = consolidated_soup.new_tag('td')
            summary_td['class'] = 'summary-cell'
            summary_td.append(
                _build_summary_badges(consolidated_soup, row_data['summary_text'])
            )
            tr_tag.append(summary_td)

            percent_td = consolidated_soup.new_tag('td')
            percent_td['class'] = 'percent-column'
            percent_td.append(
                _build_percent_cell(consolidated_soup, row_data['percent_value'])
            )
            tr_tag.append(percent_td)

            tbody_tag.append(tr_tag)

    table_tag.append(thead_tag)
    table_tag.append(tbody_tag)
    table_wrapper.append(table_tag)
    return table_wrapper


class Parser_html:
    def __init__(self):
        pass

    @staticmethod
    def parse_html(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            return soup

    @staticmethod
    def save_html(soup, output_filename):
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(soup.prettify())

    @staticmethod
    def get_consolidated_html(
        report_metadata: list[dict],
        output_dir: str, 
        output_filename: str,
    ) -> None:
        consolidated_soup = BeautifulSoup('<html lang="ru">', 'html.parser')
        head_tag = BeautifulSoup().new_tag('head')
        meta_tag = BeautifulSoup().new_tag('meta', charset='UTF-8')
        title_tag = BeautifulSoup().new_tag('title')
        body_tag = BeautifulSoup().new_tag('body')
        h1_tag = BeautifulSoup().new_tag('h1')

        head_tag.append(meta_tag)
        head_tag.append(title_tag)
        consolidated_soup.append(head_tag)
        title_tag.string = 'Сводный отчет'
        summary_style = BeautifulSoup().new_tag('style')
        summary_style.string = """
body {
    font-family: Arial, sans-serif;
    padding: 24px 0 40px;
    background-color: #f7f7f7;
    color: #222;
}
h1 {
    text-align: center;
    margin-bottom: 24px;
}
.summary-table-wrapper {
    width: 80%;
    margin: 0 auto;
}
.summary-table {
    width: 100%;
    border-collapse: collapse;
    background-color: #ffffff;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}
.summary-table th,
.summary-table td {
    padding: 12px 14px;
    border: 1px solid #d9d9d9;
    vertical-align: middle;
    text-align: left;
}
.summary-table thead tr {
    background-color: #ececec;
}
.summary-table tbody tr:nth-child(even) {
    background-color: #fafafa;
}
.summary-table .model-cell {
    font-weight: bold;
    width: 22%;
}
.summary-table .ids-cell {
    width: 20%;
    white-space: nowrap;
}
.summary-table .link-cell {
    width: 8%;
    white-space: nowrap;
}
.summary-table .summary-cell {
    width: 34%;
}
.summary-table .percent-column {
    width: 16%;
}
.summary-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
}
.summary-badge {
    display: inline-block;
    padding: 4px 7px;
    border-radius: 7px;
    background-color: #f2f4f7;
    border: 1px solid #d8dee6;
    white-space: nowrap;
    font-size: 12px;
    line-height: 1.2;
}
.percent-cell {
    min-width: 110px;
}
.percent-label {
    margin-bottom: 5px;
    font-weight: bold;
    font-size: 16px;
}
.percent-bar {
    width: 100%;
    height: 8px;
    background-color: #e5e7eb;
    border-radius: 999px;
    overflow: hidden;
}
.percent-bar-fill {
    height: 100%;
    border-radius: 999px;
}
.summary-table a {
    color: #0a58ca;
    text-decoration: none;
}
.summary-table a:hover {
    text-decoration: underline;
}
.summary-footer {
    width: 80%;
    margin: 18px auto 0;
    text-align: right;
    color: #666;
}
.summary-footer a {
    color: #0a58ca;
    text-decoration: none;
}
.summary-footer a:hover {
    text-decoration: underline;
}
"""
        head_tag.append(summary_style)

        table_rows = []
        for meta in report_metadata:
            table_rows.append(_extract_report_data_from_meta(meta, output_dir))

        h1_tag.string = 'Сводный отчет'
        footer_tag = BeautifulSoup().new_tag('footer', attrs={'class': 'summary-footer'})
        footer_text = BeautifulSoup().new_tag('span')
        footer_text.string = 'Автор: '
        footer_link = BeautifulSoup().new_tag('a', href='https://github.com/i-savelev')
        footer_link.string = 'i-savelev'
        footer_tag.append(footer_text)
        footer_tag.append(footer_link)
        body_tag.append(h1_tag)
        body_tag.append(_build_consolidated_table(consolidated_soup, table_rows))
        body_tag.append(footer_tag)
        consolidated_soup.append(body_tag)

        output_file_path = f'{output_dir}/{output_filename}.html'
        Parser_html.save_html(consolidated_soup, output_file_path)

    @staticmethod
    def add_file_name_to_report(file_name, file_path):
        soup = Parser_html.parse_html(file_path)
        h2_tag = soup.new_tag('h2')
        h2_tag.string = file_name
        h1_tag = soup.find('h1')
        h1_tag.insert_after(h2_tag)
        Parser_html.save_html(soup, file_path)

    @staticmethod
    def delete_skipped_from_one_html(html_path):
        soup = Parser_html.parse_html(html_path)
        deleted_section_titles = []

        for section in soup.find_all('section'):
            skipped_item = section.find('span', class_='item skipped')
            if skipped_item is None:
                continue
            section_title = section.find('h2')
            deleted_section_titles.append(
                section_title.get_text(' ', strip=True) if section_title is not None else 'Без названия'
            )
            section.decompose()

        Parser_html.save_html(soup, html_path)
        return {
            'count': len(deleted_section_titles),
            'titles': deleted_section_titles,
        }

    @staticmethod
    def delete_skipped(folder_path):
        deleted_items_by_file = {}
        for root, _, files in os.walk(folder_path):
            for file_name in files:
                if not file_name.endswith('.html'):
                    continue
                path_file = os.path.join(root, file_name)
                deleted_items_by_file[path_file] = (
                    Parser_html.delete_skipped_from_one_html(path_file)
                )
        return deleted_items_by_file


def delete_skipped_from_one_html(html_path):
    return Parser_html.delete_skipped_from_one_html(html_path)['count']


def delete_skipped(folder_path):
    return {
        file_path: deleted_data['count']
        for file_path, deleted_data in Parser_html.delete_skipped(folder_path).items()
    }


if __name__ == '__main__':
    # Для ручного тестирования оставлен заглушечный вызов. 
    # Актуальная сигнатура теперь принимает list[dict], а не str.
    pass