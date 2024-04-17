from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    bot_token: SecretStr
    group_id: SecretStr
    tonapi_host: SecretStr
    tonapi_key: SecretStr
    tonapi_bridge_key: SecretStr
    manifest_url: SecretStr
    sts_jetton_minter_address: SecretStr
    ts_jetton_minter_address: SecretStr

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


config = Settings()
