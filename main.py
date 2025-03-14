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


@bot.message_handler(func=lambda message: True and message.text == language_check(message.chat.id)[1]['draw']['back_in_menu'])
def back_in_menu(message):
    base.delete(models.State, user_id=str(message.chat.id))
    base.delete(models.DrawProgress, user_id=(str(message.chat.id)))
    base.delete(models.SubscribeChannel, user_id=(str(message.chat.id)))
    bot.send_message(message.chat.id, language_check(message.chat.id)[1]['menu']['welcome_text'], reply_markup=keyboard.get_menu_keyboard(message.chat.id))


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
    fsm.set_state(message.chat.id, "writting_channel_id")
    bot.send_message(message.chat.id, text['chanel_id'], reply_markup=back_button)


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
    global FILE_VIDEO_PATH
    middleware.delete_files_in_folder('temp_videos')
    file_id = ''
    file_type = ''
    text = language_check(str(message.chat.id))[1]['draw']
    back_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_button.row(text['back_in_menu'])
    tmp = fsm.get_state(message.chat.id)[1]
    if message.content_type == 'video':
        print("zaebuch")
        bot.send_message(message.chat.id, "Видео создается")
        file_info = bot.get_file(message.video.file_id)
        video_file = bot.download_file(file_info.file_path)
        input_video_path = f'temp_videos/temp_{message.video.file_id}.mp4'
        output_video_path = f'temp_videos/square_{message.video.file_id}.mp4'
        with open(input_video_path, 'wb') as new_file:
            new_file.write(video_file)
        #add_watermark(input_video_path, input_video_path, 'apz.png')
        middleware.convert_to_square(input_video_path, output_video_path, message)
        bot.send_message(message.chat.id, language_check(message.chat.id)[1]['create_video']['change_action'],
                         reply_markup=keyboard.change_video(message.chat.id))
        os.remove(input_video_path)
        FILE_VIDEO_PATH = output_video_path
        #os.remove(output_video_path)
    else:
        print('puzda')
        file_id = ''
        file_type = 'text'

####получить в какой канал отправлять
@bot.message_handler(content_types=['text'], func=lambda message: True and message.text == language_check(message.chat.id)[1]['create_video']['change_button'][0])
def publish_video_get_id(message):
    text = language_check(str(message.chat.id))
    back_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_button.row(text[1]['create_video']['back_in_menu'])
    bot.send_message(message.chat.id, language_check(message.chat.id)[1]['draw']['chanel_id'], reply_markup=back_button)
    fsm.set_state(message.chat.id, 'publish_video')


####публикация видео в канале
@bot.message_handler(content_types=['text'], func=lambda message: True and fsm.get_state(message.chat.id)[0] == 'publish_video')
def publish_video(message):
    text = language_check(str(message.chat.id))
    print(message.text)
    print(FILE_VIDEO_PATH)
    with open(f"{FILE_VIDEO_PATH}", "rb") as video:
        bot.send_video_note(message.text, video)
    os.remove(f"{FILE_VIDEO_PATH}")
    bot.send_message(message.chat.id, language_check(message.chat.id)[1]['menu']['welcome_text'],
                     reply_markup=keyboard.get_menu_keyboard(message.chat.id))


if __name__ == '__main__':
    bot.polling(none_stop=True)

'''
# Fetch reactions for the media message
    chat_member = bot.get_chat_member(chat_id=message1.chat.id, user_id=bot.id)
    reactions = chat_member.get('user', {}).get('is_bot') and bot.get_chat_member(chat_id=message.chat.id, user_id=user_id).get('user').get('is_bot')
    if reactions:
        reaction_count = len([reaction for reaction in reactions if reaction.get('user', {}).get('is_bot') == False and reaction['type'] in ['like', 'dislike']])
        user_collection.update_one({'user_id': user_id}, {'$inc': {'likes_count': reaction_count}})
            
        # Update reactions in the database
        for reaction in reactions:
            if reaction.get('user', {}).get('is_bot'):
                continue
            reaction_user_id = reaction['user']['id']
            if reaction['type'] == 'like':
                user_collection.update_one({'user_id': reaction_user_id}, {'$inc': {'likes_count': 1}})
            elif reaction['type'] == 'dislike':
                user_collection.update_one({'user_id': reaction_user_id}, {'$inc': {'dislikes_count': 1}})

  
'''
