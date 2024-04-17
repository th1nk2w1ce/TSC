from pytonconnect import TonConnect

from config_reader import config
from DB.fast_db import TcStorage

Manifest_Url = config.manifest_url.get_secret_value()


def get_connector(chat_id: int):
    connector = TonConnect(Manifest_Url, storage=TcStorage(chat_id))
    connector.api_tokens = {"tonapi": config.tonapi_bridge_key}
    return connector
