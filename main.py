import config
import middleware
import telebot
import models
import time
from datetime import datetime
from datetime import timedelta
from middleware import keyboard
from app import fsm, bot
from app import main_base as base
from tool import language_check, create_inlineKeyboard
import os
import asyncio
import traceback

from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.fx import crop

from moviepy.editor import *
from telegram import Update, InputMediaVideo
from telegram.ext import CallbackContext

middleware.start_draw_timer()
middleware.end_draw_timer()

TEMP_FOLDER = "temp_videos"
FILE_VIDEO_PATH = 'test'
input_video_path = ''
output_video_path = ''
FLAG_PUBLISH_VIDEO = False
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)


@bot.message_handler(commands=['start'])
def start(message):
    print(base.select_all(models.DrawNot))
    base.delete(models.State, user_id=message.chat.id)
    if message.chat.type == 'private':
        text = language_check(message.chat.id)
        if text[0] == True:
            bot.send_message(message.chat.id, language_check(message.chat.id)[1]['menu']['welcome_text'], reply_markup=keyboard.get_menu_keyboard(message.chat.id))
        else:
            bot.send_message(message.chat.id, language_check(message.chat.id)[1]['menu']['welcome_text'], reply_markup=keyboard.get_menu_keyboard(message.chat.id))
            base.new(models.User, str(message.chat.id), str(message.chat.username), "RU")


@bot.callback_query_handler(func=lambda call: True and call.data.split('_')[0] == 'geton')
def get_on_draw(call):
    try:
        text = language_check(call.message.chat.id)[1]['draw']
        tmp = middleware.new_player(call)
        print(tmp)
        if tmp == 'not_subscribe':
            bot.answer_callback_query(callback_query_id=call.id, show_alert=True,  text=text['not_subscribe'])
        if tmp == 'n_posts_error':
            bot.answer_callback_query(callback_query_id=call.id,show_alert=True, text=text['n_posts_error'])
        if tmp is False:
            bot.answer_callback_query(callback_query_id=call.id, show_alert=True,  text=text['already_in'])
        else:
            bot.answer_callback_query(callback_query_id=call.id, show_alert=True,  text=text['got_on'])
            #bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, inline_message_id=call.inline_message_id, reply_markup=create_inlineKeyboard({f"({tmp[1]}) {tmp[2]}":call.data}))
    except Exception as e:
        print(traceback.format_exc())


@bot.message_handler(func=lambda message: True and message.text == language_check(message.chat.id)[1]['menu']['menu_buttons'][2])
def change_language(message):
    user = base.get_one(models.User, user_id=str(message.chat.id))
    print(user)
    if user.language == 'RU':
        base.update(models.User, {'language': "ENG"}, user_id=str(message.chat.id))
        bot.send_message(message.chat.id, language_check(message.chat.id)[1]['menu']['welcome_text'], reply_markup=keyboard.get_menu_keyboard(message.chat.id))
    else:
        base.update(models.User, {'language': "RU"}, user_id=str(message.chat.id))
        bot.send_message(message.chat.id, language_check(message.chat.id)[1]['menu']['welcome_text'], reply_markup=keyboard.get_menu_keyboard(message.chat.id))


@bot.message_handler(func=lambda message: True and message.text == language_check(message.chat.id)[1]['menu']['channels_menu'][-1])
def back_editing(message):
    bot.send_message(message.chat.id, text="Выберите действие", reply_markup=keyboard.channel_buttons(message.chat.id))


@bot.message_handler(func=lambda message: True and message.text == language_check(message.chat.id)[1]['draw']['back_in_menu'])
def back_in_menu(message):
    base.delete(models.State, user_id=str(message.chat.id))
    base.delete(models.DrawProgress, user_id=(str(message.chat.id)))
    base.delete(models.SubscribeChannel, user_id=(str(message.chat.id)))
    bot.send_message(message.chat.id, language_check(message.chat.id)[1]['menu']['welcome_text'], reply_markup=keyboard.get_menu_keyboard(message.chat.id))


@bot.message_handler(func=lambda message: True and message.text == language_check(message.chat.id)[1]['menu']['menu_buttons'][-1])
def channels_edit(message):
    bot.send_message(message.chat.id, text="Выберите действие", reply_markup=keyboard.channel_buttons(message.chat.id))
    # channels = base.select_all(models.Channels)
    # print(channels)


