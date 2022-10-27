import json


def config(filename: str = 'appsettings'):
    try:
        with open(f"{filename}.json", "r", encoding='utf-8') as settings:
            return json.load(settings)
    except FileNotFoundError as e:
        print("[ERROR] JSON configuration file was not found")
        exit()
