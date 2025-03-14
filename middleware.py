import queue
import time
import traceback

import models
import random
import threading
import keyboard
import config
import asyncio
from tool import language_check, create_inlineKeyboard
from app import middleware_base, bot, post_base, end_base
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from telethon import TelegramClient
from telethon.tl.types import PeerChannel

from moviepy.editor import *
from moviepy.video.fx import crop


def check_user(user_id):
    user = middleware_base.get_one(models.User, user_id=str(user_id))
    if user != None:
        return user
    else:
        return False


def create_draw_progress(user_id, tmp):
    middleware_base.delete(models.DrawProgress, user_id=(str(user_id)))
    middleware_base.new(models.DrawProgress, str(user_id), tmp['chanel_id'], tmp['chanel_name'], tmp['draw_text'], tmp['file_type'], tmp['file_id'], int(tmp['winers_count']), int(tmp['n_posts']),tmp['start_time'], tmp['end_time'])
    middleware_base.delete(models.State, user_id=str(user_id))

    return draw_info(user_id)


def draw_info(user_id):
    tmp = check_post(str(user_id))
    print("tmp", tmp)
    text = language_check(user_id)[1]['draw']
    draw_text = f"{text['change_text']}\n{text['post_time_text']} {tmp.post_time}\n{text['over_time_text']} {tmp.end_time}\n{text['chanel/chat']} {tmp.chanel_name}\n{text['count_text']} {tmp.winers_count}\n{text['posts_text']} {tmp.n_posts}\n{text['text']} {tmp.text}"
    return draw_text


def check_post(user_id):
    data = middleware_base.get_one(models.DrawProgress, user_id=str(user_id))
    return data


def send_draw_info(user_id):
    tmp = check_post(str(user_id))
    text = language_check(user_id)[1]['draw']
    draw_text = f"{text['change_text']}\n{text['post_time_text']} {tmp.post_time}\n{text['over_time_text']} {tmp.end_time}\n{text['chanel/chat']} {tmp.chanel_name}\n{text['count_text']} {tmp.winers_count}\n{text['posts_text']} {tmp.n_posts}\n{text['text']} {tmp.text}"
    if tmp.file_type == 'photo':
        bot.send_photo(user_id, tmp.file_id, draw_text, reply_markup=keyboard.get_draw_keyboard(user_id))
    if tmp.file_type == 'document':
        bot.send_document(user_id, tmp.file_id, caption=draw_text, reply_markup=keyboard.get_draw_keyboard(user_id))
    else:
        bot.send_message(user_id, draw_text, reply_markup=keyboard.get_draw_keyboard(user_id))
    middleware_base.delete(models.State, user_id=user_id)



def my_draw_info(user_id, row=0):
    if row < 0:
        return 'first'

    text = language_check(user_id)[1]['my_draw']
    notposted = middleware_base.select_all(models.DrawNot, user_id=str(user_id))
    posted = middleware_base.select_all(models.Draw, user_id=str(user_id))
    all_draws = notposted + posted
    if len(all_draws) == 0:
        bot.send_message(user_id, text['no_draw'])

    if row >= len(all_draws):
        print('notttt')



    draw_text = f"{text['your_draw']}\n{text['post_time_text']} {all_draws[row].post_time}\n{text['over_time_text']} {all_draws[row].end_time}\n{text['chanel/chat']} {all_draws[row].chanel_name}\n{text['count_text']} {all_draws[row].winers_count}\n{text['text']} {all_draws[row].text}"
    keyboard = create_inlineKeyboard({text['back']: "back", text['next']: "next"}, 2)
    if all_draws[row].file_type == 'photo':
        bot.send_photo(user_id, all_draws[row].file_id, draw_text, reply_markup=keyboard)
    elif all_draws[row].file_type == 'document':
        bot.send_document(user_id, all_draws[row].file_id, caption=draw_text, reply_markup=keyboard)
    else:
        bot.send_message(user_id, draw_text, reply_markup=keyboard)





def start_draw_timer():
    def timer():
        while 1:
            for i in post_base.select_all(models.DrawNot):

                count = 0
                post_time = datetime.now().strftime('%Y-%m-%d %H:%M')
                post_time = time.strptime(post_time, '%Y-%m-%d %H:%M')
                if post_time >= time.strptime(i.post_time, '%Y-%m-%d %H:%M'):
                    if i.file_type == 'photo':
                        tmz = bot.send_photo(i.chanel_id, i.file_id, i.text, reply_markup=create_inlineKeyboard({language_check(i.user_id)[1]['draw']['get_on']:f'geton_{i.id}'}))
                    elif i.file_type == 'document':
                        tmz = bot.send_document(i.chanel_id, i.file_id, caption=i.text, reply_markup=create_inlineKeyboard({language_check(i.user_id)[1]['draw']['get_on']:f'geton_{i.id}'}))
                    else:
                        tmz = bot.send_message(i.chanel_id, i.text, reply_markup=create_inlineKeyboard({language_check(i.user_id)[1]['draw']['get_on']:f'geton_{i.id}'}))
                    post_base.new(models.Draw, i.id, i.user_id, tmz.message_id, i.chanel_id, i.chanel_name, i.text, i.file_type, i.file_id, i.winers_count, i.n_posts, i.post_time, i.end_time)
                    post_base.delete(models.DrawNot, id=str(i.id))
            time.sleep(5)
    rT = threading.Thread(target = timer)
    rT.start()


