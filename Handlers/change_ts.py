import asyncio

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandObject
from aiogram.types import Message, CallbackQuery
from tonsdk.utils import *
from tonsdk.boc import *
from aiogram.exceptions import TelegramBadRequest
import aiohttp
import time

from languages import messages
from TON_Handlers.connector import get_connector
import keyboards as kb
from config_reader import config
from states import SellTSStates
from TON_Handlers.wallets_hadler import get_wallet_address
from Handlers.main_menu import connect_wallet, start


router = Router()


@router.callback_query(F.data=="sell_ts")
async def sell_ts(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(text=messages["pls_wait"])
    connector = get_connector(call.message.chat.id)
    if not await connector.restore_connection():
        await connect_wallet(call.message, state)
        return

    ts_wallet_address = await get_wallet_address(connector.account.address, config.ts_jetton_minter_address.get_secret_value()) 

    value = ''
    while value == '':
        try:
            url = f'{config.tonapi_host.get_secret_value()}/v2/blockchain/accounts/{ts_wallet_address}/methods/get_wallet_data'
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={'Authorization': f'Bearer {config.tonapi_key.get_secret_value()}'})as response:
                    value = float((await response.json())['decoded']['balance'])
        except Exception as e:
            print(e)
            pass

    msg = await call.message.edit_text(text=messages["sell_ts_amount"].format(round(value/1e9, 4)), reply_markup=kb.back_kb())
    await state.set_state(SellTSStates.AmountInput)
    await state.update_data(message=msg)
    await state.update_data(balance=float(value)/1e9)
    await state.update_data(ts_wallet_address=ts_wallet_address)


@router.message(SellTSStates.AmountInput)
async def sell_ts_amount(message: Message, state: FSMContext):
    await message.delete()
    msg = (await state.get_data())["message"]
    balance = (await state.get_data())["balance"]
    ts_wallet_address = (await state.get_data())["ts_wallet_address"]
    try:
        amount = float(message.text)
        if amount <= 0 or amount > balance:
            raise ValueError
    except ValueError:
        try:
            await msg.edit_text(messages["sell_ts_amount_error"].format(round(balance, 4)), reply_markup=kb.back_kb())
        except TelegramBadRequest:
            pass
        return
    msg = await msg.edit_text(messages["sell_ts_approve"].format(amount), reply_markup=kb.yes_no_kb())
    await state.set_state(SellTSStates.Approve)
    await state.update_data(amount=amount)
    await state.update_data(message=msg)
    await state.update_data(ts_wallet_address=ts_wallet_address)


@router.callback_query(SellTSStates.Approve, F.data=="yes")
async def sell_ts_approve(call: CallbackQuery, state: FSMContext):
    amount = float((await state.get_data())["amount"])
    msg = (await state.get_data())["message"]
    ts_wallet_address = (await state.get_data())["ts_wallet_address"]

    connector = get_connector(call.message.chat.id)
    if not await connector.restore_connection():
        await connect_wallet(call.message, state)
        return

    transaction = {
        'valid_until': int(time.time()) + 300,
        'messages': [
            {
                'address': ts_wallet_address,
                'amount': '500000000',
                'payload': bytes_to_b64str(begin_cell().store_uint(0x0f8a7ea5, 32).store_uint(1, 64).store_coins(int(amount * 1e9)).store_address(Address(config.sts_jetton_minter_address.get_secret_value())).store_address(Address(connector.account.address)).store_uint(0, 1).store_coins(400000000).store_uint(0, 1).end_cell().to_boc())
            },
        ]
    }

    try:
        await msg.edit_text(messages['accept_trans'], reply_markup=kb.open_wallet_kb())
        trans = await connector.send_transaction(transaction)
        cell_tr = begin_cell().end_cell().one_from_boc(b64str_to_hex(trans['boc'])).bytes_hash().hex()

        await msg.edit_text(messages['pls_wait'])
        print(cell_tr)
        for _ in range(60):
            await asyncio.sleep(2)
            async with aiohttp.ClientSession() as session:
                response = await session.get(f'{config.tonapi_host.get_secret_value()}/v2/events/{cell_tr}')
            try:
                if not (await response.json())['in_progress']:
                    break
            except KeyError:
                pass
    except Exception as e:
        print(e)
        await msg.edit_text(messages['something_went_wrong'])
        return
    
    await start(call.message, CommandObject("start"), state)
