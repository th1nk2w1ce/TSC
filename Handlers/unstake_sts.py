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
from states import UnstakeSTSStates
from TON_Handlers.wallets_hadler import get_wallet_address
from Handlers.main_menu import connect_wallet, start



router = Router()


@router.callback_query(F.data=="unstake_sts")
async def stake_sts(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(text=messages["pls_wait"])
    connector = get_connector(call.message.chat.id)
    if not await connector.restore_connection():
        await connect_wallet(call.message, state)
        return

    sts_wallet_address = await get_wallet_address(connector.account.address, config.sts_jetton_minter_address.get_secret_value())

    value = ''
    while value == '':
        try:
            url = f'https://tonapi.io/v2/blockchain/accounts/{sts_wallet_address}/methods/get_extra_data'
            async with aiohttp.ClientSession() as session:
                response = await session.get(url, headers={'Authorization': f'Bearer {config.tonapi_key.get_secret_value()}'})
            value = int((await response.json())['stack'][0]['num'], 16)
        except Exception as e:
            print(e)
            pass

    msg = await call.message.edit_text(messages['unstake_sts_amount'].format(value / 1e9), reply_markup=kb.back_kb())
    await state.set_state(UnstakeSTSStates.AmountInput)
    await state.update_data(message=msg)
    await state.update_data(balance=float(value) / 1e9)
    await state.update_data(sts_wallet_address=sts_wallet_address)


@router.message(UnstakeSTSStates.AmountInput)
async def stake_sts_amount(message: Message, state: FSMContext):
    await message.delete()
    msg = (await state.get_data())["message"]
    balance = (await state.get_data())["balance"]
    sts_wallet_address = (await state.get_data())["sts_wallet_address"]
    try:
        amount = float(message.text)
        if amount < 0 or amount > balance or 0 < balance - amount < 20:
            raise ValueError
    except ValueError:
        try:
            await msg.edit_text(messages["unstake_sts_amount_error"].format(balance), reply_markup=kb.back_kb())
        except TelegramBadRequest:
            pass
        return

    msg = await msg.edit_text(messages["stake_sts_approve"].format(amount), reply_markup=kb.yes_no_kb())
    await state.set_state(UnstakeSTSStates.Approve)
    await state.update_data(amount=amount)
    await state.update_data(message=msg)
    await state.update_data(sts_wallet_address=sts_wallet_address)


@router.callback_query(UnstakeSTSStates.Approve, F.data=="yes")
async def stake_sts_approve(call: CallbackQuery, state: FSMContext):
    amount = float((await state.get_data())["amount"])
    msg = (await state.get_data())["message"]
    sts_wallet_address = (await state.get_data())["sts_wallet_address"]

    connector = get_connector(call.message.chat.id)
    if not await connector.restore_connection():
        await connect_wallet(call.message, state)
        return

    transaction = {
        'valid_until': int(time.time()) + 300,
        'messages': [
            {
                'address': sts_wallet_address,
                'amount': '600000000',
                'payload': bytes_to_b64str(begin_cell().store_uint(0x48e9880f, 32).store_uint(1, 64).store_coins(int(amount * 1e9)).end_cell().to_boc())
            },
        ]
    }

    try:
        await msg.edit_text(messages['accept_trans'], reply_markup=kb.open_wallet_kb())
        await connector.send_transaction(transaction)
    except Exception as e:
        print(e)
        await msg.edit_text(messages['something_went_wrong'])
        return
    
    await start(call.message, CommandObject("start"), state)
