from settings_bot import config
from main import client
import logging


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s][%(name)s] - %(message)s",
                        datefmt='%d-%b-%y %H:%M:%S')

    settings = config()
    client.run(settings["token_bot"])
