import qrcode
import os
import sqlite3
import random
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.markdown import link
from aiogram.types.input_file import InputFile
from tonsdk.utils import Address
from pytonconnect import TonConnect
from config import api_token
import database

con = sqlite3.connect("DB.db", check_same_thread=False)
cur = con.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS "users" (
    "tg_id" INTEGER,
    "sts"   INTEGER DEFAULT (0),
    "flag"  BOOLEAN DEFAULT (false),
    "referer" INTEGER,
    "all_referals" INTEGER DEFAULT (0)
)''')

bot = Bot(token=api_token)
dp = Dispatcher(bot)

Account = KeyboardButton('Личный кабинет👤')

PersonalAccount = ReplyKeyboardMarkup(resize_keyboard=True).add(Account)

check = InlineKeyboardMarkup(row_width=1)

checkButton = InlineKeyboardButton(text='Проверить подписку', callback_data='check')        

check.add(checkButton)

@dp.message_handler(commands=['start'], chat_type=types.ChatType.PRIVATE)
async def start_command(message: types.Message):
    if not cur.execute(f"SELECT tg_id FROM users WHERE tg_id == {message.from_user.id}").fetchall():
        if len(message.text.split()) > 1:
            if int(message.text.split()[1]) != int(message.from_user.id):
                try:
                    cur.execute(f"INSERT INTO users (tg_id) VALUES ({message.from_user.id})")
                    con.commit()
                    sts = cur.execute(f"SELECT sts FROM users WHERE tg_id == {message.text.split()[1]}").fetchall()[0][0]
                    cur.execute(f"UPDATE users SET referer = {message.text.split()[1]} WHERE tg_id = {message.from_user.id}")
                    cur.execute(f"UPDATE users SET sts = {sts + 0.2} WHERE tg_id = {message.text.split()[1]}")
                    con.commit()

                    user = message.from_user.id
                    depth = 1
                    while depth <= 12:
                        referer = cur.execute(f"SELECT referer FROM users WHERE tg_id == {user}").fetchall()[0][0]
                        if referer is None:
                            break
                        all_referals = cur.execute(f"SELECT all_referals FROM users WHERE tg_id == {referer}").fetchall()[0][0]
                        cur.execute(f"UPDATE users SET all_referals = {all_referals + 1} WHERE tg_id = {referer}")
                        con.commit()
                        depth += 1
                        user = referer
                except:
                    pass
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
    
    user_channel_status = await bot.get_chat_member(chat_id=-1001738673084, user_id=message.from_user.id)
    if user_channel_status["status"] == 'left':
        await message.answer("Прежде чем начать работу с ботом подпишитесь на [канал](https://t.me/tspc_channel)", parse_mode='MarkdownV2', disable_web_page_preview=True, reply_markup = check)
        return
    
    if not cur.execute(f"SELECT flag FROM users WHERE tg_id == {message.from_user.id}").fetchall()[0][0]:
        sts = cur.execute(f"SELECT sts FROM users WHERE tg_id == {message.from_user.id}").fetchall()[0][0]
        cur.execute(f"UPDATE users SET sts = {sts + 1} WHERE tg_id = {message.from_user.id}")
        cur.execute(f"UPDATE users SET flag = true WHERE tg_id = {message.from_user.id}")
        con.commit()

    await message.answer("Нажмите кнопку «личный кабинет»", reply_markup = PersonalAccount)

@dp.message_handler(commands=['connect_wallet'], chat_type=types.ChatType.PRIVATE)
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
    generated_url_tonkeeper = await connector.connect(wallets_list[0])

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
        await asyncio.sleep(1)
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

    user_channel_status = await bot.get_chat_member(chat_id=-1001738673084, user_id=message.from_user.id)
    if user_channel_status["status"] == 'left':
        await message.answer("Прежде чем начать работу с ботом подпишитесь на [канал](https://t.me/tspc_channel)", parse_mode='MarkdownV2', disable_web_page_preview=True, reply_markup = check)
        return
    
    if not cur.execute(f"SELECT flag FROM users WHERE tg_id == {message.from_user.id}").fetchall()[0][0]:
        sts = cur.execute(f"SELECT sts FROM users WHERE tg_id == {message.from_user.id}").fetchall()[0][0]
        cur.execute(f"UPDATE users SET sts = {sts + 1} WHERE tg_id = {message.from_user.id}")
        cur.execute(f"UPDATE users SET flag = true WHERE tg_id = {message.from_user.id}")
        con.commit()
        
    await message.answer("Нажмите кнопку «личный кабинет»", reply_markup = PersonalAccount)

@dp.callback_query_handler(text = 'check')
async def check_subscription(call: types.CallbackQuery):
    user_channel_status = await bot.get_chat_member(chat_id=-1001738673084, user_id=call.from_user.id)
    if user_channel_status["status"] == 'left':
        await call.answer("Вы не подписаны на канал")
        return
    
    await call.message.delete()
    await call.message.answer("Нажмите кнопку «личный кабинет»", reply_markup = PersonalAccount)

@dp.message_handler(text = 'Личный кабинет👤', chat_type=types.ChatType.PRIVATE)
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
    
    user_channel_status = await bot.get_chat_member(chat_id=-1001738673084, user_id=message.from_user.id)
    if user_channel_status["status"] == 'left':
        await message.answer("Прежде чем начать работу с ботом подпишитесь на [канал](https://t.me/tspc_channel)", parse_mode='MarkdownV2', disable_web_page_preview=True, reply_markup = check)
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

# Entry point for the application; starts polling for updates from the Telegram API
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)