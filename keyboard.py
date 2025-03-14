import telebot
import base
import models
from tool import language_check

def get_menu_keyboard(user_id):
	buttons = language_check(user_id)[1]['menu']['menu_buttons']
	menu_keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
	menu_keyboard.row(buttons[0], buttons[1])
	menu_keyboard.row(buttons[2], buttons[3], buttons[-1])
	return menu_keyboard


def get_draw_keyboard(user_id):
	buttons = language_check(user_id)[1]['draw']['draw_buttons']
	draw_keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
	draw_keyboard.row(buttons[0], buttons[1])
	draw_keyboard.row(buttons[2], buttons[3])
	draw_keyboard.row(buttons[4], buttons[5])
	draw_keyboard.row(buttons[6], buttons[8])
	draw_keyboard.row(buttons[7])
	return draw_keyboard
	

def back_button(user_id):
	buttons = language_check(user_id)[1]['draw']['back']
	back_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
	back_button.row(buttons)
	return back_button


def change_video(user_id):
	buttons = language_check(user_id)[1]['create_video']['change_button']
	change_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
	change_button.row(buttons[0], buttons[1])
	change_button.row(buttons[2])
	return change_button


def channel_buttons(user_id):
	buttons = language_check(user_id)[1]['menu']['channels_menu']
	channel_buttons = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
	channel_buttons.row(buttons[0], buttons[1])
	channel_buttons.row(language_check(user_id)[1]['draw']['back_in_menu'])
	return channel_buttons


def change_filter(user_id):
	buttons = language_check(user_id)[1]['create_video']['filter']
	change_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
	change_button.row(buttons[0], buttons[1])
	change_button.row(buttons[2])
	return change_button