@bot.message_handler(func=lambda message: True and message.text == language_check(message.chat.id)[1]['menu']['channels_menu'][1])
def delete_channel(message):
    try:
        if len(base.select_all(models.Channels)) > 0:
            text = language_check(str(message.chat.id))
            back_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            back_button.row(text[1]['menu']['channels_menu'][-1])
            bot.send_message(message.chat.id,
                             text="Вам отправлен список каналов доступных для удаления.",
                             reply_markup=back_button)
            markup = telebot.types.InlineKeyboardMarkup()
            channels = [channel.channel_id for channel in base.select_all(models.Channels)]
            for channel in channels:
                # Предполагаем, что `channel` имеет атрибут `name` для отображения имени канала
                button = telebot.types.InlineKeyboardButton(text=channel, callback_data=f'delete_{channel}')
                markup.add(button)

            # Отправляем сообщение с инлайн-кнопками под предыдущим сообщением
            bot.send_message(message.chat.id, text="Выберите канал, который вы хотели бы удалить ❌",
                             reply_markup=markup)
        else:
            bot.send_message(message.chat.id, text="У вас нет добавленных каналов, которые можно удалить 😞")
    except:
        print(traceback.format_exc())


@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
def handle_delete_channel(call):
    channel_id = call.data.split('_')[1]
    base.delete(models.Channels, channel_id=channel_id)
    bot.send_message(call.from_user.id, text="Канал " + str(channel_id) + " успешно удален ✅", reply_markup=keyboard.channel_buttons(call.from_user.id))


@bot.message_handler(func=lambda message: True and message.text == language_check(message.chat.id)[1]['menu']['channels_menu'][0])
def add_channel(message):
    text = language_check(str(message.chat.id))
    back_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_button.row(text[1]['menu']['channels_menu'][-1])
    fsm.set_state(message.chat.id, 'add_channel_base')
    bot.send_message(message.chat.id, text="Введите юзернейм канала в формате @username. 🎉 Вы должны быть администратором этого канала и добавить в администраторы бота. 🤖 Если канал приватный, то необходимо отправить ID этого канала. 🔐 Чтобы узнать ID приватного канала, перешлите любой пост из этого канала специальному боту @getmyid_bot. 📩 Нижняя строка — ответ от бота и будет являться ID вашего приватного канала. 📜 Перешлите этот ID боту! 🚀", reply_markup=back_button)


@bot.message_handler(func=lambda message: True and fsm.get_state(message.chat.id)[0] == 'add_channel_base')
def add_channel(message):
    status = ['creator', 'administrator']
    text = language_check(str(message.chat.id))[1]['menu']
    back_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_button.row(text['channels_menu'][-1])

    try:
        if str(bot.get_chat_member(chat_id=message.text, user_id=message.from_user.id).status) not in status:
            bot.send_message(language_check(str(message.chat.id))[1]['draw']['not_admin'], reply_markup=back_button)
            return ''
        tmp = bot.send_message(message.text, 'test')
        bot.delete_message(tmp.chat.id, tmp.message_id)
        id = len([channel.channel_id for channel in base.select_all(models.Channels)])
        base.new(models.Channels, id, message.text)
        bot.send_message(message.chat.id, text="Канал успешно добавлен ✅", reply_markup=keyboard.channel_buttons(message.chat.id))
    except:
        print(traceback.format_exc())
        bot.send_message(message.chat.id, language_check(str(message.chat.id))[1]['draw']['not_in_chanel'], reply_markup=back_button)
        return ''


@bot.message_handler(func=lambda message: True and message.text == language_check(message.chat.id)[1]['draw']['back'] and middleware.check_post(message.chat.id) != None)
def back_in_draw_menu(message):
    base.delete(models.State, user_id=str(message.chat.id))
    middleware.send_draw_info(message.chat.id)


@bot.message_handler(func=lambda message: True and message.text == language_check(message.chat.id)[1]['menu']['menu_buttons'][1])
def my_draws(message):
    middleware.my_draw_info(message.chat.id)
    fsm.set_state(message.chat.id, 'my_draws', number=0)


