import qrcode
import asyncio
from io import BytesIO
from aiogram import Router, Bot, F
from aiogram.client.session import aiohttp
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.utils.deep_linking import create_start_link, decode_payload
from tonsdk.utils import *
from tonsdk.boc import *
from datetime import datetime

from languages import messages
from DB.db_requests import Storage, get_first_lvl_referrals
from TON_Handlers.connector import get_connector
import keyboards as kb
from config_reader import config
import TON_Handlers.wallets_hadler as TH
import Handlers.utils as util

router = Router()


@router.message(Command("start"))
async def start(message: Message, command: CommandObject, state: FSMContext):
    await state.clear()
    if message.from_user.id != message.bot.id:
        msg = await message.answer(messages["pls_wait"])
    else:
        try:
            msg = await message.edit_text(messages["pls_wait"])
        except Exception as e:
            if 'message to edit not found' in str(e):
                msg = await message.answer(messages["pls_wait"])
            else:
                msg = message

    # register new user if not exists
    if not await Storage(message.chat.id).get_user():
        # get referrer id
        args = command.args
        if args is not None:
            try:
                payload = int(decode_payload(args))
                if payload == message.chat.id:
                    await msg.edit_text(text=messages["ref_link_error"])
                    return
            except: 
                await msg.edit_text(text=messages["ref_link_error"])
                return
        else:
            await msg.edit_text(text=messages["register_ref_error"])
            return

        # check if referrer is logged in with wallet
        connector_referrer = get_connector(payload)
        if not await connector_referrer.restore_connection():
            await msg.edit_text(text=messages["ref_link_error"])
            return

        referrer_address = connector_referrer.account.address

        await Storage(message.chat.id).add_user(payload, referrer_address)

        # update users referrer number
        user = message.chat.id
        for _ in range(12):
            referrer = (await Storage(user).get_user())[0]
            if referrer == 0 or referrer == user:
                break
            await Storage(referrer).update_referrals()
            user = referrer

    # check if user is connected to wallet
    connector = get_connector(message.chat.id)
    if not await connector.restore_connection():
        await msg.delete()
        await connect_wallet(message, state)
        return
    
    # check if user is subscribed to channel
    if not await check_user_subscription(message.chat.id, message.bot, True):
        await msg.delete()
        return

    await connector.restore_connection()
    transaction = await TH.deploy_wallets(connector.account.address, message.chat.id)

    if transaction is None:
        await msg.edit_text(text=messages["something_went_wrong"])
        return
    if transaction:
        try:
            await msg.edit_text(text=messages['accept_trans'], reply_markup=kb.open_wallet_kb())
            trans = await connector.send_transaction(transaction)
            cell_tr = begin_cell().end_cell().one_from_boc(b64str_to_hex(trans['boc'])).bytes_hash().hex()
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
            await msg.edit_text(text=messages["something_went_wrong"])
            print(f'Error: {e}')
    else:
        await personal_account(msg, state)


@router.callback_query(F.data.in_({"start", "no"}))
async def refresh(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await start(call.message, CommandObject("start"), state)


async def personal_account(message: Message, state: FSMContext):
    if not await Storage(message.chat.id).get_user():
        return

    user = await Storage(message.chat.id).get_user()
    all_referals = user[1]
    firts_lvl_referals = await get_first_lvl_referrals(message.chat.id)
    link = await create_start_link(message.bot, payload=message.chat.id, encode=True)

    connector = get_connector(message.chat.id)
    await connector.restore_connection()

    ts_wallet_address = await TH.get_wallet_address(connector.account.address, config.ts_jetton_minter_address.get_secret_value())
    sts_wallet_address = await TH.get_wallet_address(connector.account.address, config.sts_jetton_minter_address.get_secret_value())

    ts = ''
    sts = ''
    balance_stacked = ''
    first_lvl_staked = ''
    last_activity = 0

    for _ in range(120):
        if ts == '':
            ts = await TH.get_balance(ts_wallet_address)
        if sts == '':
            sts = await TH.get_balance(sts_wallet_address)
        if balance_stacked == '':
            balance_stacked, first_lvl_staked, last_activity = await TH.get_staked_balance(sts_wallet_address)
        if ts != '' and sts != '':
            break
        await asyncio.sleep(1)

    qualification = util.get_qualification(all_referals, balance_stacked, first_lvl_staked)

    if ts == '' or sts == '':
        await message.edit_text(messages["something_went_wrong"])
        return

    referer = user[0]

    if referer is None:
        referer = 'никто'
    else:
        try:
            referer_name = (await message.bot.get_chat(referer)).first_name
        except:
            referer_name = 'No name'
        referer = f'<a href="tg://user?id={referer}">{referer_name}</a>'

    dtime = int(datetime.now().timestamp()) - last_activity
    reward_staked = balance_stacked * dtime * 6018518518518519 / 100000000000000000000000

    if balance_stacked == 0:
        reward_staked = 0.0

    await message.edit_text(messages['main_menu'].format(firts_lvl_referals, all_referals, referer, qualification, sts, (balance_stacked / 1e9), reward_staked, ((first_lvl_staked - balance_stacked) / 1e9), ts, link), reply_markup=kb.main_menu_kb())


@router.message(Command("disconnect_wallet"))
async def disconect_wallet(message: Message):
    if not await Storage(message.chat.id).get_user():
        return
    
    connector = get_connector(message.chat.id)

    if not await connector.restore_connection():
        await message.answer(text=messages["wallet_connected"])
        return

    await connector.disconnect()

    await message.answer(text=messages["wallet_disconnected"])


@router.message(Command("connect_wallet"))
async def connect_wallet(message: Message, state: FSMContext):
    if not await Storage(message.chat.id).get_user():
        return
    
    connector = get_connector(message.chat.id)

    if await connector.restore_connection():
        await message.answer(text=messages["wallet_connected"])
        return
    
    wallet = connector.get_wallets()[1]

    generated_url = await connector.connect(wallet)

    img = qrcode.make(generated_url)
    stream = BytesIO()
    img.save(stream)
    file = BufferedInputFile(file=stream.getvalue(), filename='qrcode')

    msg = await message.answer_photo(photo=file,
                                     caption=messages['connect_wallet_time'],
                                     reply_markup=kb.connect_wallet_kb(generated_url))

    wallet_address = None

    for _ in range(1, 300):
        await asyncio.sleep(1)
        if connector.connected:
            if connector.account.address:
                wallet_address = connector.account.address
            break
    
    await msg.delete()

    if wallet_address is None:
        await message.answer(text=messages["connect_wallet_error"])
        return
    else:
        await start(message, CommandObject("start"), state)


async def check_user_subscription(user_id: int, bot: Bot, send: bool):
    user_channel_status = await bot.get_chat_member(chat_id=int(config.group_id.get_secret_value()), user_id=user_id)
    if user_channel_status.status == 'left':
        if send:
            await bot.send_message(chat_id=user_id, text=messages["subscribe_on_channel"], disable_web_page_preview=True, reply_markup=kb.check_subs_kb())
        return False
    return True


@router.callback_query(F.data=="check_subs")
async def check_subs(call: CallbackQuery, state: FSMContext):
    if not await check_user_subscription(call.message.chat.id, call.bot, False):
        await call.answer(text=messages["subscription_error"], show_alert=True)
        return

    await call.message.delete()
    await start(call.message, CommandObject("start"), state)
