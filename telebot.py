import asyncio
import io
import random
import urllib.request
import config
from PIL import Image, ImageDraw, ImageFont
import aiohttp
import asyncpraw
from aiogram import Bot, types
from aiogram.utils import exceptions
from aiogram.dispatcher import Dispatcher
from aiogram.types import InputFile



API_TOKEN = config.settings['TOKEN']
CHANNEL_ID = -1001753223893
SUBBREDIT_LIST = ['starterpacks', 'memes', 'AdviceAnimals', 'BikiniBottomTwitter', 'me_irl', 'NSFWFunny', 'dankmemes', 'meme', '4chan', 'MemeMan',
                  'NSFWMeme', 'NSFWMemes', 'NSFWMemes2', 'badmemes']


bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
dispatcher = Dispatcher(bot)

reddit = asyncpraw.Reddit(client_id=config.settings['CLIENT_ID'],
                          client_secret=config.settings['SECRET_CODE'],
                          user_agent='random_reddit_bot/0.0.1')

mems = []

TIMEOUT = 30

POST_LIMIT = 1


async def send_photo(channel_id: int, title: str, photo: bytes):
    try:
        image = Image.open(io.BytesIO(photo))
    except (IOError, OSError) as e:
        print(f"Error loading image: {e}")
        return

    try:
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("arial.ttf", 32)
        text = "t.me/memesreddits"
        textwidth, textheight = draw.textsize(text, font)
        x = image.width - textwidth - 10
        y = image.height - textheight - 10
        draw.text((x, y), text, font=font, fill='#FF0000')
        photo_io = io.BytesIO()
        image.save(photo_io, format='JPEG')
        photo_io.seek(0)
        photo = photo_io.getvalue()

        await bot.send_photo(chat_id=channel_id, caption=title, photo=InputFile(io.BytesIO(photo)))
    except exceptions.BadRequest as e:
        print(f"Error sending photo: {e}")
    except exceptions.RetryAfter as e:
        print(f"Retry after {TIMEOUT} seconds.")
        await asyncio.sleep(TIMEOUT)
        return await send_photo(channel_id, title, photo)
    except Exception as e:
        print(f"Unhandled error sending photo: {e}")



async def main():
    while True:
        try:
            # выбираем случайный subreddit из списка
            SUBREDDIT_NAME = random.choice(SUBBREDIT_LIST)

            # ждем заданное количество секунд
            await asyncio.sleep(TIMEOUT)

            # получаем новые посты из subreddit
            memes_submissions = await reddit.subreddit(SUBREDDIT_NAME)
            memes_submissions = memes_submissions.new(limit=POST_LIMIT)
            item = await memes_submissions.__anext__()

            # если пост еще не был отправлен, отправляем его
            if item.title not in mems:
                mems.append(item.title)

                # загружаем картинку из поста
                url = item.url
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        photo = await response.read()

                # добавляем водяной знак на картинку и отправляем сообщение с картинкой и названием поста
                await send_photo(CHANNEL_ID, item.title, photo)
        except Exception as e:
            print(f"Unhandled error in main loop: {e}")
            print("Restarting the loop...")
            continue


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