@bot.callback_query_handler(func=lambda call: True and call.data == 'next')
def next(call):
    try:
        text = language_check(call.message.chat.id)[1]['my_draw']
        number = int(fsm.get_state(call.message.chat.id)[1]['number']) + 1
        tmp = middleware.my_draw_info(call.message.chat.id, row=number)
        if tmp == 'last':
            bot.answer_callback_query(callback_query_id=call.id, show_alert=False,  text=text['last'])
            return
        bot.delete_message(call.message.chat.id, call.message.message_id)
        fsm.set_state(call.message.chat.id, 'my_draws', number=number)
    except:
        fsm.remove_state(call.message.chat.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: True and call.data == 'back')
def back(call):
    try:
        text = language_check(call.message.chat.id)[1]['my_draw']
        number = int(fsm.get_state(call.message.chat.id)[1]['number']) - 1
        tmp = middleware.my_draw_info(call.message.chat.id, row=number)
        if tmp == 'first':
            bot.answer_callback_query(callback_query_id=call.id, show_alert=False,  text=text['first'])
            return

        bot.delete_message(call.message.chat.id, call.message.message_id)
        fsm.set_state(call.message.chat.id, 'my_draws', number=number)
    except:
        fsm.remove_state(call.message.chat.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.message_handler(func=lambda message: True and middleware.check_post(message.chat.id) != None and message.text == language_check(message.chat.id)[1]['draw']['draw_buttons'][-3])
def submit(message):
    text = language_check(str(message.chat.id))
    bot.send_message(message.chat.id, text[1]['draw']['submit_text'], reply_markup=keyboard.get_menu_keyboard(message.chat.id))
    tmp = base.get_one(models.DrawProgress, user_id=str(message.chat.id))
    base.new(models.DrawNot, tmp.id, tmp.user_id, tmp.chanel_id, tmp.chanel_name, tmp.text, tmp.file_type, tmp.file_id, tmp.winers_count, tmp.n_posts, tmp.post_time, tmp.end_time)
    base.delete(models.DrawProgress, user_id=(str(message.chat.id)))
    base.delete(models.State, user_id=(str(message.chat.id)))


@bot.message_handler(func=lambda message: True and message.text == language_check(message.chat.id)[1]['menu']['menu_buttons'][0])
def enter_id(message):
    base.delete(models.DrawProgress, user_id=(str(message.chat.id)))
    base.delete(models.SubscribeChannel, user_id=(str(message.chat.id)))
    text = language_check(str(message.chat.id))[1]['draw']
    back_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_button.row(text['back_in_menu'])
    markup = telebot.types.InlineKeyboardMarkup()
    channels = [channel.channel_id for channel in base.select_all(models.Channels)]
    for channel in channels:
        # Предполагаем, что `channel` имеет атрибут `name` для отображения имени канала
        button = telebot.types.InlineKeyboardButton(text=channel, callback_data=f'Choose_{channel}')
        markup.add(button)
    fsm.set_state(message.chat.id, "writting_channel_id")
    bot.send_message(message.chat.id, text['chanel_id'], reply_markup=back_button)
    if len(channels) > 0:
        bot.send_message(message.chat.id, text='Выбрать 📋', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, text="У вас нет сохраненных каналов, пожалуйста следуйте указаниям выше или вернитесь в меню и добавьте канал во вкладке 'Редактировать каналы'")


@bot.callback_query_handler(func=lambda call: call.data.startswith('Choose_'))
def handle_enter_text(call):
    channel_id = call.data.split('_')[1]
    status = ['creator', 'administrator']
    text = language_check(str(call.from_user.id))[1]['draw']
    back_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_button.row(text['back_in_menu'])

    try:
        if str(bot.get_chat_member(chat_id=channel_id, user_id=call.from_user.id).status) not in status:
            bot.send_message(text['not_admin'], reply_markup=back_button)
            return ''
        tmp = bot.send_message(channel_id, 'test')
        bot.delete_message(tmp.chat.id, tmp.message_id)
    except:
        bot.send_message(call.from_user.id, text['not_in_chanel'], reply_markup=back_button)
        return ''
    fsm.set_state(call.from_user.id, "writting_text", chanel_id=channel_id, chanel_name=tmp.chat.title)
    bot.send_message(call.from_user.id, text['draw_text'], reply_markup=back_button)

@bot.message_handler(func=lambda message: True and fsm.get_state(message.chat.id)[0] == 'writting_channel_id')
def enter_text(message):
    status = ['creator', 'administrator']
    text = language_check(str(message.chat.id))[1]['draw']
    back_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_button.row(text['back_in_menu'])

    try:
        if str(bot.get_chat_member(chat_id=message.text, user_id=message.from_user.id).status) not in status:
            bot.send_message(text['not_admin'], reply_markup=back_button)
            return ''
        tmp = bot.send_message(message.text, 'test')
        bot.delete_message(tmp.chat.id, tmp.message_id)
    except:
        bot.send_message(message.chat.id, text['not_in_chanel'], reply_markup=back_button)
        return ''
    fsm.set_state(message.chat.id, "writting_text", chanel_id=message.text, chanel_name=tmp.chat.title)
    bot.send_message(message.chat.id, text['draw_text'], reply_markup=back_button)


@bot.message_handler(func=lambda message: True and fsm.get_state(message.chat.id)[0] == 'writting_text')
def enter_photo(message):
    text = language_check(str(message.chat.id))[1]['draw']
    back_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_button.row(text['back_in_menu'])
    tmp = fsm.get_state(message.chat.id)[1]
    fsm.set_state(message.chat.id, "enter_photo", chanel_id=tmp['chanel_id'], chanel_name=tmp['chanel_name'], draw_text=message.text)
    bot.send_message(message.chat.id, text['file'], reply_markup=back_button)


@bot.message_handler(content_types=['text', 'photo', 'document'], func=lambda message: True and fsm.get_state(message.chat.id)[0] == 'enter_photo')
def enter_photo(message):
    file_id = ''
    file_type = ''
    text = language_check(str(message.chat.id))[1]['draw']
    back_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_button.row(text['back_in_menu'])
    tmp = fsm.get_state(message.chat.id)[1]
    if message.content_type == 'photo':
        file_id = message.photo[0].file_id
        file_type = 'photo'
    elif message.content_type == 'document':
        file_id = message.document.file_id
        file_type = 'document'
    else:
        file_id = ''
        file_type = 'text'

    fsm.set_state(message.chat.id, "enter_winers_count", chanel_id=tmp['chanel_id'], chanel_name=tmp['chanel_name'], draw_text=tmp['draw_text'], file_type=file_type, file_id=file_id)
    bot.send_message(message.chat.id, text['winers_count'], reply_markup=back_button)


@bot.message_handler(func=lambda message: True and fsm.get_state(message.chat.id)[0] == 'enter_winers_count')
def enter_winers_count(message):
    text = language_check(str(message.chat.id))[1]['draw']
    try:
        print(int(message.text))
    except:
        bot.send_message(message.chat.id, text['not_int'])
        return 'gg'

    back_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_button.row(text['back_in_menu'])
    tmp = fsm.get_state(message.chat.id)[1]
    fsm.set_state(message.chat.id, "enter_n_posts", chanel_id=tmp['chanel_id'], chanel_name=tmp['chanel_name'], draw_text=tmp['draw_text'],
                  file_type=tmp['file_type'], file_id=tmp['file_id'], winers_count=message.text)

    bot.send_message(message.chat.id, text['n_posts'], reply_markup=back_button)


@bot.message_handler(func=lambda message: True and fsm.get_state(message.chat.id)[0] == 'enter_n_posts')
def enter_n_posts(message):
    text = language_check(str(message.chat.id))[1]['draw']
    try:
        print(int(message.text))
    except:
        bot.send_message(message.chat.id, text['not_int'])
        return 'gg'

    back_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_button.row(text['back_in_menu'])
    tmp = fsm.get_state(message.chat.id)[1]
    fsm.set_state(message.chat.id, "enter_start_time", chanel_id=tmp['chanel_id'], chanel_name=tmp['chanel_name'],
                  draw_text=tmp['draw_text'],
                  file_type=tmp['file_type'], file_id=tmp['file_id'], winers_count=tmp['winers_count'], n_posts=message.text)

    bot.send_message(message.chat.id, text['post_time'], reply_markup=back_button)


@bot.message_handler(func=lambda message: True and fsm.get_state(message.chat.id)[0] == 'enter_start_time')
def enter_start_time(message):
    text = language_check(str(message.chat.id))[1]['draw']
    try:																	# Проверяет правильно ли ввёл время юзер
        print(time.strptime(message.text, '%Y-%m-%d %H:%M'))
    except:
        bot.send_message(message.chat.id, text['invalid_format_time'])
        return 'gg'

    if time.strptime(datetime.now().strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') >= time.strptime(message.text, '%Y-%m-%d %H:%M'):
        bot.send_message(message.chat.id, text['over_time'])
        return 'gg'


    back_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_button.row(text['back_in_menu'])

    tmp = fsm.get_state(message.chat.id)[1]
    fsm.set_state(message.chat.id, "enter_end_time", chanel_id=tmp['chanel_id'], chanel_name=tmp['chanel_name'], draw_text=tmp['draw_text'],
                  file_type=tmp['file_type'], file_id=tmp['file_id'], winers_count=tmp['winers_count'], n_posts=tmp['n_posts'], start_time=message.text)

    bot.send_message(message.chat.id, text['end_time'], reply_markup=back_button)


@bot.message_handler(func=lambda message: True and fsm.get_state(message.chat.id)[0] == 'enter_end_time')
def enter_end_time(message):
    text = language_check(str(message.chat.id))[1]['draw']
    try:
        print(time.strptime(message.text, '%Y-%m-%d %H:%M'))
    except:
        bot.send_message(message.chat.id, text['invalid_format_time'])
        return 'gg'

    tmp = fsm.get_state(message.chat.id)[1]
    if time.strptime(tmp['start_time'], '%Y-%m-%d %H:%M') >= time.strptime(message.text, '%Y-%m-%d %H:%M'):
        bot.send_message(message.chat.id, text['post_biger'])
        return 'gg'

    if time.strptime(datetime.now().strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') >= time.strptime(message.text, '%Y-%m-%d %H:%M'):
        bot.send_message(message.chat.id, text['over_time'])
        return 'gg'

    back_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_button.row(text['back_in_menu'])
    fsm.set_state(message.chat.id, "enter_end_time", chanel_id=tmp['chanel_id'], chanel_name=tmp['chanel_name'], draw_text=tmp['draw_text'], file_type=tmp['file_type'],
                  file_id=tmp['file_id'], winers_count=tmp['winers_count'], n_posts=tmp['n_posts'], start_time=tmp['start_time'], end_time=message.text)
    tmp = fsm.get_state(message.chat.id)[1]
    if tmp['file_type'] == 'photo':
        bot.send_photo(message.chat.id, tmp['file_id'], middleware.create_draw_progress(message.chat.id, tmp), reply_markup=keyboard.get_draw_keyboard(message.chat.id))
    elif tmp['file_type'] == 'document':
        bot.send_document(message.chat.id, tmp['file_id'], caption=middleware.create_draw_progress(message.chat.id, tmp), reply_markup=keyboard.get_draw_keyboard(message.chat.id))
    else:
        bot.send_message(message.chat.id, middleware.create_draw_progress(message.chat.id, tmp), reply_markup=keyboard.get_draw_keyboard(message.chat.id))


@bot.message_handler(func=lambda message: True and middleware.check_post(message.chat.id) != None and message.text == language_check(message.chat.id)[1]['draw']['draw_buttons'][0])
def change_start_time(message):
    text = language_check(str(message.chat.id))[1]['draw']
    fsm.set_state(message.chat.id, 'change_post_time')
    bot.send_message(message.chat.id, text['post_time'], reply_markup=keyboard.back_button(message.chat.id))


@bot.message_handler(func=lambda message: True and fsm.get_state(message.chat.id)[0] == 'change_post_time')
def confirm_change_start_time(message):
    text = language_check(str(message.chat.id))[1]['draw']
    try:																	# Проверяет правильно ли ввёл время юзер
        print(time.strptime(message.text, '%Y-%m-%d %H:%M'))
    except:
        bot.send_message(message.chat.id, text['invalid_format_time'])
        return 'gg'

    if time.strptime(datetime.now().strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') >= time.strptime(message.text, '%Y-%m-%d %H:%M'):
        bot.send_message(message.chat.id, text['over_time'])
        return 'gg'

    tmp = base.get_one(models.DrawProgress, user_id=str(message.chat.id))
    if time.strptime(message.text, '%Y-%m-%d %H:%M') >= time.strptime(tmp.end_time, '%Y-%m-%d %H:%M'):
        bot.send_message(message.chat.id, text['post_biger'])
        return 'gg'

    base.update(models.DrawProgress, {'post_time': message.text}, user_id=str(message.chat.id))
    middleware.send_draw_info(message.chat.id)


@bot.message_handler(func=lambda message: True and middleware.check_post(message.chat.id) != None and message.text == language_check(message.chat.id)[1]['draw']['draw_buttons'][1])
def change_end_time(message):
    text = language_check(str(message.chat.id))[1]['draw']
    fsm.set_state(message.chat.id, 'change_end_time')
    bot.send_message(message.chat.id, text['end_time'], reply_markup=keyboard.back_button(message.chat.id))


@bot.message_handler(func=lambda message: True and fsm.get_state(message.chat.id)[0] == 'change_end_time')
def confirm_change_end_time(message):
    text = language_check(str(message.chat.id))[1]['draw']
    try:
        print(time.strptime(message.text, '%Y-%m-%d %H:%M'))
    except:
        bot.send_message(message.chat.id, text['invalid_format_time'])
        return 'gg'

    if time.strptime(datetime.now().strftime('%Y-%m-%d %H:%M'), '%Y-%m-%d %H:%M') >= time.strptime(message.text, '%Y-%m-%d %H:%M'):
        bot.send_message(message.chat.id, text['over_time'])
        return 'gg'

    tmp = base.get_one(models.DrawProgress, user_id=str(message.chat.id))
    if time.strptime(message.text, '%Y-%m-%d %H:%M') <= time.strptime(tmp.post_time, '%Y-%m-%d %H:%M'):
        bot.send_message(message.chat.id, text['post_biger'])
        return 'gg'

    base.update(models.DrawProgress, {'end_time': message.text}, user_id=str(message.chat.id))
    middleware.send_draw_info(message.chat.id)


@bot.message_handler(func=lambda message: True and middleware.check_post(message.chat.id) != None and message.text == language_check(message.chat.id)[1]['draw']['draw_buttons'][2])
def change_winers_count(message):
    text = language_check(str(message.chat.id))[1]['draw']
    fsm.set_state(message.chat.id, 'change_winers_count')
    bot.send_message(message.chat.id, text['winers_count'], reply_markup=keyboard.back_button(message.chat.id))


@bot.message_handler(func=lambda message: True and fsm.get_state(message.chat.id)[0] == 'change_winers_count')
def confirm_change_wines_count(message):
    try:
        print(int(message.text))
    except:
        bot.send_message(message.chat.id, language_check(message.chat.id)[1]['draw']['not_int'])
        return 'gg'

    base.update(models.DrawProgress, {'winers_count': message.text}, user_id=str(message.chat.id))
    middleware.send_draw_info(message.chat.id)


@bot.message_handler(func=lambda message: True and middleware.check_post(message.chat.id) != None and message.text == language_check(message.chat.id)[1]['draw']['draw_buttons'][3])
def change_text(message):
    text = language_check(str(message.chat.id))[1]['draw']
    fsm.set_state(message.chat.id, 'change_draw_text')
    bot.send_message(message.chat.id, text['draw_text'], reply_markup=keyboard.back_button(message.chat.id))


@bot.message_handler(func=lambda message: True and fsm.get_state(message.chat.id)[0] == 'change_draw_text')
def confirm_change_draw_text(message):
    base.update(models.DrawProgress, {'text': message.text}, user_id=str(message.chat.id))
    middleware.send_draw_info(message.chat.id)


@bot.message_handler(func=lambda message: True and middleware.check_post(message.chat.id) != None and message.text == language_check(message.chat.id)[1]['draw']['draw_buttons'][8])
def change_n_posts(message):
    text = language_check(str(message.chat.id))[1]['draw']
    fsm.set_state(message.chat.id, 'change_n_posts')
    bot.send_message(message.chat.id, text['n_posts'], reply_markup=keyboard.back_button(message.chat.id))


@bot.message_handler(func=lambda message : True and fsm.get_state(message.chat.id)[0] == 'change_n_posts')
def confirm_change_n_posts(message):
    text = language_check(str(message.chat.id))[1]['draw']
    try:
        print(int(message.text))
    except:
        bot.send_message(message.chat.id, text['not_int'])
        return 'gg'
    base.update(models.DrawProgress, {'n_posts': int(message.text)}, user_id=str(message.chat.id))
    middleware.send_draw_info(message.chat.id)


@bot.message_handler(func=lambda message: True and middleware.check_post(message.chat.id) != None and message.text == language_check(message.chat.id)[1]['draw']['draw_buttons'][4])
def change_photo(message):
    text = language_check(str(message.chat.id))[1]['draw']
    fsm.set_state(message.chat.id, 'change_draw_photo')
    bot.send_message(message.chat.id, text['file'], reply_markup=keyboard.back_button(message.chat.id))


@bot.message_handler(content_types=['text', 'photo', 'document'], func=lambda message: True and fsm.get_state(message.chat.id)[0] == 'change_draw_photo')
def confirm_change_draw_photo(message):
    file_id = ''
    file_type = ''
    if message.content_type == 'photo':
        file_id = message.photo[0].file_id
        file_type = 'photo'
    elif message.content_type == 'document':
        file_id = message.document.file_id
        file_type = 'document'
    else:
        file_id = ''
        file_type = 'text'
    base.update(models.DrawProgress, {'file_id': file_id, 'file_type': file_type}, user_id=str(message.chat.id))
    middleware.send_draw_info(message.chat.id)


@bot.message_handler(func=lambda message: True and middleware.check_post(message.chat.id) != None and message.text == language_check(message.chat.id)[1]['draw']['draw_buttons'][5])
def add_chanel(message):
    text = language_check(str(message.chat.id))[1]['draw']
    fsm.set_state(message.chat.id, 'add_check_channel')
    bot.send_message(message.chat.id, text['chanel_id_check'], reply_markup=keyboard.back_button(message.chat.id))


@bot.message_handler(func=lambda message: True and fsm.get_state(message.chat.id)[0] == 'add_check_channel')
def add_check_channel(message):
    text = language_check(str(message.chat.id))[1]['draw']
    try:
        status = ['creator', 'administrator']
        if str(bot.get_chat_member(chat_id=message.text, user_id=message.from_user.id).status) not in status:
            bot.send_message(text['not_admin'])
            return ''
    except:
        bot.send_message(message.chat.id, text['not_in_chanel'])
        return ''
    tmp = base.get_one(models.DrawProgress, user_id=str(message.chat.id))
    base.new(models.SubscribeChannel, tmp.id, str(message.chat.id), message.text)
    middleware.send_draw_info(message.chat.id)
    print(base.select_all(models.SubscribeChannel))


#### кнопка записать видео или перезаписать
@bot.message_handler(content_types=['text', 'video', 'document'], func=lambda message: True and (message.text == language_check(message.chat.id)[1]['menu']['menu_buttons'][3] or message.text == language_check(message.chat.id)[1]["create_video"]["change_button"][1]))
def create_video(message):
    text = language_check(str(message.chat.id))
    back_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_button.row(text[1]['create_video']['back_in_menu'])
    bot.send_message(message.chat.id, language_check(message.chat.id)[1]['create_video']['get_video'], reply_markup=back_button)


@bot.message_handler(content_types=['video'], func=lambda message: True) ### получить и отправить видос в лс
def enter_video(message):
	global FILE_VIDEO_PATH, input_video_path, output_video_path
	
	text = language_check(str(message.chat.id))[1]['draw']
	back_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
	back_button.row(text['back_in_menu'])
	tmp = fsm.get_state(message.chat.id)[1]
	if message.content_type == 'video':
		print("zaebuch")
		#bot.send_message(message.chat.id, "Видео создается")
		file_info = bot.get_file(message.video.file_id)
		video_file = bot.download_file(file_info.file_path)
		input_video_path = f'temp_videos/temp_{message.video.file_id}.mp4'
		output_video_path = f'temp_videos/square_{message.video.file_id}.mp4'
		with open(input_video_path, 'wb') as new_file:
			new_file.write(video_file)
		# middleware.add_watermark(input_video_path, input_video_path, 'cirlce.png')
		# middleware.convert_to_square(input_video_path, output_video_path, message)
		bot.send_message(message.chat.id, language_check(message.chat.id)[1]['create_video']['change_filter'],
						 reply_markup=keyboard.change_filter(message.chat.id))
		FILE_VIDEO_PATH = output_video_path
	
	else:
		print('puzda')
		file_id = ''
		file_type = 'text'
		
@bot.message_handler(content_types=['text'], func=lambda message: True and message.text in language_check(message.chat.id)[1]['create_video']['filter']) ### получить и отправить видос в лс
def enter_video(message):
	global input_video_path, output_video_path
	flag = False
	print("vse zaecich")
	bot.send_message(message.chat.id, "Видео создается")
	if message.text == language_check(message.chat.id)[1]['create_video']['filter'][0]:
		middleware.add_watermark(input_video_path, input_video_path, 'apz.png')
		flag = True
	elif message.text == language_check(message.chat.id)[1]['create_video']['filter'][1]:
		middleware.add_frame(input_video_path, input_video_path, 'apz2.png')
		flag = True
	middleware.convert_to_square(input_video_path, output_video_path, message, flag)
	bot.send_message(message.chat.id, language_check(message.chat.id)[1]['create_video']['change_action'],
	                 reply_markup=keyboard.change_video(message.chat.id))
	


####получить в какой канал отправлять
@bot.message_handler(content_types=['text'], func=lambda message: True and message.text == language_check(message.chat.id)[1]['create_video']['change_button'][0])
def publish_video_get_id(message):
    text = language_check(str(message.chat.id))
    back_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_button.row(text[1]['create_video']['back_in_menu'])
    bot.send_message(message.chat.id, language_check(message.chat.id)[1]['draw']['chanel_id'], reply_markup=back_button)
    markup = telebot.types.InlineKeyboardMarkup()
    channels = [channel.channel_id for channel in base.select_all(models.Channels)]
    for channel in channels:
        # Предполагаем, что `channel` имеет атрибут `name` для отображения имени канала
        button = telebot.types.InlineKeyboardButton(text=channel, callback_data=f'Chooseone_{channel}')
        markup.add(button)
    if len(channels) > 0:
        bot.send_message(message.chat.id, text='Выбрать 📋', reply_markup=markup)
    else:
        bot.send_message(message.chat.id,
                         text="У вас нет сохраненных каналов, пожалуйста следуйте указаниям выше или вернитесь в меню и добавьте канал во вкладке 'Редактировать каналы'")
    fsm.set_state(message.chat.id, 'publish_video')


@bot.callback_query_handler(func=lambda call: call.data.startswith('Chooseone_'))
def publish_video(call):
    channel_id = call.data.split('_')[1]
    text = language_check(str(call.from_user.id))
    with open(str(FILE_VIDEO_PATH).replace("temp_videos/", "temp_videos/1"), "rb") as video:
        bot.send_video_note(channel_id, video)
    bot.send_message(call.from_user.id, language_check(call.from_user.id)[1]['menu']['welcome_text'],
                     reply_markup=keyboard.get_menu_keyboard(call.from_user.id))
    middleware.delete_files_in_folder('temp_videos')

####публикация видео в канале
@bot.message_handler(content_types=['text'], func=lambda message: True and fsm.get_state(message.chat.id)[0] == 'publish_video')
def publish_video(message):
    text = language_check(str(message.chat.id))
    with open(str(FILE_VIDEO_PATH).replace("temp_videos/", "temp_videos/1"), "rb") as video:
        bot.send_video_note(message.text, video)
    bot.send_message(message.chat.id, language_check(message.chat.id)[1]['menu']['welcome_text'],
                     reply_markup=keyboard.get_menu_keyboard(message.chat.id))
    middleware.delete_files_in_folder('temp_videos')


if __name__ == '__main__':
    bot.polling(none_stop=True)

