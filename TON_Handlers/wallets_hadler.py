import asyncio
import aiohttp
import time
from tonsdk.utils import *
from tonsdk.boc import *

from config_reader import config
from DB.db_requests import Storage


async def get_wallet_address(address, minter):
    url = f'https://tonapi.io/v2/blockchain/accounts/{minter}/methods/get_wallet_address?args={address}'
    try:
        async with aiohttp.ClientSession() as session:
            resp = await session.get(url=url, headers={'Authorization': f'Bearer {config.tonapi_key.get_secret_value()}'})
        response = (await resp.json())['decoded']['jetton_wallet_address']
        return response
    except Exception as e:
        print(f'Error: {e}')
        return None


async def deploy_wallets(address, user_id):
    sts_wallet_address = None
    ts_wallet_address = None
    for _ in range(120):
        await asyncio.sleep(1)
        if sts_wallet_address is None:
            sts_wallet_address = await get_wallet_address(address, config.sts_jetton_minter_address.get_secret_value())
        if ts_wallet_address is None:
            ts_wallet_address = await get_wallet_address(address, config.ts_jetton_minter_address.get_secret_value())
        if ts_wallet_address is not None and sts_wallet_address is not None:
            break

    if ts_wallet_address is None or sts_wallet_address is None:
        return None

    referer_address = (await Storage(user_id).get_user())[2]

    try:
        await asyncio.sleep(0.5)
        url = f'https://tonapi.io/v2/blockchain/accounts/{ts_wallet_address}/methods/get_extra_data'
        async with aiohttp.ClientSession() as session:
            resp = await session.get(url, headers={'Authorization': f'Bearer {config.tonapi_key.get_secret_value()}'})
        ts_referer = await resp.json()
        await asyncio.sleep(0.5)
        url = f'https://tonapi.io/v2/blockchain/accounts/{sts_wallet_address}/methods/get_extra_data'
        async with aiohttp.ClientSession() as session:
            resp = await session.get(url, headers={'Authorization': f'Bearer {config.tonapi_key.get_secret_value()}'})
        sts_referer = await resp.json()
    except Exception as e:
        return None

    transaction = {}
    if ('error' in ts_referer and ts_referer['error'] == 'rate limit: free tier') or ('error' in sts_referer and sts_referer['error'] == 'rate limit: free tier'):
        return None

    if ('error' in ts_referer and ts_referer['error'] == 'entity not found') and ('error' in sts_referer and sts_referer['error'] == 'entity not found'):
        transaction = {
            'valid_until': int(time.time()) + 300,
            'messages': [
                {
                    'address': config.sts_jetton_minter_address.get_secret_value(),
                    'amount': '500000000',
                    'payload': bytes_to_b64str(
                        begin_cell().store_uint(0x2fc0dce9, 32).store_uint(1, 64).store_uint(1, 1).store_ref(
                            begin_cell().store_uint(0x14dc5f3d, 32).store_uint(1, 64).store_address(
                                Address(referer_address)).end_cell()).end_cell().to_boc())
                },

                {
                    'address': config.ts_jetton_minter_address.get_secret_value(),
                    'amount': '500000000',
                    'payload': bytes_to_b64str(
                        begin_cell().store_uint(0x2fc0dce9, 32).store_uint(1, 64).store_uint(1, 1).store_ref(
                            begin_cell().store_uint(0x14dc5f3d, 32).store_uint(1, 64).store_address(
                                Address(referer_address)).end_cell()).end_cell().to_boc())
                },
            ]
        }
    elif ('error' in ts_referer and ts_referer['error'] == 'entity not found'):
        transaction = {
            'valid_until': int(time.time()) + 300,
            'messages': [
                {
                    'address': config.ts_jetton_minter_address.get_secret_value(),
                    'amount': '500000000',
                    'payload': bytes_to_b64str(
                        begin_cell().store_uint(0x2fc0dce9, 32).store_uint(1, 64).store_uint(1, 1).store_ref(
                            begin_cell().store_uint(0x14dc5f3d, 32).store_uint(1, 64).store_address(
                                Address(referer_address)).end_cell()).end_cell().to_boc())
                },
            ]
        }
    elif ('error' in sts_referer and sts_referer['error'] == 'entity not found'):
        transaction = {
            'valid_until': int(time.time()) + 300,
            'messages': [
                {
                    'address': config.sts_jetton_minter_address.get_secret_value(),
                    'amount': '500000000',
                    'payload': bytes_to_b64str(
                        begin_cell().store_uint(0x2fc0dce9, 32).store_uint(1, 64).store_uint(1, 1).store_ref(
                            begin_cell().store_uint(0x14dc5f3d, 32).store_uint(1, 64).store_address(
                                Address(referer_address)).end_cell()).end_cell().to_boc())
                },
            ]
        }
    return transaction


async def get_balance(address: str) -> float:
    url = f'https://tonapi.io/v2/blockchain/accounts/{address}/methods/get_wallet_data'
    try:
        async with aiohttp.ClientSession() as session:
            resp = await session.get(url, headers={'Authorization': f'Bearer {config.tonapi_key.get_secret_value()}'})
        balance = float((await resp.json())['decoded']['balance']) / 1e9
        return balance
    except Exception as e:
        print(f'Error: {e}')
        return 0


async def get_staked_balance(address: str) -> tuple[float, float]:
    try:
        url = f'https://tonapi.io/v2/blockchain/accounts/{address}/methods/get_extra_data'
        async with aiohttp.ClientSession() as session:
            resp = await session.get(url, headers={'Authorization': f'Bearer {config.tonapi_key.get_secret_value()}'})
        response = await resp.json()
        return float(int(response['stack'][0]['num'], 16)), float(int(response['stack'][3]['num'], 16))
    except Exception as e:
        print(f'Error: {e}')
        return 0, 0