def end_draw_timer():
    def end_timer():
        while 1:
            for i in end_base.select_all(models.Draw):
                count = 0
                post_time = datetime.now().strftime('%Y-%m-%d %H:%M')
                post_time = time.strptime(post_time, '%Y-%m-%d %H:%M')
                if post_time >= time.strptime(i.end_time, '%Y-%m-%d %H:%M'):
                    text = language_check(i.user_id)[1]['draw']
                    players = end_base.select_all(models.DrawPlayer, draw_id=str(i.id))
                    if players == []:
                        winers = f"{i.text}\n*****\n{text['no_winers']}"
                        owin = f"{text['no_winers']}"
                    else:
                        winers = f"{i.text}\n*****\n{text['winers']}\n"
                        owin = f"{text['winers']}\n"
                        winners = list()
                        for x in range(int(i.winers_count)):
                            if count >= len(players):
                                break
                            random_player = random.choice(players)
                            winners.append(random_player.user_name)
                            bot.send_message(random_player.user_id, text="Поздравляем!🎉 Ты стал победителем в конкурсе в канале " + i.chanel_id)
                            winers += f"<a href='tg://user?id={random_player.user_id}'>{random_player.user_name}</a>\n"
                            owin += f"<a href='tg://user?id={random_player.user_id}'>{random_player.user_name}</a>\n"
                            count += 1
                    try:
                        bot.send_message(chat_id=str(i.chanel_id), text=winers, parse_mode='HTML')
                    except:
                        end_base.delete(models.Draw, id = i.id)
                        bot.send_message(i.chanel_id, text['failed_post'])
                        return 'gg'
                    with open('winners.txt', 'w', encoding='utf-8') as file:
                        for winner in winners:
                            file.write('@' + winner)
                    with open('winners.txt', 'rb') as f:
                        bot.send_document(i.user_id, f)
                    bot.send_message(i.user_id, f"{text['your_draw_over']}\n{owin}", parse_mode='HTML')
                    end_base.delete(models.Draw, id = i.id)
                    time.sleep(1)

            time.sleep(5)
    rT = threading.Thread(target = end_timer)
    rT.start()


async def check_reactions(user_id, n_posts):
    try:
        async with TelegramClient('new5', config.api_id, config.api_hash) as client:
            print("Connected successfully")
            entity = await client.get_entity('t.me/hallomememe')
            total_reactions = 0
            print("get_entity")
            async for message in client.iter_messages(entity, limit=n_posts):
                print("post checked")
                if message.reactions:
                    reactions = message.reactions
                    for reaction in reactions.results:
                        if reaction.user_id == user_id:
                            total_reactions += 1
            print("messages checked")
            return total_reactions
    except Exception as e:
        print("Traceback with code: ", e)


def new_player(call):
    id = int(call.data.split('_')[1])
    print(call.data.split('_'))
    tmp = middleware_base.get_one(models.Draw, id=id)
    try:
        chanel = middleware_base.select_all(models.SubscribeChannel, draw_id=tmp.id)
        status = ['left', 'kicked', 'restricted', 'member', 'admin', 'creator']
        for i in chanel:
            if bot.get_chat_member(chat_id=i.channel_id, user_id=call.from_user.id).status in status:
                return 'not_subscribe'
    except:
        pass

    players = middleware_base.get_one(models.DrawPlayer, draw_id=str(tmp.id), user_id=str(call.from_user.id))
    if players is None:
        # total_reactions = asyncio.run(check_reactions(call.from_user.id, tmp.n_posts))
        # print("User reacted: ", total_reactions)
        # if total_reactions < tmp.n_posts:
        #     print('error')
        #     return 'n_posts_error'
        middleware_base.new(models.DrawPlayer, tmp.id, str(call.from_user.id), str(call.from_user.username))
        tmz = middleware_base.select_all(models.DrawPlayer, draw_id=tmp.id)
        return len(tmz), language_check(tmp.user_id)[1]['draw']['play']
    else:
        print('bool')
        return False


def convert_to_square(input_video_path, output_video_path, message):
    # Prеобразование видео в видеокружок
    input_video = VideoFileClip(f"{input_video_path}")

    w, h = input_video.size
    circle_size = 360
    aspect_ratio = float(w) / float(h)

    if w > h:
        new_w = int(circle_size * aspect_ratio)
        new_h = circle_size
    else:
        new_w = circle_size
        new_h = int(circle_size / aspect_ratio)

    resized_video = input_video.resize((new_w, new_h))
    output_video = resized_video.crop(x_center=resized_video.w / 2, y_center=resized_video.h / 2, width=circle_size,
                                      height=circle_size)
    output_video.write_videofile(f"{output_video_path}", codec="libx264", audio_codec="aac", bitrate="5M")

    with open(f"{output_video_path}", "rb") as video:
        bot.send_video_note(message.chat.id, video)


def process_video(input_path, output_path):
    # Загружаем видео
    video = VideoFileClip(input_path)

    # Обрезаем видео до квадратного формата
    (w, h) = video.size
    min_side = min(w, h)
    cropped_video = crop(video, width=min_side, height=min_side, x_center=w/2, y_center=h/2)

    # Уменьшаем длительность до 60 секунд (если нужно)
    if cropped_video.duration > 60:
        cropped_video = cropped_video.subclip(0, 60)

    # Сохраняем обработанное видео
    cropped_video.write_videofile(output_path, codec='libx264')

    # Закрываем видео
    video.close()
    cropped_video.close()



def delete_files_in_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f'Ошибка при удалении файла {file_path}. {e}')


