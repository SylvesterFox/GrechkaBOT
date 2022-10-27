from settings_bot import config
from main import client

if __name__ == "__main__":
    settings = config()
    client.run(settings["token_bot"])
