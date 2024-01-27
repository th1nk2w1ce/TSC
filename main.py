import qrcode
import os
import sqlite3
import random
import asyncio
import requests
import json
import time
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.markdown import link
from aiogram.types.input_file import InputFile
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from tonsdk.utils import *
from tonsdk.boc import *

from pytonconnect import TonConnect
from config import api_token, tonapi_key
import database

class States(StatesGroup):
    Sell_ts = State()
    Stake_sts = State()
    Unstake_sts = State()
    Buy_ts = State()

con = sqlite3.connect("DB.db", check_same_thread=False)
cur = con.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS "users" (
    "tg_id" INTEGER,
    "sts"   INTEGER DEFAULT (0),
    "flag"  BOOLEAN DEFAULT (false),
    "referer" INTEGER,
    "all_referals" INTEGER DEFAULT (0),
    "referer_address"	TEXT
)''')

cur.execute('''INSERT INTO users VALUES (
    1749027454,
    0,
    false,
    1749027454,
    0,
    "UQBKgXCNLPexWhs2L79kiARR1phGH1LwXxRbNsCFF9doczSI"
)''')

bot = Bot(token=api_token)
dp = Dispatcher(bot, storage=MemoryStorage())

Account = KeyboardButton('Личный кабинет👤')

PersonalAccount = ReplyKeyboardMarkup(resize_keyboard=True).add(Account)

check = InlineKeyboardMarkup(row_width=1)

checkButton = InlineKeyboardButton(text='Проверить подписку', callback_data='check')        

check.add(checkButton)

sts_jetton_minter_address = 'EQByOAMcF6dy-ITBQBkt8szOdsVaGJdvVJJ88sLBlmpZUSg6'
ts_jetton_minter_address = 'EQC13fWOjunJP2fsA1cG0ynUKVs0Nrf4wM4iBc7egsZM3Ayd'

async def get_wallet_address(address, minter):
    url = f'https://tonapi.io/v2/blockchain/accounts/{minter}/methods/get_wallet_address?args={address}'
    try:
        response = requests.get(url, headers={'Authorization': f'Bearer {tonapi_key}'}).json()['decoded']['jetton_wallet_address']
        return response
    except Exception as e:
        print(e)
        return None

@dp.message_handler(commands=['start'], state='*', chat_type=types.ChatType.PRIVATE)
async def start_command(message: types.Message):
    if not cur.execute(f"SELECT tg_id FROM users WHERE tg_id == {message.from_user.id}").fetchall():
        print(message.text)
        if len(message.text.split()) > 1:
            if int(message.text.split()[1]) != int(message.from_user.id) and cur.execute(f"SELECT tg_id FROM users WHERE tg_id == {message.text.split()[1]}").fetchall():
                try:
                    cur.execute(f"INSERT INTO users (tg_id) VALUES ({message.from_user.id})")
                    con.commit()
                    sts = cur.execute(f"SELECT sts FROM users WHERE tg_id == {message.text.split()[1]}").fetchall()[0][0]
                    cur.execute(f"UPDATE users SET referer = {message.text.split()[1]} WHERE tg_id = {message.from_user.id}")
                    cur.execute(f"UPDATE users SET sts = {sts + 0.2} WHERE tg_id = {message.text.split()[1]}")
                    con.commit()

                    storage_referer = database.Storage(str(cur.execute(f"SELECT referer FROM users WHERE tg_id == {message.from_user.id}").fetchall()[0][0]))

                    connector_referer = TonConnect(manifest_url='https://raw.githubusercontent.com/AndreyBur/Access_control_bot/master/pytonconnect-manifest.json', storage=storage_referer)
                    # Attempt to restore the existing connection, if any
                    is_connected = await connector_referer.restore_connection()

                    if not is_connected:
                        await message.answer("Что-то пошло не так...\nПопробуйте ещё раз позже")
                        return

                    referer_address = connector_referer.account.address

                    cur.execute(f'UPDATE users SET referer_address = "{referer_address}" WHERE tg_id = {message.from_user.id}')
                    con.commit()

                    user = message.from_user.id
                    depth = 1
                    while depth <= 12:
                        referer = cur.execute(f"SELECT referer FROM users WHERE tg_id == {user}").fetchall()[0][0]
                        if referer is None or referer == user:
                            break
                        all_referals = cur.execute(f"SELECT all_referals FROM users WHERE tg_id == {referer}").fetchall()[0][0]
                        cur.execute(f"UPDATE users SET all_referals = {all_referals + 1} WHERE tg_id = {referer}")
                        con.commit()
                        depth += 1
                        user = referer
                except Exception as e:
                    print(e)
                    return
            else:
                await message.answer("Не действительная ссылка")
                return
        else:
            await message.answer("Регистрация в боте возможна только по реферальной ссылке")
            return

    # Create a storage instance based on the user's ID
    storage = database.Storage(str(message.from_user.id))

    # Initialize a connection using the given manifest URL and storage
    connector = TonConnect(manifest_url='https://raw.githubusercontent.com/AndreyBur/Access_control_bot/master/pytonconnect-manifest.json', storage=storage)
    # Attempt to restore the existing connection, if any
    is_connected = await connector.restore_connection()

    # If not connected, prompt the user to connect their wallet
    if not is_connected:
        await message.answer("Прежде чем начать работу с ботом подключите кошелёк")
        await connect_wallet_tonkeeper(message)
        return
    
    sts_wallet_address = await get_wallet_address(connector.account.address, sts_jetton_minter_address)
    ts_wallet_address = await get_wallet_address(connector.account.address, ts_jetton_minter_address)

    if (sts_wallet_address is None or ts_wallet_address is None):
        await message.answer("Что-то пошло не так...\nПопробуйте ещё раз позже")
        return
    
    sts_referer = ''
    ts_referer = ''

    referer_address = cur.execute(f"SELECT referer_address FROM users WHERE tg_id == {message.from_user.id}").fetchall()[0][0]

    try:
        await asyncio.sleep(0.5)
        url = f'https://tonapi.io/v2/blockchain/accounts/{ts_wallet_address}/methods/get_extra_data'
        ts_referer = requests.get(url, headers={'Authorization': f'Bearer {tonapi_key}'}).json()
        await asyncio.sleep(0.5)
        url = f'https://tonapi.io/v2/blockchain/accounts/{sts_wallet_address}/methods/get_extra_data'
        sts_referer = requests.get(url, headers={'Authorization': f'Bearer {tonapi_key}'}).json()
    except Exception as e:
        print(e)
        await message.answer("Что-то пошло не так...\nПопробуйте ещё раз позже")
        return

    transaction = { }
    if ('error' in ts_referer and ts_referer['error'] == 'rate limit: free tier') or ('error' in sts_referer and sts_referer['error'] == 'rate limit: free tier'):
        await message.answer("Что-то пошло не так...\nПопробуйте ещё раз позже")
        return

    if ('error' in ts_referer and ts_referer['error'] == 'entity not found') and ('error' in sts_referer and sts_referer['error'] == 'entity not found'):
        transaction = {
            'valid_until': int(time.time()) + 300,
            'messages': [
                {
                    'address': sts_jetton_minter_address,
                    'amount': '1300000000',
                    'payload': bytes_to_b64str(begin_cell().store_uint(0x2fc0dce9, 32).store_uint(1, 64).store_uint(1, 1).store_ref(begin_cell().store_uint(0x14dc5f3d, 32).store_uint(1, 64).store_address(Address(referer_address)).end_cell()).end_cell().to_boc())
                },

                {
                    'address': ts_jetton_minter_address,
                    'amount': '1300000000',
                    'payload': bytes_to_b64str(begin_cell().store_uint(0x2fc0dce9, 32).store_uint(1, 64).store_uint(1, 1).store_ref(begin_cell().store_uint(0x14dc5f3d, 32).store_uint(1, 64).store_address(Address(referer_address)).end_cell()).end_cell().to_boc())
                },
            ]
        }
    elif ('error' in ts_referer and ts_referer['error'] == 'entity not found'):
        transaction = {
            'valid_until': int(time.time()) + 300,
            'messages': [
                {
                    'address': ts_jetton_minter_address,
                    'amount': '1300000000',
                    'payload': bytes_to_b64str(begin_cell().store_uint(0x2fc0dce9, 32).store_uint(1, 64).store_uint(1, 1).store_ref(begin_cell().store_uint(0x14dc5f3d, 32).store_uint(1, 64).store_address(Address(referer_address)).end_cell()).end_cell().to_boc())
                },
            ]
        }
    elif ('error' in sts_referer and sts_referer['error'] == 'entity not found'):
        transaction = {
            'valid_until': int(time.time()) + 300,
            'messages': [
                {
                    'address': sts_jetton_minter_address,
                    'amount': '1300000000',
                    'payload': bytes_to_b64str(begin_cell().store_uint(0x2fc0dce9, 32).store_uint(1, 64).store_uint(1, 1).store_ref(begin_cell().store_uint(0x14dc5f3d, 32).store_uint(1, 64).store_address(Address(referer_address)).end_cell()).end_cell().to_boc())
                },
            ]
        }
    
    
    if transaction:
        try:
            await message.answer("Подтвердите транзакцию в кошельке для дальнейшей работы с ботом")
            await connector.send_transaction(transaction)
        except Exception as e:
            print(e)
            await message.answer("Что-то пошло не так...\nПопробуйте ещё раз позже")
            return

    
    if not cur.execute(f"SELECT flag FROM users WHERE tg_id == {message.from_user.id}").fetchall()[0][0]:
        sts = cur.execute(f"SELECT sts FROM users WHERE tg_id == {message.from_user.id}").fetchall()[0][0]
        cur.execute(f"UPDATE users SET sts = {sts + 1} WHERE tg_id = {message.from_user.id}")
        cur.execute(f"UPDATE users SET flag = true WHERE tg_id = {message.from_user.id}")
        con.commit()

    await message.answer("Нажмите кнопку «личный кабинет»", reply_markup = PersonalAccount)

@dp.message_handler(commands=['connect_wallet'], state='*', chat_type=types.ChatType.PRIVATE)
async def connect_wallet_tonkeeper(message: types.Message):
    if not cur.execute(f"SELECT tg_id FROM users WHERE tg_id == {message.from_user.id}").fetchall():
        return
    # Create a storage instance based on the user's ID
    storage = database.Storage(str(message.from_user.id))
    
    # Initialize a connection using the given manifest URL and storage
    connector = TonConnect(manifest_url='https://raw.githubusercontent.com/AndreyBur/Access_control_bot/master/pytonconnect-manifest.json', storage=storage)
    # Attempt to restore the existing connection, if any
    is_connected = await connector.restore_connection()

    # If already connected, inform the user and exit the function
    if is_connected:
        await message.answer('Ваш кошелёк уже поключён')
        return

    # Retrieve the available wallets
    wallets_list = connector.get_wallets()

    # Generate a connection URL for the wallet
    generated_url_tonkeeper = await connector.connect(wallets_list[1])

    # Create an inline keyboard markup with a button to open the connection URL
    urlkb = InlineKeyboardMarkup(row_width=1)
    urlButton = InlineKeyboardButton(text=f'Открыть tonkeeper', url=generated_url_tonkeeper)        
    urlkb.add(urlButton)
    
    # Generate a QR code for the connection URL and save it as an image
    img = qrcode.make(generated_url_tonkeeper)
    path = f'image{random.randint(0, 100000)}.png'
    img.save(path)
    photo = InputFile(path)

    # Send the QR code image to the user with the inline keyboard markup
    msg = await bot.send_photo(chat_id=message.chat.id, photo=photo, reply_markup=urlkb)
    # Remove the saved image from the local file system
    os.remove(path)

    address = ''

    # Check for a successful connection in a loop, with a maximum of 300 iterations (300 seconds)
    for i in range(300):
        await asyncio.sleep(0.5)
        if connector.connected:
            if connector.account.address:
                address = Address(connector.account.address).to_string(True, True, True)
            break

    # Delete the previously sent QR code message
    await msg.delete()

    if not address:
        return

    # Confirm to the user that the wallet has been successfully connected
    await message.answer('Ваш кошелёк успешно подключён')

    user_channel_status = await bot.get_chat_member(chat_id=-1002133374530, user_id=message.from_user.id)
    if user_channel_status["status"] == 'left':
        await message.answer("Прежде чем начать работу с ботом подпишитесь на [канал](https://t.me/+mhOR-8h28xg1ZTli)", parse_mode='MarkdownV2', disable_web_page_preview=True, reply_markup = check)
        return
    
    if not cur.execute(f"SELECT flag FROM users WHERE tg_id == {message.from_user.id}").fetchall()[0][0]:
        sts = cur.execute(f"SELECT sts FROM users WHERE tg_id == {message.from_user.id}").fetchall()[0][0]
        cur.execute(f"UPDATE users SET sts = {sts + 1} WHERE tg_id = {message.from_user.id}")
        cur.execute(f"UPDATE users SET flag = true WHERE tg_id = {message.from_user.id}")
        con.commit()
        
    await message.answer("Нажмите кнопку «личный кабинет»", reply_markup = PersonalAccount)

@dp.callback_query_handler(text = 'check')
async def check_subscription(call: types.CallbackQuery):
    user_channel_status = await bot.get_chat_member(chat_id=-1002133374530, user_id=call.from_user.id)
    if user_channel_status["status"] == 'left':
        await call.answer("Вы не подписаны на канал")
        return
    
    await call.message.delete()
    await call.message.answer("Нажмите кнопку «личный кабинет»", reply_markup = PersonalAccount)

@dp.message_handler(text = 'Личный кабинет👤', state='*', chat_type=types.ChatType.PRIVATE)
async def personal_account(message: types.Message):
    if not cur.execute(f"SELECT tg_id FROM users WHERE tg_id == {message.from_user.id}").fetchall():
        return

    await message.delete()

    # Create a storage instance based on the user's ID
    storage = database.Storage(str(message.from_user.id))

    # Initialize a connection using the given manifest URL and storage
    connector = TonConnect(manifest_url='https://raw.githubusercontent.com/AndreyBur/Access_control_bot/master/pytonconnect-manifest.json', storage=storage)
    # Attempt to restore the existing connection, if any
    is_connected = await connector.restore_connection()

    # If not connected, prompt the user to connect their wallet
    if not is_connected:
        await message.answer("Прежде чем начать работу с ботом подключите кошелёк")
        await connect_wallet_tonkeeper(message)
        return
    
    user_channel_status = await bot.get_chat_member(chat_id=-1002133374530, user_id=message.from_user.id)
    if user_channel_status["status"] == 'left':
        await message.answer("Прежде чем начать работу с ботом подпишитесь на [канал](https://t.me/+mhOR-8h28xg1ZTli)", parse_mode='MarkdownV2', disable_web_page_preview=True, reply_markup = check)
        return

    if not cur.execute(f"SELECT flag FROM users WHERE tg_id == {message.from_user.id}").fetchall()[0][0]:
        sts = cur.execute(f"SELECT sts FROM users WHERE tg_id == {message.from_user.id}").fetchall()[0][0]
        cur.execute(f"UPDATE users SET sts = {sts + 1} WHERE tg_id = {message.from_user.id}")
        cur.execute(f"UPDATE users SET flag = true WHERE tg_id = {message.from_user.id}")
        con.commit()

    all_referals = cur.execute(f"SELECT all_referals FROM users WHERE tg_id == {message.from_user.id}").fetchall()[0][0]
    firts_lvl_referals = len(cur.execute(f"SELECT tg_id FROM users WHERE referer == {message.from_user.id}").fetchall())
    me = await bot.get_me()
    link = 'https://t.me/' + me['username'].replace('_', '\\_') + f'?start\\={message.from_user.id}'
    sts = cur.execute(f"SELECT sts FROM users WHERE tg_id == {message.from_user.id}").fetchall()[0][0]
    referer = cur.execute(f"SELECT referer FROM users WHERE tg_id == {message.from_user.id}").fetchall()[0][0]

    if referer is None:
        referer = 'никто'
    else:
        referer_name = (await bot.get_chat(referer)).first_name
        referer = f'[{referer_name}](tg://user?id={referer})'
    
    await bot.send_message(chat_id=message.from_user.id, text=f'Рефералы первого уровня: {firts_lvl_referals}\nВсе рефералы: {all_referals}\nВас пригласил: {referer}\nБаланс STS: {sts:.2f}\nРеферальная ссылка: {link}'.replace('.', '\\.'), parse_mode='MarkdownV2')

@dp.message_handler(commands=['sell_ts'], state='*', chat_type=types.ChatType.PRIVATE)
async def sell_ts(message: types.Message):
    if not cur.execute(f"SELECT tg_id FROM users WHERE tg_id == {message.from_user.id}").fetchall():
        return

    await message.delete()

    # Create a storage instance based on the user's ID
    storage = database.Storage(str(message.from_user.id))

    # Initialize a connection using the given manifest URL and storage
    connector = TonConnect(manifest_url='https://raw.githubusercontent.com/AndreyBur/Access_control_bot/master/pytonconnect-manifest.json', storage=storage)
    # Attempt to restore the existing connection, if any
    is_connected = await connector.restore_connection()

    # If not connected, prompt the user to connect their wallet
    if not is_connected:
        await message.answer("Прежде чем начать работу с ботом подключите кошелёк")
        await connect_wallet_tonkeeper(message)
        return
    
    user_channel_status = await bot.get_chat_member(chat_id=-1002133374530, user_id=message.from_user.id)
    if user_channel_status["status"] == 'left':
        await message.answer("Прежде чем начать работу с ботом подпишитесь на [канал](https://t.me/+mhOR-8h28xg1ZTli)", parse_mode='MarkdownV2', disable_web_page_preview=True, reply_markup = check)
        return

    ts_wallet_address = await get_wallet_address(connector.account.address, ts_jetton_minter_address)

    value = ''
    while value == '':
        try:
            url = f'https://tonapi.io/v2/blockchain/accounts/{ts_wallet_address}/methods/get_wallet_data'
            value = float(requests.get(url, headers={'Authorization': f'Bearer {tonapi_key}'}).json()['decoded']['balance'])
        except Exception as e:
            print(e)
            pass


    await message.answer(f"Введите сколько TS перевести в STS. Ваш баланс {value / 1e9}")
    await States.Sell_ts.set()

@dp.message_handler(state=States.Sell_ts, chat_type=types.ChatType.PRIVATE)
async def process_sell_ts(message: types.Message, state: FSMContext):
    if not cur.execute(f"SELECT tg_id FROM users WHERE tg_id == {message.from_user.id}").fetchall():
        return

    await message.delete()

    # Create a storage instance based on the user's ID
    storage = database.Storage(str(message.from_user.id))

    # Initialize a connection using the given manifest URL and storage
    connector = TonConnect(manifest_url='https://raw.githubusercontent.com/AndreyBur/Access_control_bot/master/pytonconnect-manifest.json', storage=storage)
    # Attempt to restore the existing connection, if any
    is_connected = await connector.restore_connection()

    # If not connected, prompt the user to connect their wallet
    if not is_connected:
        await message.answer("Прежде чем начать работу с ботом подключите кошелёк")
        await connect_wallet_tonkeeper(message)
        return
    
    user_channel_status = await bot.get_chat_member(chat_id=-1002133374530, user_id=message.from_user.id)
    if user_channel_status["status"] == 'left':
        await message.answer("Прежде чем начать работу с ботом подпишитесь на [канал](https://t.me/+mhOR-8h28xg1ZTli)", parse_mode='MarkdownV2', disable_web_page_preview=True, reply_markup = check)
        return

    ts_wallet_address = await get_wallet_address(connector.account.address, ts_jetton_minter_address)

    max_value = ''
    while max_value == '':
        try:
            url = f'https://tonapi.io/v2/blockchain/accounts/{ts_wallet_address}/methods/get_wallet_data'
            max_value = float(requests.get(url, headers={'Authorization': f'Bearer {tonapi_key}'}).json()['decoded']['balance'])
        except Exception as e:
            print(e)
            pass

    try:
        value = float(message.text)
    except Exception as e:
        print(e)
        await message.answer('Не корректное число')
        return

    if value > max_value / 1e9 or value <= 0:
        await message.answer('Не корректное число')
        return

    transaction = {
        'valid_until': int(time.time()) + 300,
        'messages': [
            {
                'address': ts_wallet_address,
                'amount': '1700000000',
                'payload': bytes_to_b64str(begin_cell().store_uint(0x0f8a7ea5, 32).store_uint(1, 64).store_coins(value * 1e9).store_address(Address(sts_jetton_minter_address)).store_address(Address(connector.account.address)).store_uint(0, 1).store_coins(1500000000).store_uint(0, 1).end_cell().to_boc())
            },
        ]
    }
    
    
    try:
        await message.answer("Подтвердите транзакцию в кошельке для дальнейшей работы с ботом")
        await connector.send_transaction(transaction)
    except Exception as e:
        print(e)
        await message.answer("Что-то пошло не так...\nПопробуйте ещё раз позже")
        return

    await state.finish()

@dp.message_handler(commands=['stake_sts'], state='*', chat_type=types.ChatType.PRIVATE)
async def stake_sts(message: types.Message):
    if not cur.execute(f"SELECT tg_id FROM users WHERE tg_id == {message.from_user.id}").fetchall():
        return

    await message.delete()

    # Create a storage instance based on the user's ID
    storage = database.Storage(str(message.from_user.id))

    # Initialize a connection using the given manifest URL and storage
    connector = TonConnect(manifest_url='https://raw.githubusercontent.com/AndreyBur/Access_control_bot/master/pytonconnect-manifest.json', storage=storage)
    # Attempt to restore the existing connection, if any
    is_connected = await connector.restore_connection()

    # If not connected, prompt the user to connect their wallet
    if not is_connected:
        await message.answer("Прежде чем начать работу с ботом подключите кошелёк")
        await connect_wallet_tonkeeper(message)
        return
    
    user_channel_status = await bot.get_chat_member(chat_id=-1002133374530, user_id=message.from_user.id)
    if user_channel_status["status"] == 'left':
        await message.answer("Прежде чем начать работу с ботом подпишитесь на [канал](https://t.me/+mhOR-8h28xg1ZTli)", parse_mode='MarkdownV2', disable_web_page_preview=True, reply_markup = check)
        return

    sts_wallet_address = await get_wallet_address(connector.account.address, sts_jetton_minter_address)

    value = ''
    while value == '':
        try:
            url = f'https://tonapi.io/v2/blockchain/accounts/{sts_wallet_address}/methods/get_wallet_data'
            value = float(requests.get(url, headers={'Authorization': f'Bearer {tonapi_key}'}).json()['decoded']['balance'])
        except Exception as e:
            print(e)
            pass

    if value / 1e9 < 20:
        await message.answer('Недостаточно STS')
        return

    await message.answer(f"Введите сколько STS застейкать. Ваш баланс {value / 1e9}. (минимум 20)")
    await States.Stake_sts.set()

@dp.message_handler(state=States.Stake_sts, chat_type=types.ChatType.PRIVATE)
async def process_stake_sts(message: types.Message, state: FSMContext):
    if not cur.execute(f"SELECT tg_id FROM users WHERE tg_id == {message.from_user.id}").fetchall():
        return

    await message.delete()

    # Create a storage instance based on the user's ID
    storage = database.Storage(str(message.from_user.id))

    # Initialize a connection using the given manifest URL and storage
    connector = TonConnect(manifest_url='https://raw.githubusercontent.com/AndreyBur/Access_control_bot/master/pytonconnect-manifest.json', storage=storage)
    # Attempt to restore the existing connection, if any
    is_connected = await connector.restore_connection()

    # If not connected, prompt the user to connect their wallet
    if not is_connected:
        await message.answer("Прежде чем начать работу с ботом подключите кошелёк")
        await connect_wallet_tonkeeper(message)
        return
    
    user_channel_status = await bot.get_chat_member(chat_id=-1002133374530, user_id=message.from_user.id)
    if user_channel_status["status"] == 'left':
        await message.answer("Прежде чем начать работу с ботом подпишитесь на [канал](https://t.me/+mhOR-8h28xg1ZTli)", parse_mode='MarkdownV2', disable_web_page_preview=True, reply_markup = check)
        return

    sts_wallet_address = await get_wallet_address(connector.account.address, sts_jetton_minter_address)

    max_value = ''
    while max_value == '':
        try:
            url = f'https://tonapi.io/v2/blockchain/accounts/{sts_wallet_address}/methods/get_wallet_data'
            max_value = float(requests.get(url, headers={'Authorization': f'Bearer {tonapi_key}'}).json()['decoded']['balance'])
        except Exception as e:
            print(e)
            pass

    try:
        value = float(message.text)
    except Exception as e:
        print(e)
        await message.answer('Не корректное число')
        return

    if value > max_value / 1e9 or value <= 0:
        await message.answer('Не корректное число')
        return
    
    if max_value / 1e9 < 20:
        await message.answer('Недостаточно STS')
        return

    transaction = {
        'valid_until': int(time.time()) + 300,
        'messages': [
            {
                'address': sts_wallet_address,
                'amount': '600000000',
                'payload': bytes_to_b64str(begin_cell().store_uint(0x1c235de0, 32).store_uint(1, 64).store_coins(value * 1e9).end_cell().to_boc())
            },
        ]
    }
    
    
    try:
        await message.answer("Подтвердите транзакцию в кошельке для дальнейшей работы с ботом")
        await connector.send_transaction(transaction)
    except Exception as e:
        print(e)
        await message.answer("Что-то пошло не так...\nПопробуйте ещё раз позже")
        return

    await state.finish()

@dp.message_handler(commands=['unstake_sts'], state='*', chat_type=types.ChatType.PRIVATE)
async def unstake_sts(message: types.Message):
    if not cur.execute(f"SELECT tg_id FROM users WHERE tg_id == {message.from_user.id}").fetchall():
        return

    await message.delete()

    # Create a storage instance based on the user's ID
    storage = database.Storage(str(message.from_user.id))

    # Initialize a connection using the given manifest URL and storage
    connector = TonConnect(manifest_url='https://raw.githubusercontent.com/AndreyBur/Access_control_bot/master/pytonconnect-manifest.json', storage=storage)
    # Attempt to restore the existing connection, if any
    is_connected = await connector.restore_connection()

    # If not connected, prompt the user to connect their wallet
    if not is_connected:
        await message.answer("Прежде чем начать работу с ботом подключите кошелёк")
        await connect_wallet_tonkeeper(message)
        return
    
    user_channel_status = await bot.get_chat_member(chat_id=-1002133374530, user_id=message.from_user.id)
    if user_channel_status["status"] == 'left':
        await message.answer("Прежде чем начать работу с ботом подпишитесь на [канал](https://t.me/+mhOR-8h28xg1ZTli)", parse_mode='MarkdownV2', disable_web_page_preview=True, reply_markup = check)
        return

    sts_wallet_address = await get_wallet_address(connector.account.address, sts_jetton_minter_address)

    value = ''
    while value == '':
        try:
            url = f'https://tonapi.io/v2/blockchain/accounts/{sts_wallet_address}/methods/get_extra_data'
            value = int(requests.get(url, headers={'Authorization': f'Bearer {tonapi_key}'}).json()['stack'][0]['num'], 16)
        except Exception as e:
            print(e)
            pass

    await message.answer(f"Введите сколько STS анстейкнуть. Ваш баланс {value / 1e9}. (в стейке должно остаться не меньше 20 или 0)")
    await States.Unstake_sts.set()

@dp.message_handler(state=States.Unstake_sts, chat_type=types.ChatType.PRIVATE)
async def process_unstake_sts(message: types.Message, state: FSMContext):
    if not cur.execute(f"SELECT tg_id FROM users WHERE tg_id == {message.from_user.id}").fetchall():
        return

    await message.delete()

    # Create a storage instance based on the user's ID
    storage = database.Storage(str(message.from_user.id))

    # Initialize a connection using the given manifest URL and storage
    connector = TonConnect(manifest_url='https://raw.githubusercontent.com/AndreyBur/Access_control_bot/master/pytonconnect-manifest.json', storage=storage)
    # Attempt to restore the existing connection, if any
    is_connected = await connector.restore_connection()

    # If not connected, prompt the user to connect their wallet
    if not is_connected:
        await message.answer("Прежде чем начать работу с ботом подключите кошелёк")
        await connect_wallet_tonkeeper(message)
        return
    
    user_channel_status = await bot.get_chat_member(chat_id=-1002133374530, user_id=message.from_user.id)
    if user_channel_status["status"] == 'left':
        await message.answer("Прежде чем начать работу с ботом подпишитесь на [канал](https://t.me/+mhOR-8h28xg1ZTli)", parse_mode='MarkdownV2', disable_web_page_preview=True, reply_markup = check)
        return

    sts_wallet_address = await get_wallet_address(connector.account.address, sts_jetton_minter_address)

    max_value = ''
    while max_value == '':
        try:
            url = f'https://tonapi.io/v2/blockchain/accounts/{sts_wallet_address}/methods/get_extra_data'
            max_value = int(requests.get(url, headers={'Authorization': f'Bearer {tonapi_key}'}).json()['stack'][0]['num'], 16)
        except Exception as e:
            print(e)
            pass

    try:
        value = float(message.text)
    except Exception as e:
        print(e)
        await message.answer('Не корректное число')
        return

    if value > max_value / 1e9 or value <= 0:
        await message.answer('Не корректное число')
        return
    
    if max_value / 1e9 - value < 20 and max_value / 1e9 - value != 0:
        await message.answer('Не корректное число')
        return

    transaction = {
        'valid_until': int(time.time()) + 300,
        'messages': [
            {
                'address': sts_wallet_address,
                'amount': '200000000',
                'payload': bytes_to_b64str(begin_cell().store_uint(0x48e9880f, 32).store_uint(1, 64).store_coins(value * 1e9).end_cell().to_boc())
            },
        ]
    }
    
    
    try:
        await message.answer("Подтвердите транзакцию в кошельке для дальнейшей работы с ботом")
        await connector.send_transaction(transaction)
    except Exception as e:
        print(e)
        await message.answer("Что-то пошло не так...\nПопробуйте ещё раз позже")
        return

    await state.finish()

@dp.message_handler(commands=['buy_ts'], state='*', chat_type=types.ChatType.PRIVATE)
async def buy_ts(message: types.Message):
    if not cur.execute(f"SELECT tg_id FROM users WHERE tg_id == {message.from_user.id}").fetchall():
        return

    await message.delete()

    # Create a storage instance based on the user's ID
    storage = database.Storage(str(message.from_user.id))

    # Initialize a connection using the given manifest URL and storage
    connector = TonConnect(manifest_url='https://raw.githubusercontent.com/AndreyBur/Access_control_bot/master/pytonconnect-manifest.json', storage=storage)
    # Attempt to restore the existing connection, if any
    is_connected = await connector.restore_connection()

    # If not connected, prompt the user to connect their wallet
    if not is_connected:
        await message.answer("Прежде чем начать работу с ботом подключите кошелёк")
        await connect_wallet_tonkeeper(message)
        return
    
    user_channel_status = await bot.get_chat_member(chat_id=-1002133374530, user_id=message.from_user.id)
    if user_channel_status["status"] == 'left':
        await message.answer("Прежде чем начать работу с ботом подпишитесь на [канал](https://t.me/+mhOR-8h28xg1ZTli)", parse_mode='MarkdownV2', disable_web_page_preview=True, reply_markup = check)
        return


    await message.answer(f"Введите сколько TS купить.")
    await States.Buy_ts.set()

@dp.message_handler(state=States.Buy_ts, chat_type=types.ChatType.PRIVATE)
async def process_buy_ts(message: types.Message, state: FSMContext):
    if not cur.execute(f"SELECT tg_id FROM users WHERE tg_id == {message.from_user.id}").fetchall():
        return

    await message.delete()

    # Create a storage instance based on the user's ID
    storage = database.Storage(str(message.from_user.id))

    # Initialize a connection using the given manifest URL and storage
    connector = TonConnect(manifest_url='https://raw.githubusercontent.com/AndreyBur/Access_control_bot/master/pytonconnect-manifest.json', storage=storage)
    # Attempt to restore the existing connection, if any
    is_connected = await connector.restore_connection()

    # If not connected, prompt the user to connect their wallet
    if not is_connected:
        await message.answer("Прежде чем начать работу с ботом подключите кошелёк")
        await connect_wallet_tonkeeper(message)
        return
    
    user_channel_status = await bot.get_chat_member(chat_id=-1002133374530, user_id=message.from_user.id)
    if user_channel_status["status"] == 'left':
        await message.answer("Прежде чем начать работу с ботом подпишитесь на [канал](https://t.me/+mhOR-8h28xg1ZTli)", parse_mode='MarkdownV2', disable_web_page_preview=True, reply_markup = check)
        return

    try:
        value = float(message.text)
    except Exception as e:
        print(e)
        await message.answer('Не корректное число')
        return

    transaction = {
        'valid_until': int(time.time()) + 300,
        'messages': [
            {
                'address': ts_jetton_minter_address,
                'amount': f'{value * 1e9}',
                'payload': bytes_to_b64str(begin_cell().store_uint(0x785c33da, 32).store_uint(1, 64).end_cell().to_boc())
            },
        ]
    }
    
    
    try:
        await message.answer("Подтвердите транзакцию в кошельке для дальнейшей работы с ботом")
        await connector.send_transaction(transaction)
    except Exception as e:
        print(e)
        await message.answer("Что-то пошло не так...\nПопробуйте ещё раз позже")
        return

    await state.finish()


# Entry point for the application; starts polling for updates from the Telegram API
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)