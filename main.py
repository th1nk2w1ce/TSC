from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.markdown import link
from aiogram.types.input_file import InputFile
from config import api_token, bot_id
import database

bot = Bot(token=api_token)
dp = Dispatcher(bot, storage=MemoryStorage())

@dp.message_handler(commands=['start'], chat_type=types.ChatType.PRIVATE)
async def start_command(message: types.Message):
    # Create a storage instance based on the user's ID
    storage = database.Storage(str(message.from_user.id))

    # Initialize a connection using the given manifest URL and storage
    connector = TonConnect(manifest_url='https://raw.githubusercontent.com/AndreyBurnosov/Checking_for_nft_availability/main/pytonconnect-manifest.json', storage=storage)
    # Attempt to restore the existing connection, if any
    is_connected = await connector.restore_connection()

    # If not connected, prompt the user to connect their wallet
    if not is_connected:
        await message.answer("To check for the presence of NFT, connect your wallet in Tonkeeper")
        await connect_wallet_tonkeeper(message)
        return
    
    user_channel_status = await bot.get_chat_member(chat_id='@chatid', user_id=message.from_user.id)
    if user_channel_status["status"] == 'left':
        message.answer("Before you start working with the bot, subscribe to the channel")
        return 

@dp.message_handler(commands=['connect_wallet'], chat_type=types.ChatType.PRIVATE)
async def connect_wallet_tonkeeper(message: types.Message):
    # Create a storage instance based on the user's ID
    storage = database.Storage(str(message.from_user.id))
    
    # Initialize a connection using the given manifest URL and storage
    connector = TonConnect(manifest_url='https://raw.githubusercontent.com/AndreyBurnosov/Checking_for_nft_availability/main/pytonconnect-manifest.json', storage=storage)
    # Attempt to restore the existing connection, if any
    is_connected = await connector.restore_connection()

    # If already connected, inform the user and exit the function
    if is_connected:
        await message.answer('Your wallet is already connected.')
        return

    # Retrieve the available wallets
    wallets_list = connector.get_wallets()

    # Generate a connection URL for the wallet
    generated_url_tonkeeper = await connector.connect(wallets_list[0])

    # Create an inline keyboard markup with a button to open the connection URL
    urlkb = InlineKeyboardMarkup(row_width=1)
    urlButton = InlineKeyboardButton(text=f'Open {message.text}', url=generated_url_tonkeeper)        
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

    # Check for a successful connection in a loop, with a maximum of 300 iterations (300 seconds)
    for i in range(300):
        await asyncio.sleep(1)
        if connector.connected:
            if connector.account.address:
                address = Address(connector.account.address).to_string(True, True, True)
            break

    # Delete the previously sent QR code message
    await msg.delete()

    # Confirm to the user that the wallet has been successfully connected
    await message.answer('Your wallet has been successfully connected.', reply_markup=kb.Checkkb)