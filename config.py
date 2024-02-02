import os


class Config(object):
    TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")

    APP_ID = int(os.environ.get("APP_ID", 18421930))

    API_HASH = os.environ.get("API_HASH", "9cf3a6feb6dfcc7c02c69eb2c286830e")
