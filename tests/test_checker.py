"""Тесты бизнес-логики проверки IFC по sample-данным проекта."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

from ifc_checker_script import (
    check_ifc,
    delete_skipped,
    delete_skipped_from_one_html,
    read_json_config,
)


class TestCheckerBusinessLogic(unittest.TestCase):
    """Проверяет основную бизнес-логику формирования отчетов по IFC."""

    @classmethod
    def setUpClass(cls) -> None:
        """Подготавливает общие пути к sample-данным и папке результатов.

        :returns: ``None``.
        """

        cls.repo_root = Path(__file__).resolve().parents[1]
        cls.samples_dir = cls.repo_root / "samples"
        cls.ifc_dir = cls.samples_dir / "ifc_models"
        cls.config_path = cls.samples_dir / "sample_config.json"
        cls.ids_files = [
            cls.samples_dir / "test_all.ids",
            cls.samples_dir / "test_AR.ids",
            cls.samples_dir / "test_KR.ids",
            cls.samples_dir / "test_IOS.ids",
        ]
        cls.output_root = cls.repo_root / ".output"
        cls.report_dir = cls.output_root / "test_reports"

    def setUp(self) -> None:
        """Очищает папку с результатами перед каждым тестом.

        :returns: ``None``.
        """

        if self.report_dir.exists():
            shutil.rmtree(self.report_dir)
        self.output_root.mkdir(exist_ok=True)

    def test_check_ifc_creates_expected_reports_from_samples(self) -> None:
        """Проверяет, что `check_ifc` формирует ожидаемый набор отчетов.

        Тест использует sample IFC, IDS и JSON-конфигурацию из репозитория,
        запускает полную проверку и валидирует итоговые артефакты в папке
        `.output/test_reports`.

        :returns: ``None``.
        """

        configuration = read_json_config(str(self.config_path))
        result = check_ifc(
            folder_path_ifc=str(self.ifc_dir),
            files_path_ids=[str(path) for path in self.ids_files],
            folder_path_report=str(self.report_dir),
            configuration=configuration,
        )

        expected_html_files = {
            self.report_dir / "AR" / "Здание_1_AR(test_all).html",
            self.report_dir / "AR" / "Здание_1_AR(test_AR).html",
            self.report_dir / "KR" / "Здание_2_KR(test_all).html",
            self.report_dir / "KR" / "Здание_2_KR(test_KR).html",
            self.report_dir / "IOS" / "Здание_3_IOS(test_all).html",
            self.report_dir / "IOS" / "Здание_3_IOS(test_IOS).html",
        }

        self.assertEqual(result["report_count"], 6)
        self.assertEqual(
            {Path(path) for path in result["html_files"]},
            expected_html_files,
        )
        self.assertTrue((self.report_dir / "Сводный отчет.html").exists())
        self.assertTrue((self.report_dir / "ifc_checker.log").exists())

        for html_file in expected_html_files:
            self.assertTrue(html_file.exists(), msg=f"Отсутствует отчет: {html_file}")

        self.assertEqual(
            Path(result["summary_report"]),
            self.report_dir / "Сводный отчет.html",
        )
        self.assertEqual(
            Path(result["log_path"]),
            self.report_dir / "ifc_checker.log",
        )

        summary_soup = BeautifulSoup(
            (self.report_dir / "Сводный отчет.html").read_text(encoding="utf-8"),
            "html.parser",
        )
        summary_table = summary_soup.find("table", class_="summary-table")
        self.assertIsNotNone(summary_table)

        headers = [
            header.get_text(" ", strip=True)
            for header in summary_table.find("thead").find_all("th")
        ]
        self.assertEqual(
            headers,
            ["Модель", "IDS", "Ссылка", "Статистика", "Процент заполнения"],
        )

        body_rows = summary_table.find("tbody").find_all("tr")
        self.assertEqual(len(body_rows), 6)

        model_cells = summary_table.find_all("td", class_="model-cell")
        self.assertEqual(len(model_cells), 3)
        self.assertTrue(all(cell.get("rowspan") == "2" for cell in model_cells))

        links = summary_table.find_all("a")
        self.assertEqual(len(links), 6)
        self.assertTrue(all(link.get_text(strip=True) == "Открыть" for link in links))

        badges = summary_table.find_all("span", class_="summary-badge")
        self.assertTrue(badges)

        percent_cells = summary_table.find_all("div", class_="percent-cell")
        self.assertEqual(len(percent_cells), 6)
        percent_fills = summary_table.find_all("div", class_="percent-bar-fill")
        self.assertEqual(len(percent_fills), 6)

        summary_text = summary_table.get_text(" ", strip=True)
        self.assertIn("Specifications passed:", summary_text)
        self.assertIn("Requirements passed:", summary_text)
        self.assertIn("Checks passed:", summary_text)

    def test_delete_skipped_from_one_html_removes_only_skipped_sections(self) -> None:
        """Проверяет удаление секций со статусом ``skipped`` из одного HTML.

        :returns: ``None``.
        """

        html_content = """
        <html>
            <body>
                <section>
                    <h2>Skipped section</h2>
                    <span class="item skipped">Skipped</span>
                </section>
                <section>
                    <h2>Passed section</h2>
                    <span class="item passed">Passed</span>
                </section>
            </body>
        </html>
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            html_path = Path(temp_dir) / "single_report.html"
            html_path.write_text(html_content, encoding="utf-8")

            deleted_sections_count = delete_skipped_from_one_html(str(html_path))
            updated_html = html_path.read_text(encoding="utf-8")

            self.assertEqual(deleted_sections_count, 1)
            self.assertNotIn("Skipped section", updated_html)
            self.assertIn("Passed section", updated_html)

    def test_delete_skipped_processes_all_html_files_in_folder(self) -> None:
        """Проверяет пакетную очистку HTML-файлов от секций ``skipped``.

        :returns: ``None``.
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            nested_dir = root_dir / "nested"
            nested_dir.mkdir()

            first_html_path = root_dir / "first.html"
            second_html_path = nested_dir / "second.html"

            first_html_path.write_text(
                """
                <html><body>
                    <section><span class="item skipped">Skipped</span></section>
                    <section><span class="item passed">Passed</span></section>
                </body></html>
                """,
                encoding="utf-8",
            )
            second_html_path.write_text(
                """
                <html><body>
                    <section><span class="item skipped">Skipped</span></section>
                </body></html>
                """,
                encoding="utf-8",
            )

            deleted_items_by_file = delete_skipped(str(root_dir))

            self.assertEqual(deleted_items_by_file[str(first_html_path)], 1)
            self.assertEqual(deleted_items_by_file[str(second_html_path)], 1)
            self.assertNotIn("item skipped", first_html_path.read_text(encoding="utf-8"))
            self.assertNotIn("item skipped", second_html_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
