import logging

from aiogram import types
from sqlalchemy.orm import sessionmaker

from data.config import admins
from loader import bot, dp
from utils.db_api.models import engine, Chat


@dp.message_handler(content_types=['new_chat_members'])
async def bot_welcome(message: types.Message):
    bot_obj = await bot.get_me()
    bot_id = bot_obj.id

    for chat_member in message.new_chat_members:
        if chat_member.id == bot_id:
            session = sessionmaker(bind=engine)()

            title = message.chat.title
            chat_id = message.chat.id

            # проверяем есть ли в базе такой чат
            flag = session.query(Chat).get(chat_id)
            if flag is None:
                new_chat = Chat(chat_id=chat_id, title=title, group_id=1)
                session.add(new_chat)
                session.commit()
                logging.info(f'Добавлено чат "{title}" в базу данных')
            else:
                logging.info(f'Чат "{title}" уже есть в базе данных')

            session.close()

            for admin in admins:
                await bot.send_message(admin, f'Бот был добавлен в чат "{title}"')


@dp.message_handler(content_types=['left_chat_member'])
async def left_bot(message: types.Message):
    bot_obj = await bot.get_me()
    bot_id = bot_obj.id
    title = message.chat.title
    chat_id = message.chat.id

    if message.left_chat_member.id == bot_id:
        session = sessionmaker(bind=engine)()
        chat = session.query(Chat).get(chat_id)
        if chat is None:
            logging.error(f'Ошибка при удалении бота с чата "{chat_id}"')
        else:
            session.delete(chat)
            session.commit()
            logging.info(f'Бот вышел из чата "{title}" и был удален из базы')
        session.close()

        for admin in admins:
            await bot.send_message(admin, f'Бот был удален из чата "{title}"')

@dp.message_handler(content_types=['migrate_to_chat_id'])
async def migrate_group_to_supergroup(message: types.Message):
    bot_obj = await bot.get_me()
    migrate_from_chat_id = message.chat.id
    migrate_to_chat_id = message.migrate_to_chat_id
    title = message.chat.title

    session = sessionmaker(bind=engine)()
    chat = session.query(Chat).get(migrate_from_chat_id)
    if chat is None:
        logging.error(f'Ошибка при миграции чата с id "{migrate_from_chat_id}" на id "{migrate_to_chat_id}". Title чата - "{title}"')
        for admin in admins:
            await bot.send_message(admin, f'Ошибка при миграции чата с id "{migrate_from_chat_id}" на id "{migrate_to_chat_id}". Title чата - "{title}". Чат не найден.')
    else:
        session.query(Chat).update({"chat_id": migrate_to_chat_id})
        session.commit()
        logging.info(f'Миграция чата "{title}" была проведена успешно - новый айди "{migrate_to_chat_id}"')
        session.close()
        for admin in admins:
            await bot.send_message(admin, f'Миграция чата "{title}" была проведена успешно - новый айди "{migrate_to_chat_id}"')

