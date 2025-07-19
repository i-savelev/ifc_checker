import json

def save_json_config_template(path_to_save):
    '''
    Сохранение шаблона конфигурации

    :path_to_save -- путь для сохранения файла json
    '''
    data = {
        "ids-ifc_mapping": 
        {
            "Имя ids 1": [
                "часть названия файла ifc",
                "часть названия файла ifc"
            ],
            "Имя ids 2": [
                "часть названия файла ifc",
                "часть названия файла ifc"
            ],
            "Имя ids 3": [
                "часть названия файла ifc",
                "часть названия файла ifc"
            ],
            "Имя ids 4": [
                "часть названия файла ifc",
                "часть названия файла ifc"
            ]
        }
    }
    with open(f'{path_to_save}.json', "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def read_json_config(config_path):
    '''
    получения словаря конфигурации из json

    :config_path -- путь к файлу конфигурации
    '''
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        mapping_dict = data.get("ids-ifc_mapping", {})
    return mapping_dict

def ifc_exist_in_ids_dict(ids_file, ifc_file, json_config):
    '''
    проверка:
    - содержится ли ids файл в конфиге
    - содержатся ли строки из конигурации названии файла ifc

    :ids_file -- название ids файла
    :ifc_file -- название ifc файла
    :json_config -- словарь конфигурации, полученный с помощью "read_json_config()"
    '''
    value = False
    if ids_file in json_config:
        if json_config[ids_file]:
            for word in json_config[ids_file]:
                if word in ifc_file:
                    value = True
                    break
        else: value = True
    return value

if __name__ == '__main__':
    pass