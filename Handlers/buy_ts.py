import asyncio

import aiohttp
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandObject
from aiogram.types import Message, CallbackQuery
from tonsdk.utils import *
from tonsdk.boc import *
from aiogram.exceptions import TelegramBadRequest
import time

from languages import messages
from TON_Handlers.connector import get_connector
import keyboards as kb
from config_reader import config
from states import BuyTSStates
from Handlers.main_menu import connect_wallet, start


router = Router()


@router.callback_query(F.data=="buy_ts")
async def buy_ts(call: CallbackQuery, state: FSMContext):
    msg = await call.message.edit_text(text=messages["buy_ts_amount"], reply_markup=kb.back_kb())
    await state.set_state(BuyTSStates.AmountInput)
    await state.update_data(message=msg)


@router.message(BuyTSStates.AmountInput)
async def buy_ts_amount(message: Message, state: FSMContext):
    await message.delete()
    msg = (await state.get_data())["message"]
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        try:
            await msg.edit_text(messages["buy_ts_amount_error"], reply_markup=kb.back_kb())
        except TelegramBadRequest:
            pass
        return
    msg = await msg.edit_text(messages["buy_ts_approve"].format(amount), reply_markup=kb.yes_no_kb())
    await state.set_state(BuyTSStates.Approve)
    await state.update_data(amount=amount)
    await state.update_data(message=msg)


@router.callback_query(BuyTSStates.Approve, F.data=="yes")
async def buy_ts_approve(call: CallbackQuery, state: FSMContext):
    amount = float((await state.get_data())["amount"])
    msg = (await state.get_data())["message"]

    transaction = {
        'valid_until': int(time.time()) + 300,
        'messages': [
            {
                'address': config.ts_jetton_minter_address.get_secret_value(),
                'amount': f'{int(amount * 1e9 / 4) + 100000000}',
                'payload': bytes_to_b64str(begin_cell().store_uint(0x785c33da, 32).store_uint(1, 64).end_cell().to_boc())
            },
        ]
    }
    
    connector = get_connector(call.message.chat.id)
    if await connector.restore_connection():
        try:
            await msg.edit_text(messages['accept_trans'], reply_markup=kb.open_wallet_kb())
            trans = await connector.send_transaction(transaction)
            cell_tr = begin_cell().end_cell().one_from_boc(b64str_to_hex(trans['boc'])).bytes_hash().hex()

            await msg.edit_text(messages['pls_wait'])

            for _ in range(60):
                await asyncio.sleep(2)
                async with aiohttp.ClientSession() as session:
                    async with session.get(f'{config.tonapi_host.get_secret_value()}/v2/events/{cell_tr}') as response:
                        try:
                            if not (await response.json())['in_progress']:
                                break
                        except KeyError:
                            pass

        except Exception as e:
            print(e)
            await msg.edit_text(messages['something_went_wrong'])
            return

    else:
        await msg.delete()
        await connect_wallet(call.message, state)
        return
    
    await start(call.message, CommandObject("start"), state)