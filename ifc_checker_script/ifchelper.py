import ifcopenshell
import ifctester
import os
import ifctester.reporter


class Ifc_help:
    """
    Класс содержит методы для работы с ifc
    """

    def __init__(self):
        pass

    @staticmethod
    def check_ifc_file(file_path, ids_path_file, report_path_folder):
        """
        Функция проверяет файл ifc по ids и формирует отчет
        """
        if file_path.endswith('.ifc'):
            ifc_file = ifcopenshell.open(file_path)  # Открытие ifc файла
            ifc_file_name = os.path.basename(file_path)  # Получение имени файла
            ids_file_path = ids_path_file
            test_ids = ifctester.ids.open(ids_file_path)  # Открытие файла ids
            test_ids.validate(ifc_file)  # Проверка файла ifc
            reporter_obj = ifctester.reporter.Html(test_ids)  # Создание отчета
            reporter_obj.report()
            reporter_obj.to_file(f'{report_path_folder}/{ifc_file_name.replace('.ifc', '')}.html')  # Запись отчета в файл

    @staticmethod
    def get_property_by_propertySet(ifc_file, ifc_id):
        """
        Функция для вывода наборов свойств и свойств в виде:
        - PropertySet
        ------ prop.Name: prop.NominalValue
        """
        ifc_entitie = ifc_file.by_guid(ifc_id)
        # обработка элемента
        for rel in ifc_entitie.IsDefinedBy:  # Набор связей с определениями наборов
            # свойств, прикрепленных к данному объекту
            if rel.is_a("IfcRelDefinesByProperties"):  # IfcRelDefinesByProperties
                # определяет отношения между определениями наборов свойств и объектами
                prop_set = rel.RelatingPropertyDefinition  # Ссылка на определение
                # набора свойств для этого объекта
                if prop_set.is_a("IfcPropertySet"):  # IfcPropertySet - это контейнер,
                    # который содержит свойства в дереве свойств
                    print('-', f'"{prop_set.Name}"')  # Вывод имени набора свойств
                    for prop in prop_set.HasProperties:
                        print('------', f'"{prop.Name}: {prop.NominalValue}"')
                        # Вывод имен и значений свойств для всех свойств в наборе

        # Обработка Property Sets из типа элемента (если есть)
        if hasattr(ifc_entitie, "IsTypedBy") and ifc_entitie.IsTypedBy:  # Обработка типа
            for type_rel in ifc_entitie.IsTypedBy:
                type_entity = type_rel.RelatingType
                if hasattr(type_entity, "HasPropertySets") and type_entity.HasPropertySets:
                    for prop_set in type_entity.HasPropertySets:
                        if prop_set.is_a("IfcPropertySet"):
                            print('-', f'"{prop_set.Name}" (Тип ifc)')
                            for prop in prop_set.HasProperties:
                                print('------', f'"{prop.Name}: {prop.NominalValue}"')

    @staticmethod
    def get_ifc_project_info(ifc_file):
        """
        Функция для получения информации о проекте
        """
        ifc_project_by_type = ifc_file.by_type('IfcProject')[0]
        proj_info = ifc_project_by_type.get_info()
        print('\n', str(proj_info), '\n')


if __name__ == '__main__':
    # Проверка работы функции
    ifc_file_path = r'c:\Users\...\Здание_1.ifc'
    ids_path_file = r'c:\Users\...\test.ids'
    report_path_folder = r'c:\Users\...\reports'
    Ifc_help.check_ifc_file(ifc_file_path, ids_path_file, report_path_folder)

    file_path = r'c:\Users\...\Здание_1.ifc'
    ifc_file = ifcopenshell.open(file_path)
    ifc_id = '22X3PS23z9Xwf8iH$NMQN3'
    Ifc_help.get_property_by_propertySet(ifc_file, ifc_id)

    Ifc_help.get_ifc_project_info(ifc_file)
