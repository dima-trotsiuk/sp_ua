import mysql.connector
from mysql.connector import Error
import telebot
from telebot import types
from loguru import logger
from pylab import rcParams
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

bot = telebot.TeleBot('1477439147:AAGFkVgkny6xw7T9zPbZjvIbavnJLnpofF4', parse_mode=None)
logger.add("logger.log", format="{time} | {level} | {message}",
           level="DEBUG", rotation="100 KB", compression="zip")

# Начало
'''
Глобальные функции
'''


# Начало

def spam_check(call, message=True):
    if message:
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            bot.send_message(call.message.chat.id, "😏😏😏")
    else:
        try:
            bot.delete_message(call.chat.id, call.message_id + 1)
        except:
            bot.send_message(call.chat.id, "😏😏😏")


def connection_func():
    try:
        conn = mysql.connector.connect(host='localhost',
                                       database='sp_ua_test',
                                       user='root',
                                       password='admin')
        return conn
    except Error as e:
        logger.error(f"Помилка в connection_func: {e}")


def admins_info(message):
    conn = connection_func()
    cursor = conn.cursor()
    cursor.execute(
        f"select title from categories where id = (select category_id from admins where id = '{message.chat.id}');")
    category_tuple = cursor.fetchone()
    category = category_tuple[0]

    cursor.execute(f"select who_change from admins where id = {message.chat.id};")
    who_change_tuple = cursor.fetchone()
    who_change = who_change_tuple[0]

    cursor.execute(f"select item_id from admins where id = {message.chat.id};")
    who_change_tuple = cursor.fetchone()
    item_id = who_change_tuple[0]

    conn.close()
    cursor.close()
    return [category, who_change, item_id]


# повертає admin_name останнього замовленя
def admin_name_last_order():
    conn = connection_func()
    cursor = conn.cursor()
    last_id = last_id_orders()
    cursor.execute(
        f'select admin_name from orders where id = {last_id}')
    admin_name = cursor.fetchone()
    admin_name = admin_name[0]
    conn.close()
    cursor.close()
    return admin_name


def last_id_orders():
    conn = connection_func()
    cursor = conn.cursor()
    cursor.execute(f'select id from orders order by id desc limit 1;')
    last_id = cursor.fetchone()
    last_id = last_id[0]
    conn.close()
    cursor.close()
    return last_id


# Конец
'''
Глобальные функции
'''


# Конец


@bot.message_handler(commands=['start'])
def welcome(message):
    keyboard_schedule = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Склад Дімона")
    item2 = types.KeyboardButton("Склад Владоса")
    item3 = types.KeyboardButton("Редагувати склад")
    item4 = types.KeyboardButton("Full склад")
    item5 = types.KeyboardButton("Управління замовленнями")
    item6 = types.KeyboardButton("Пошук по ТТН")
    item7 = types.KeyboardButton("Статистика за місяць")
    keyboard_schedule.add(item1, item2, item3, item4, item5, item6, item7)

    conn = connection_func()
    query = f"select id from admins where id = {message.from_user.id}"
    cursor = conn.cursor()
    cursor.execute(query)

    if cursor.fetchone() is None:
        bot.send_message(message.from_user.id, f"Простим смертним вхід заборонений🪓")
    else:
        bot.send_message(message.from_user.id,
                         "Ну шо, аніме?",
                         reply_markup=keyboard_schedule)
    conn.close()
    cursor.close()


# Начало
'''
Склад Дімона & Склад Владоса
'''


# Начало


@bot.message_handler(func=lambda message: message.text == 'Склад Дімона' or message.text == 'Склад Владоса')
def get_storage_text(message):
    arr = message.text.split(" ")
    if arr[1] == "Дімона":
        storage = get_storage('dima')
    else:
        storage = get_storage('vlad')

    if storage == -1:
        bot.send_message(message.from_user.id, f"Помилка в запросі в БД")
    else:
        bot.send_message(message.from_user.id, storage)


# Запиує в rows склад
def get_storage(kto):
    conn = connection_func()
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * FROM categories")
        rows = cursor.fetchall()
        full_storage = ''
        for category in rows:
            full_storage += f"\n{category[1]}\n\n"
            cursor.execute(f"SELECT * FROM {category[2]}_{kto}")
            list_product = cursor.fetchall()
            full_storage += print_storage(list_product, category[2])
        return full_storage
    except Error as e:
        logger.error(f"Помилка в get_storage: {e}")
        return -1
    finally:
        conn.close()
        cursor.close()


# Виводить склад
def print_storage(storage, cat):
    try:
        full_storage = ''
        if cat == 'stickers':
            for el in storage:
                full_storage += f'{el[0]:02}. "{el[1]}" - '
                if el[2] == 0:
                    full_storage += f'0'
                else:
                    if el[2] % el[3] == 0:
                        full_storage += f'{el[2] / el[3] :.0f}x{el[3]}'
                    else:
                        full_storage += f'{el[2] // el[3]}x{el[3]} {el[2] % el[3]}'
                full_storage += '\n'
            return full_storage
        else:
            for el in storage:
                full_storage += f'{el[0]:02}. "{el[1]}" - {el[2]}\n'
            return full_storage
    except Error as e:
        logger.error(f"Помилка в print_storage: {e}")


# Конец
'''
Склад Дімона & Склад Владоса
'''
# Конец


# Начало
'''
Редагувати склад
'''


# Начало


@bot.message_handler(func=lambda message: message.text == 'Редагувати склад')
def change(message):
    change_storage = types.InlineKeyboardMarkup(row_width=3)
    change_dima = types.InlineKeyboardButton("Дімона", callback_data="user_dima")
    change_vlad = types.InlineKeyboardButton("Владоса", callback_data="user_vlad")
    change_storage.add(change_dima, change_vlad)
    bot.send_message(message.from_user.id, 'Чий склад ти хочеш редагувати?', reply_markup=change_storage)


@bot.callback_query_handler(func=lambda call: "user" in call.data)
def change_call(call):
    conn = connection_func()
    cursor = conn.cursor()
    try:
        if call.data == "user_dima":
            cursor.execute(f"update admins set who_change = 'dima' where id = {call.message.chat.id};")
            conn.commit()
            change_choose_cat(call)
        elif call.data == "user_vlad":
            cursor.execute(f"update admins set who_change = 'vlad' where id = {call.message.chat.id};")
            conn.commit()
            change_choose_cat(call)
        spam_check(call)
    except Error as e:
        logger.error(f"Помилка в change_call {e}")
    finally:
        conn.close()
        cursor.close()


def change_choose_cat(call):
    cat = types.InlineKeyboardMarkup(row_width=3)
    cat1 = types.InlineKeyboardButton("Стікери", callback_data="category_stickers")
    cat2 = types.InlineKeyboardButton("Постери", callback_data="category_posters")
    cat3 = types.InlineKeyboardButton("Лампи", callback_data="category_lamps")
    cat.add(cat1, cat2, cat3)
    bot.send_message(call.message.chat.id, 'Категорія?', reply_markup=cat)


@bot.callback_query_handler(func=lambda call: "category" in call.data)
def change_choose_cat_call(call):
    conn = connection_func()
    cursor = conn.cursor()
    try:
        cat_dir = {"stickers": 1, "posters": 2, "lamps": 3}
        arr = call.data.split("_")
        cursor.execute(f"update admins set category_id = {cat_dir[arr[1]]} where id = {call.message.chat.id};")
        conn.commit()

    except Error as e:
        logger.error(f"Помилка в change_choose_cat_call: {e}")
    finally:
        conn.close()
        cursor.close()
        change_menu(call)
        spam_check(call)


def change_menu(call):
    conn = connection_func()
    cursor = conn.cursor()
    try:
        category_and_who = admins_info(call.message)
        category = category_and_who[0]
        who_change = category_and_who[1]

        cursor.execute(f"select * from {category}_{who_change}")

        storage = cursor.fetchall()

        all_order = types.InlineKeyboardMarkup(row_width=3)
        if category == "stickers":
            for el in storage:  # (1, 'Рандом 1', 200, 100, 0)
                full_storage = ''
                full_storage += f'{el[0]}. "{el[1]}" - '
                if el[2] == 0:
                    full_storage += f'0'
                else:
                    if el[2] % el[3] == 0:
                        full_storage += f'{el[2] / el[3] :.0f}x{el[3]}'
                    else:
                        full_storage += f'{el[2] // el[3]}x{el[3]} {el[2] % el[3]}'
                full_storage += '\n'
                order = types.InlineKeyboardButton(f"{full_storage}",
                                                   callback_data=f'change_{el[0]}')
                all_order.add(order)
        else:
            for el in storage:
                full_storage = ''
                full_storage += f'{el[0]}. "{el[1]}" - {el[2]}'
                order = types.InlineKeyboardButton(f"{full_storage}",
                                                   callback_data=f'change_{el[0]}')
                all_order.add(order)
        order = types.InlineKeyboardButton(f"+", callback_data=f'change_new')
        all_order.add(order)
        bot.send_message(call.message.chat.id, "Склад:", reply_markup=all_order)

    except Error as e:
        logger.error(f"Помилка в change_menu {e}")
    finally:
        conn.close()
        cursor.close()


@bot.callback_query_handler(func=lambda call: "change" in call.data)
def change_menu_call(call):
    info_from_admins = admins_info(call.message)
    category = info_from_admins[0]

    arr = call.data.split("_")
    if arr[1] == 'new':
        sent = bot.send_message(call.message.chat.id, f"Назва?")

        bot.register_next_step_handler(sent, new_product)
    else:
        id_arr = arr[1]

        conn = connection_func()
        cursor = conn.cursor()
        cursor.execute(f"update admins set item_id = {id_arr} where id = {call.message.chat.id};")
        conn.commit()
        conn.close()
        cursor.close()

        info = get_quantity(call)  # (26, 'Знаки', 0, 50, 0)
        if info == -1:
            bot.send_message(call.message.chat.id, "Помилка в запросі в БД")
        elif info == 0:
            pass
        else:
            change_order = types.InlineKeyboardMarkup(row_width=3)
            if category == 'stickers':
                change_plus = types.InlineKeyboardButton(f'+{25 if info[3] % 25 == 0 else info[3]}',
                                                         callback_data=f"plus_{id_arr}_{info[2]}_{25 if info[3] % 25 == 0 else info[3]}")
                change_x = types.InlineKeyboardButton('Власне значення', callback_data=f"xxx_{id_arr}")
                change_minus = types.InlineKeyboardButton(f'-{25 if info[3] % 25 == 0 else info[3]}',
                                                          callback_data=f"minus_{id_arr}_{info[2]}_{25 if info[3] % 25 == 0 else info[3]}")
            else:
                change_plus = types.InlineKeyboardButton('+1', callback_data=f"plus_{id_arr}_{info[2]}_{1}")
                change_x = types.InlineKeyboardButton('Власне значення', callback_data=f"xxx_{id_arr}")
                change_minus = types.InlineKeyboardButton('-1', callback_data=f"minus_{id_arr}_{info[2]}_{1}")

            close = types.InlineKeyboardButton('Закрити', callback_data=f"close")

            change_order.add(change_plus, change_x, change_minus, close)

            bot.send_message(call.message.chat.id, f'{info[0]}. "{info[1]}" кількість - {info[2]}',
                             reply_markup=change_order)


def get_quantity(call):
    info = admins_info(call.message)
    category = info[0]
    who_change_storage = info[1]
    id = info[2]
    if connection_func() == -1:
        bot.send_message(call.message.chat.id, f"Невдале підключення до БД")
        return 0
    else:
        conn = connection_func()
        cursor = conn.cursor()
        try:
            cursor.execute(f"SELECT * FROM {category}_{who_change_storage} where id = {id}")
            rows = cursor.fetchone()

            return rows
        except Error as e:
            logger.error(f"Помилка в get_quantity: {e}")
            return -1
        finally:
            conn.close()
            cursor.close()


title = ''


def new_product(message):
    info = admins_info(message)
    category = info[0]
    global title
    title = message.text
    logger.debug(title)

    if category == 'stickers':
        sent = bot.send_message(message.chat.id, f"Стікерів в паці?")
        bot.register_next_step_handler(sent, new_product_stickers)
    else:
        conn = connection_func()
        cursor = conn.cursor()
        try:
            query = f"insert into {category}_all (name) values ('{title}')"
            cursor.execute(query)
            conn.commit()
            query = f"insert into {category}_dima set name = " \
                    f"(select name from {category}_all where id_{category} = " \
                    f"(select id_{category} from {category}_all order by id_{category} desc limit 1));"
            cursor.execute(query)
            conn.commit()
            query = f"insert into {category}_vlad set name = " \
                    f"(select name from {category}_all where id_{category} = " \
                    f"(select id_{category} from {category}_all order by id_{category} desc limit 1));"
            cursor.execute(query)
            conn.commit()

            bot.send_message(message.from_user.id, "Зміни збрежено")
        except Error as e:
            logger.error(f"Помилка в new_product {e}")
        finally:
            conn.close()
            cursor.close()


def new_product_stickers(message):
    global title
    conn = connection_func()
    cursor = conn.cursor()
    try:
        if message.text.isdigit():
            query = f"insert into stickers_dima (name, quantity_in_pack) values ('{title}', {int(message.text)})"
            cursor.execute(query)
            conn.commit()
            query = f"insert into stickers_vlad (name, quantity_in_pack) values ('{title}', {int(message.text)})"
            cursor.execute(query)
            conn.commit()
            query = f"insert into stickers_all set name = (select name from stickers_dima where id = " \
                    f"(select id from stickers_dima order by id desc limit 1));"
            cursor.execute(query)
            conn.commit()

            bot.send_message(message.from_user.id, "Зміни збрежено")
        else:
            conn.close()
            cursor.close()
            sent = bot.send_message(message.chat.id, f"Число будь-ласка")
            bot.register_next_step_handler(sent, new_product_stickers)
    except Error as e:
        logger.error(f"Помилка в new_product_stickers {e}")
    finally:
        conn.close()
        cursor.close()


@bot.callback_query_handler(func=lambda call: "plus" in call.data)
def plus(call):
    info = admins_info(call.message)
    category = info[0]
    who_change_storage = info[1]
    arr = call.data.split("_")
    id_arr = arr[1]
    plus_value = int(arr[3])
    conn = connection_func()
    cursor = conn.cursor()
    try:
        query = f"update {category}_{who_change_storage} set quantity = quantity + {plus_value} where id = {id_arr}"
        cursor.execute(query)
        conn.commit()
        # оновлення товару в stickers_all
        if category == 'stickers':
            query = "update stickers_all set " \
                    "quantity = ((select quantity div quantity_in_pack from stickers_dima where id = stickers_all.id_stickers) + " \
                    "(select quantity div quantity_in_pack from stickers_vlad where id = stickers_all.id_stickers)) " \
                    f"where id_stickers = {id_arr};"
            cursor.execute(query)
            conn.commit()
        else:
            query = f"update {category}_all set quantity = ((select quantity from {category}_dima where id = {category}_all.id_{category}) + " \
                    f"(select quantity from {category}_vlad where id = {category}_all.id_{category}))" \
                    f"where id_{category} = {id_arr};"
            cursor.execute(query)
            conn.commit()

        spam_check(call)
        change_menu_call(call)
    except Error as e:
        logger.error(f"Помилка в plus: {e}")
        bot.send_message(call.message.chat.id, "Помилка в запросі в БД")
    finally:
        conn.close()
        cursor.close()


@bot.callback_query_handler(func=lambda call: "minus" in call.data)
def minus(call):
    info = admins_info(call.message)
    category = info[0]
    who_change_storage = info[1]

    arr = call.data.split("_")
    id_arr = arr[1]
    plus_value = int(arr[3])
    conn = connection_func()
    cursor = conn.cursor()
    try:
        query = f"select quantity from {category}_{who_change_storage} where id = {id_arr}"
        cursor.execute(query)
        row = cursor.fetchone()
        quantity = row[0]
        if quantity < plus_value:
            bot.send_message(call.message.chat.id, f'Незя відняти {plus_value}')
        else:
            quantity -= plus_value
            query = f"update {category}_{who_change_storage} set quantity = quantity - {plus_value} where id = {id_arr}"
            cursor.execute(query)
            conn.commit()
            # оновлення товару в stickers_all
            if category == 'stickers':
                query = "update stickers_all set " \
                        "quantity = ((select quantity div quantity_in_pack from stickers_dima where id = stickers_all.id_stickers) + " \
                        "(select quantity div quantity_in_pack from stickers_vlad where id = stickers_all.id_stickers)) " \
                        f"where id_stickers = {id_arr};"
                cursor.execute(query)
                conn.commit()
            else:
                query = f"update {category}_all set quantity = ((select quantity from {category}_dima where id = {category}_all.id_{category}) + " \
                        f"(select quantity from {category}_vlad where id = {category}_all.id_{category}))" \
                        f"where id_{category} = {id_arr};"
                cursor.execute(query)
                conn.commit()
            spam_check(call)
            change_menu_call(call)
    except Error as e:
        logger.error(f"Помилка в plus: {e}")
        bot.send_message(call.message.chat.id, "Помилка в запросі в БД")
    finally:
        conn.close()
        cursor.close()


@bot.callback_query_handler(func=lambda call: "close" in call.data)
def close(call):
    spam_check(call)


@bot.callback_query_handler(func=lambda call: "xxx" in call.data)
def xxx(call):
    try:
        arr = call.data.split("_")
        id_arr = arr[1]
        conn = connection_func()
        cursor = conn.cursor()
        cursor.execute(f"update admins set item_id = {id_arr} where id = {call.message.chat.id};")
        conn.commit()
        sent = bot.send_message(call.message.chat.id, f"Нова кількість? (Напиши -1 для виходу)")
        bot.register_next_step_handler(sent, new_quantity)
    except Error as e:
        logger.error(f"Помилка в xxx: {e}")
        bot.send_message(call.message.chat.id, "Помилка в запросі в БД")


def new_quantity(message):
    info = admins_info(message)
    category = info[0]
    who_change_storage = info[1]
    id = info[2]

    conn = connection_func()
    cursor = conn.cursor()
    try:
        int(message.text)
        if int(message.text) == -1:
            bot.send_message(message.chat.id, f"👌")
        elif int(message.text) < 0:
            sent = bot.send_message(message.chat.id, f"Мінусові значення не можна задавати")
            bot.register_next_step_handler(sent, new_quantity)
        else:
            query = f"update {category}_{who_change_storage} set quantity = {message.text} where id = {id}"
            cursor.execute(query)
            conn.commit()
            # оновлення товару в stickers_all
            if category == 'stickers':
                query = "update stickers_all set " \
                        "quantity = ((select quantity div quantity_in_pack from stickers_dima where id = stickers_all.id_stickers) + " \
                        "(select quantity div quantity_in_pack from stickers_vlad where id = stickers_all.id_stickers)) " \
                        f"where id_stickers = {id};"
                cursor.execute(query)
                conn.commit()
            else:
                query = f"update {category}_all set quantity = ((select quantity from {category}_dima where id = {category}_all.id_{category}) + " \
                        f"(select quantity from {category}_vlad where id = {category}_all.id_{category}))" \
                        f"where id_{category} = {id};"
                cursor.execute(query)
                conn.commit()
            bot.send_message(message.chat.id, "Зміни збережено")
    except:
        sent = bot.send_message(message.chat.id, f"Введи число, бомж")
        conn.close()
        cursor.close()
        bot.register_next_step_handler(sent, new_quantity)
    finally:
        conn.close()
        cursor.close()


# Конец
'''
Редагувати склад
'''
# Конец

# Начало
'''
Full склад
'''


# Начало


@bot.message_handler(func=lambda message: message.text == 'Full склад')
def full_storage(message):
    conn = connection_func()
    cursor = conn.cursor()
    try:
        cursor.execute(f"select * from stickers_all")
        storage = cursor.fetchall()

        all_order = types.InlineKeyboardMarkup(row_width=3)
        full_storage = 'Стикеры\n\n'
        for el in storage:  # (1, 'Рандом 1', 3, 0)
            full_storage += f'{el[0]:02}. "{el[1]}" - {el[2]}'
            full_storage += '\n'

        cursor.execute(f"select * from posters_all")
        storage = cursor.fetchall()
        full_storage += '\nПостеры\n\n'
        for el in storage:  # (1, 'Рандом 1', 3, 0)
            full_storage += f'{el[0]:02}. "{el[1]}" - {el[2]}'
            full_storage += '\n'

        cursor.execute(f"select * from lamps_all")
        storage = cursor.fetchall()
        full_storage += '\nЛампы\n\n'
        for el in storage:  # (1, 'Рандом 1', 3, 0)
            full_storage += f'{el[0]:02}. "{el[1]}" - {el[2]}'
            full_storage += '\n'
        bot.send_message(message.chat.id, full_storage, reply_markup=all_order)
    except Error as e:
        logger.error(f"Помилка в full_storage {e}")
    finally:
        conn.close()
        cursor.close()


# Конец
'''
Full склад
'''
# Конец


# Начало
'''
Управління замовленнями
'''


# Начало


@bot.message_handler(func=lambda message: message.text == 'Управління замовленнями')
def menu_orders(message):
    menu_orders_keyboard = types.InlineKeyboardMarkup(row_width=3)
    add_order = types.InlineKeyboardButton("Додати", callback_data="add_order")
    view_orders = types.InlineKeyboardButton("Перегланути", callback_data="view_orders")
    send_orders = types.InlineKeyboardButton("Відправити", callback_data="send_orders")
    delete_order = types.InlineKeyboardButton("Видалити", callback_data="delete_order")
    menu_orders_keyboard.add(add_order, view_orders, send_orders, delete_order)
    bot.send_message(message.chat.id, 'Меню управління замовленнями:', reply_markup=menu_orders_keyboard)


@bot.callback_query_handler(func=lambda call: "order" in call.data)
def menu_orders_call(call):
    if call.data == "add_order":
        platform_order(call.message)
    elif call.data == "view_orders":
        view_orders(call)
    elif call.data == "send_orders":
        send_orders(call)
    elif call.data == "delete_order":
        delete_order(call)
    spam_check(call)


'''add_order'''


def platform_order(message):
    platform_order_keyboard = types.InlineKeyboardMarkup(row_width=3)
    instagram = types.InlineKeyboardButton("instagram", callback_data="platform_instagram")
    site = types.InlineKeyboardButton("site", callback_data="platform_site")
    olx = types.InlineKeyboardButton("olx", callback_data="platform_olx")
    izi = types.InlineKeyboardButton("izi", callback_data="platform_izi")
    dropshipping = types.InlineKeyboardButton("dropshipping", callback_data="platform_dropshipping")
    other = types.InlineKeyboardButton("other", callback_data="platform_other")
    platform_order_keyboard.add(instagram, site, olx, izi, dropshipping, other)
    bot.send_message(message.chat.id, 'Платформа продажі?', reply_markup=platform_order_keyboard)


@bot.callback_query_handler(func=lambda call: "platform" in call.data)
def platform_order_call(call):
    arr = call.data.split("_")
    platform = arr[1]
    platform_order_bd(platform)
    get_ttn(call.message)
    spam_check(call)


def platform_order_bd(platform):
    conn = connection_func()
    cursor = conn.cursor()
    try:
        cursor.execute(f'insert into orders set platform = "{platform}";')
        conn.commit()
    except Error as e:
        logger.error(f"Помилка в platform_order_bd {e}")
    finally:
        conn.close()
        cursor.close()


def get_ttn(message):
    ttn = bot.send_message(message.chat.id, "ТТН??")
    bot.register_next_step_handler(ttn, get_ttn_call)


def get_ttn_call(message):
    conn = connection_func()
    cursor = conn.cursor()
    try:
        conn.close()
        cursor.close()
        last_id = last_id_orders()

        conn = connection_func()
        cursor = conn.cursor()
        cursor.execute(f'update orders set ttn = "{message.text}" where id = {last_id};')
        conn.commit()

        select_admin = types.InlineKeyboardMarkup(row_width=3)
        dima = types.InlineKeyboardButton("Дімона", callback_data="admin_dima")
        vlad = types.InlineKeyboardButton("Владоса", callback_data="admin_vlad")
        select_admin.add(dima, vlad)
        bot.send_message(message.from_user.id, 'З чийого складу пиздимо товар?))', reply_markup=select_admin)
    except Error as e:
        logger.error(f"Помилка в platform_order_bd {e}")
    finally:
        conn.close()
        cursor.close()


@bot.callback_query_handler(func=lambda call: "admin" in call.data)
def select_admin_call(call):
    conn = connection_func()
    cursor = conn.cursor()
    try:
        arr = call.data.split("_")
        admin_name = arr[1]
        last_id = last_id_orders()

        cursor.execute(f'update orders set admin_name = "{admin_name}" where id = {last_id}')
        conn.commit()
        cursor.execute(f'update admins set who_change = "{admin_name}" where id = {call.message.chat.id}')
        conn.commit()
    except Error as e:
        logger.error(f"Помилка в select_admin_call {e}")
    finally:
        conn.close()
        cursor.close()
        spam_check(call)
    change_choose_cat_orders(call)


def change_choose_cat_orders(call):
    cat = types.InlineKeyboardMarkup(row_width=3)
    cat1 = types.InlineKeyboardButton("Стікери", callback_data="catid_stickers")
    cat2 = types.InlineKeyboardButton("Постери", callback_data="catid_posters")
    cat3 = types.InlineKeyboardButton("Лампи", callback_data="catid_lamps")
    cat.add(cat1, cat2, cat3)
    bot.send_message(call.message.chat.id, 'Категорія?', reply_markup=cat)


@bot.callback_query_handler(func=lambda call: "catid" in call.data)
def select_cat(call):
    conn = connection_func()
    cursor = conn.cursor()
    try:
        if call.data == "catid_stickers":
            cursor.execute(f'update admins set category_id = 1 where id = {call.message.chat.id}')
        elif call.data == "catid_posters":
            cursor.execute(f'update admins set category_id = 2 where id = {call.message.chat.id}')
        elif call.data == "catid_lamps":
            cursor.execute(f'update admins set category_id = 3 where id = {call.message.chat.id}')
        conn.commit()
        conn.close()
        cursor.close()
        select_product(call.message)
    except Error as e:
        logger.error(f"Помилка в select_admin_call {e}")
    finally:
        conn.close()
        cursor.close()
        spam_check(call)


message_delete = ''


def select_product(message):
    conn = connection_func()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f'select title from categories where id = (select category_id from admins where id = {message.chat.id})')
        category = cursor.fetchone()
        category = category[0]

        conn.close()
        cursor.close()
        admin_name = admin_name_last_order()

        conn = connection_func()
        cursor = conn.cursor()
        cursor.execute(f"select * from {category}_{admin_name}")
        storage = cursor.fetchall()

        all_order = types.InlineKeyboardMarkup(row_width=3)
        if category == "stickers":
            for el in storage:  # (1, 'Рандом 1', 200, 100, 0)
                full_storage = ''
                full_storage += f'{el[0]}. "{el[1]}" - '
                if el[2] == 0:
                    full_storage += f'0'
                else:
                    if el[2] % el[3] == 0:
                        full_storage += f'{el[2] / el[3] :.0f}x{el[3]}'
                    else:
                        full_storage += f'{el[2] // el[3]}x{el[3]} {el[2] % el[3]}'
                full_storage += '\n'
                order = types.InlineKeyboardButton(f"{full_storage}",
                                                   callback_data=f'selectproduct_{el[0]}')
                all_order.add(order)
        else:
            for el in storage:
                full_storage = ''
                full_storage += f'{el[0]}. "{el[1]}" - {el[2]}'
                order = types.InlineKeyboardButton(f"{full_storage}",
                                                   callback_data=f'selectproduct_{el[0]}')
                all_order.add(order)
        one_more_time = types.InlineKeyboardButton(f"Вибрати іншу категорію", callback_data=f'select_one_more')
        done = types.InlineKeyboardButton(f"Замовлення укомплектовано", callback_data=f'select_done')
        all_order.add(one_more_time)
        all_order.add(done)
        bot.send_message(message.chat.id, "Склад:", reply_markup=all_order)

        global message_delete
        message_delete = message
    except Error as e:
        logger.error(f"Помилка в select_product {e}")
    finally:
        conn.close()
        cursor.close()


@bot.callback_query_handler(func=lambda call: "selectproduct" in call.data)
def select_product_call(call):
    conn = connection_func()
    cursor = conn.cursor()
    try:
        cursor.execute(
            f'select title from categories where id = (select category_id from admins where id = {call.message.chat.id})')
        category = cursor.fetchone()
        category = category[0]

        conn.close()
        cursor.close()
        admin_name = admin_name_last_order()

        conn = connection_func()
        cursor = conn.cursor()
        cursor.execute(
            f'select quantity from admins where id = {call.message.chat.id}')
        quantity = cursor.fetchone()
        quantity = quantity[0]

        arr = call.data.split("_")
        id_arr = arr[1]

        change_order = types.InlineKeyboardMarkup(row_width=3)
        if category == 'stickers':
            cursor.execute(
                f"select id, name, quantity, quantity_in_pack from {category}_{admin_name} where id = {id_arr}")
            info = cursor.fetchone()

            change_plus = types.InlineKeyboardButton(f'+{25 if info[3] % 25 == 0 else info[3]}',
                                                     callback_data=f"plucs_{id_arr}_{25 if info[3] % 25 == 0 else info[3]}")
            change_x = types.InlineKeyboardButton('Власне значення', callback_data=f"other_{id_arr}")
            change_minus = types.InlineKeyboardButton(f'-{25 if info[3] % 25 == 0 else info[3]}',
                                                      callback_data=f"minucs_{id_arr}_{25 if info[3] % 25 == 0 else info[3]}")
        else:
            cursor.execute(f"select id, name, quantity from {category}_{admin_name} where id = {id_arr}")
            info = cursor.fetchone()
            change_plus = types.InlineKeyboardButton('+1', callback_data=f"plucs_{id_arr}_{1}")
            change_x = types.InlineKeyboardButton('Власне значення', callback_data=f"other_{id_arr}")
            change_minus = types.InlineKeyboardButton('-1', callback_data=f"minucs_{id_arr}_{1}")

        add_to_order = types.InlineKeyboardButton('Додати до замовлення', callback_data=f"add_product_to_ord")
        close = types.InlineKeyboardButton('Закрити', callback_data=f"close")

        change_order.add(change_plus, change_x, change_minus)
        change_order.add(add_to_order)
        change_order.add(close)

        bot.send_message(call.message.chat.id, f'{info[0]}. "{info[1]}" вибрано - {quantity}',
                         reply_markup=change_order)
    except Error as e:
        logger.error(f"Помилка в select_product_call {e}")
    finally:
        conn.close()
        cursor.close()


@bot.callback_query_handler(func=lambda call: "plucs" in call.data)
def plucs(call):
    arr = call.data.split("_")
    id = arr[1]
    plus = arr[2]

    conn = connection_func()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f'select title from categories where id = (select category_id from admins where id = {call.message.chat.id})')
        category = cursor.fetchone()
        category = category[0]

        conn.close()
        cursor.close()
        admin_name = admin_name_last_order()

        conn = connection_func()
        cursor = conn.cursor()

        cursor.execute(f"select quantity from {category}_{admin_name} where id = {id}")
        quantity_all = cursor.fetchone()
        quantity_all = quantity_all[0]

        cursor.execute(f"select quantity from admins where id = {call.message.chat.id}")
        quantity_now = cursor.fetchone()
        quantity_now = quantity_now[0]

        cursor.execute(f'update admins set item_id = {id} where id = {call.message.chat.id}')
        conn.commit()

        if quantity_now <= quantity_all - int(plus):
            cursor.execute(f"update admins set quantity = quantity + {plus} where id = {call.message.chat.id}")
            conn.commit()
            spam_check(call)

        else:
            bot.send_message(call.message.chat.id, "Йопт, на складі немає стільки товару")
            spam_check(call)

        conn.close()
        cursor.close()
        select_product_call(call)
    except Error as e:
        logger.error(f"Помилка в plucs {e}")
    finally:
        conn.close()
        cursor.close()


@bot.callback_query_handler(func=lambda call: "minucs" in call.data)
def minucs(call):
    arr = call.data.split("_")
    id = arr[1]
    plus = arr[2]

    conn = connection_func()
    cursor = conn.cursor()
    try:
        cursor.execute(f"select quantity from admins where id = {call.message.chat.id}")
        quantity_now = cursor.fetchone()
        quantity_now = quantity_now[0]

        cursor.execute(f'update admins set item_id = {id} where id = {call.message.chat.id}')
        conn.commit()

        if quantity_now - int(plus) >= 0:
            cursor.execute(f"update admins set quantity = quantity - {plus} where id = {call.message.chat.id}")
            conn.commit()
            spam_check(call)
        else:
            bot.send_message(call.message.chat.id, "Прєдусмотрєно😏")
            spam_check(call)

        conn.close()
        cursor.close()
        select_product_call(call)
    except Error as e:
        logger.error(f"Помилка в minucs {e}")
    finally:
        conn.close()
        cursor.close()


@bot.callback_query_handler(func=lambda call: "other" in call.data)
def other(call):
    arr = call.data.split("_")
    id_arr = arr[1]
    conn = connection_func()
    cursor = conn.cursor()
    try:
        cursor.execute(f"update admins set item_id = {id_arr} where id = {call.message.chat.id};")
        conn.commit()
        conn.close()
        cursor.close()
        sent = bot.send_message(call.message.chat.id, f"Яку кількість додати? (Напиши -1 для виходу)")
        bot.register_next_step_handler(sent, new_quantity_select, call)
    except Error as e:
        logger.error(f"Помилка в other: {e}")
        bot.send_message(call.message.chat.id, "Помилка в запросі в БД")
    finally:
        conn.close()
        cursor.close()


def new_quantity_select(message, call, flag=True):
    if flag:
        spam_check(call)
    conn = connection_func()
    cursor = conn.cursor()

    conn.close()
    cursor.close()
    info = admins_info(call.message)
    category = info[0]
    who_change = info[1]
    item_id = info[2]

    conn = connection_func()
    cursor = conn.cursor()
    cursor.execute(f"select quantity from {category}_{who_change} where id = {item_id}")
    quantity = cursor.fetchone()
    quantity = quantity[0]
    try:
        if not message.text.isdigit():
            conn.close()
            cursor.close()
            sent = bot.send_message(message.chat.id, f"Введи число, бомж")
            bot.register_next_step_handler(sent, new_quantity_select, call, False)
        elif int(message.text) < 0:
            conn.close()
            cursor.close()
            sent = bot.send_message(message.chat.id, f"Мінусові значення не можна задавати")
            bot.register_next_step_handler(sent, new_quantity_select, call, False)
        elif quantity < int(message.text):
            bot.send_message(message.chat.id, "Я канешно все понімаю, но в нас немає стільки товару(((")
            select_product_call(call)
        else:
            query = f"update admins set quantity = {message.text} where id = {message.chat.id}"
            cursor.execute(query)
            conn.commit()
            conn.close()
            cursor.close()
            select_product_call(call)
    except:
        sent = bot.send_message(message.chat.id, f"Введи число, бомж")
        bot.register_next_step_handler(sent, new_quantity_select, call, False)
    finally:
        conn.close()
        cursor.close()


@bot.callback_query_handler(func=lambda call: "add_product_to_ord" in call.data)
def add_to_order(call):
    conn = connection_func()
    cursor = conn.cursor()
    try:
        conn.commit()
        cursor.execute(f"insert into order_products set "
                       f"category_id = (select category_id from admins where id = {call.message.chat.id}),"
                       f"product_id = (select item_id from admins where id = {call.message.chat.id}),"
                       f"order_id = (select id from orders order by id desc limit 1),"
                       f"quantity = (select quantity from admins where id = {call.message.chat.id});")
        conn.commit()

        cursor.execute(f"select quantity from admins where id = {call.message.chat.id}")
        quantity = cursor.fetchone()
        conn.close()
        cursor.close()
        info = admins_info(call.message)
        category = info[0]
        who_change = admin_name_last_order()
        item_id = info[2]
        quantity = quantity[0]

        conn = connection_func()
        cursor = conn.cursor()
        cursor.execute(f"update {category}_{who_change} set quantity = quantity - {quantity} where id = {item_id}")
        conn.commit()

        cursor.execute(f"update admins set quantity = 0 where id = {call.message.chat.id}")
        conn.commit()

        cursor.execute(f"update admins set quantity = 0 where id = {call.message.chat.id}")
        conn.commit()

        # оновлення товару в stickers_all
        if category == 'stickers':
            query = f"update {category}_all set " \
                    f"quantity = (select quantity div quantity_in_pack from stickers_dima where id = {item_id}) + " \
                    f"(select quantity div quantity_in_pack from stickers_vlad where id = {item_id})" \
                    f"where id_stickers = {item_id}"
        else:
            query = f"update {category}_all set " \
                    f"quantity = (select quantity from {category}_dima where id = {item_id}) + " \
                    f"(select quantity from {category}_vlad where id = {item_id})" \
                    f"where id_{category} = {item_id}"

        cursor.execute(query)
        conn.commit()

        spam_check(call)
        bot.send_message(call.message.chat.id, "Додано до замовлення🤑")
    except Error as e:
        logger.error(f"Помилка в add_to_order: {e}")
        bot.send_message(call.message.chat.id, "Помилка в запросі в БД")
    finally:
        conn.close()
        cursor.close()


@bot.callback_query_handler(func=lambda call: "select_one_more" in call.data)
def one_more_call(call):
    change_choose_cat_orders(call)

    global message_delete
    spam_check(message_delete, False)


@bot.callback_query_handler(func=lambda call: "select_done" in call.data)
def select_done_call(call):
    sent = bot.send_message(call.message.chat.id, f"Price?")
    bot.register_next_step_handler(sent, set_a_price)

    global message_delete
    spam_check(message_delete, False)


def set_a_price(message):
    conn = connection_func()
    cursor = conn.cursor()
    try:
        int(message.text)
        price = int(message.text)
        if price >= 0:
            last_id = last_id_orders()
            cursor.execute(f'update orders set price = {message.text} where id = {last_id};')
            conn.commit()
            bot.send_message(message.chat.id, "Додано до бази даних🤯")
        else:
            conn.close()
            cursor.close()
            sent = bot.send_message(message.chat.id, "Піздиш гроші ПАДЛА?? Напиши нормально:")
            bot.register_next_step_handler(sent, set_a_price)
    except:
        conn.close()
        cursor.close()
        sent = bot.send_message(message.chat.id, "Цифру пж:")
        bot.register_next_step_handler(sent, set_a_price)
    finally:
        conn.close()
        cursor.close()


'''view_orders'''


def view_orders(call):
    conn = connection_func()
    cursor = conn.cursor()
    try:
        cursor.execute(f"select id from orders where status = 'processing'")

        id_processing_turple = cursor.fetchall()
        if not id_processing_turple:
            bot.send_message(call.message.chat.id, f"Немає замовлень😢")
        else:

            id_processing_turple = list(id_processing_turple)  # [(69,), (72,), (76,), (77,)]

            id_processing_list = []
            for el in id_processing_turple:
                id_processing_list.append(el[0])  # [69, 72, 76, 77]

            for el in id_processing_list:
                send = ''
                cursor.execute(f"select admin_name, id, platform, ttn, price from orders where id = {el}")

                info = cursor.fetchone()  # ('dima', 88, 'instagram', '4567', 100)
                admin_name = info[0]
                id = info[1]
                platform = info[2]
                ttn = info[3]
                price = info[4]
                send += f"\n\nЗамовлення №{id} ({platform})\nТТН: {ttn}\n"

                cursor.execute(
                    f"select category_id, product_id, quantity from order_products where order_id = {el}")
                info = cursor.fetchall()  # (category_id = 1, product_id = 23, quantity = 25)
                for i in info:
                    category_id = i[0]
                    product_id = i[1]
                    quantity = i[2]

                    cursor.execute(f"select title from categories where id = {category_id}")
                    category = cursor.fetchone()

                    categories = category[0]

                    cursor.execute(f"select name from {categories}_{admin_name} where id = {product_id}")
                    title = cursor.fetchone()
                    logger.debug(title)
                    title = title[0]

                    send += f"{quantity} {title} ({categories})\n"
                send += f"= {price} грн\nЗапакував: {admin_name}"
                bot.send_message(call.message.chat.id, send)

    except Error as e:
        logger.error(f"Помилка в view_orders: {e}")
    finally:
        conn.close()
        cursor.close()


'''send_orders'''


def send_orders(call):
    conn = connection_func()
    cursor = conn.cursor()
    cursor.execute(f"update orders set status = 'sent' where status = 'processing'")
    conn.commit()
    conn.close()
    cursor.close()
    bot.send_message(call.message.chat.id, "Всі замовлення були відправлені🥰")


@bot.callback_query_handler(func=lambda call: "close" in call.data)
def close_call(call):
    spam_check(call)


'''delete_order'''


def delete_order(call):
    sent = bot.send_message(call.message.chat.id, f"Номер замовлення?")
    bot.register_next_step_handler(sent, delete_order_by_number)


def delete_order_by_number(message):
    id_order = message.text

    conn = connection_func()
    cursor = conn.cursor()

    if not id_order.isdigit():
        bot.send_message(message.chat.id, "Незрозуміле число🤓")
    else:
        try:
            cursor.execute(f"delete from order_products where order_id = {id_order};")
            conn.commit()

            cursor.execute(f"delete from orders where id = {id_order};")
            conn.commit()

            bot.send_message(message.chat.id, f"Готово👌")
        except Error as e:
            logger.error(f"Помилка в delete_order_by_number: {e}")
            bot.send_message(message.chat.id, "Помилка😇")
        finally:
            conn.close()
            cursor.close()


# Конец
'''
Управління замовленнями
'''
# Конец

# Начало
'''
Пошук по ттн
'''


# Начало


@bot.message_handler(func=lambda message: message.text == 'Пошук по ТТН')
def search_by_ttn(message):
    sent = bot.send_message(message.chat.id, "ТТНчік?")
    bot.register_next_step_handler(sent, search_by_ttn_handler)


def search_by_ttn_handler(message):
    ttn = message.text
    conn = connection_func()
    cursor = conn.cursor(buffered=True)

    send = ''
    cursor.execute(f"select admin_name, id, platform, price, date from orders where ttn = '{ttn}'")

    info = cursor.fetchone()  # ('dima', 957, 'instagram', 100, datetime.datetime(2021, 2, 5, 11, 42, 44))
    if not info:
        bot.send_message(message.chat.id, f"Такого ТТН немає😳")
    else:

        admin_name = info[0]
        id = info[1]
        platform = info[2]
        price = info[3]
        date = info[4]
        send += f"{date}\n"
        send += f"Замовлення №{id} ({platform})\nТТН: {ttn}\n"
        try:
            cursor.execute(
                f"select category_id, product_id, quantity from order_products where order_id = {id}")
            info = cursor.fetchall()  # (category_id = 1, product_id = 23, quantity = 25)
            for i in info:
                category_id = i[0]
                product_id = i[1]
                quantity = i[2]

                cursor.execute(f"select title from categories where id = {category_id}")
                category = cursor.fetchone()

                categories = category[0]

                cursor.execute(f"select name from {categories}_{admin_name} where id = {product_id}")
                title = cursor.fetchone()
                title = title[0]

                send += f"{quantity} {title} ({categories})\n"
            send += f"= {price} грн\nЗапакував: {admin_name}"
            bot.send_message(message.chat.id, send)
        except Error as e:
            logger.error(f"Помилка в search_by_ttn_handler: {e}")
            bot.send_message(message.chat.id, "ТТН має пошкоджені дані😇")

    conn.close()
    cursor.close()


# Конец
'''
Пошук по ттн
'''
# Конец


# Начало
'''
Статистика за місяць
'''


# Начало


@bot.message_handler(func=lambda message: message.text == 'Статистика за місяць')
def monthly_statistics(message):
    conn = connection_func()
    cursor = conn.cursor()
    mouths_dict = {1: "Січень", 2: "Лютий", 3: "Березень", 4: "Квітень", 5: "Травень", 6: "Червень", 7: "Липень",
                   8: "Серпень", 9: "Вересень", 10: "Жовтень", 11: "Листопад", 12: "Грудень"}
    message_to_send = ''
    try:
        cursor.execute(f"select count(*) from orders where EXTRACT( MONTH FROM date) = EXTRACT( MONTH FROM now());")
        number_of_orders = cursor.fetchone()
        number_of_orders = number_of_orders[0]
        if number_of_orders == 0:
            bot.send_message(message.chat.id, f"Дядько, заказів ще немає")
        else:
            cursor.execute(f"select MONTH(now());")
            mouth = cursor.fetchone()
            mouth_number = mouth[0]
            message_to_send += mouths_dict[mouth_number]

            cursor.execute(f"select DATE_FORMAT(now(), '%d.%m.%Y');")
            date = cursor.fetchone()
            date = date[0]
            message_to_send += f" {date} (СТАТИСТИКА)\n"


            logger.debug(number_of_orders)

            message_to_send += f"Замовлень - {number_of_orders}\n"


            cursor.execute(f"select DAYOFMONTH(now());")
            now_day = cursor.fetchone()
            now_day = now_day[0]
            message_to_send += f"Середня кількість замовлень - {number_of_orders / now_day:.1f}\n"

            cursor.execute(f"SELECT SUM(price) FROM `orders` where EXTRACT( MONTH FROM date) = EXTRACT( MONTH FROM now());")
            sum_price = cursor.fetchone()
            sum_price = sum_price[0]
            message_to_send += f"\nПрибуток - {sum_price} грн"
            bot.send_message(message.chat.id, message_to_send)

            '''Диаграмма Платформы продажи'''
            top_platforms_diagram(message)

            '''Диаграмма Топ 7 товаров'''
            top_7_product_diagram(message)



    except Error as e:
        logger.debug(f"{e}")


def top_platforms_diagram(message):
    conn = connection_func()
    cursor = conn.cursor()
    platform_dict = {'instagram': 0, 'olx': 0, 'site': 0, 'izi': 0, 'dropshipping': 0, 'other': 0}
    platform_dict_string = ''
    for el in platform_dict:
        cursor.execute(f"select count(*) from orders "
                       f"where EXTRACT( MONTH FROM date) = EXTRACT( MONTH FROM now()) "
                       f"GROUP by platform "
                       f"having platform = '{el}';")
        cout = cursor.fetchone()
        if cout is None:
            cout = 0
        else:
            cout = cout[0]
        platform_dict[el] = cout
        platform_dict_string += f"{el} - {cout} замовлень\n"
    conn.close()
    cursor.close()
    rcParams["figure.figsize"] = 10, 4
    x = list(platform_dict.values())
    y = list(platform_dict.keys())
    sr = pd.Series(x, index=y)
    sr.plot(kind="barh", color="#33F7FF")
    plt.savefig('top_platform.png')
    plt.gcf().clear()

    top_platform_photo = open('top_platform.png', 'rb')
    bot.send_photo(message.chat.id, top_platform_photo, caption=platform_dict_string)


def top_7_product_diagram(message):
    conn = connection_func()
    cursor = conn.cursor()
    cursor.execute(f"select category_id, product_id, count(*) as count "
                   f"from order_products "
                   f"where order_id >= (select id from orders where EXTRACT( MONTH FROM date) = EXTRACT( MONTH FROM now()) order by id limit 1)"
                   f"group by product_id "
                   f"order by count desc "
                   f"limit 7;")
    data_orders = cursor.fetchall()
    logger.debug(data_orders)
    list_top = []
    list_count = []
    for el in data_orders:
        name_product = "("
        cursor.execute(f"select name, title from categories where id = {el[0]}")
        category = cursor.fetchone()
        category_title = category[1]
        category = category[0]
        name_product += category
        name_product += ')\n'

        cursor.execute(f"select name from {category_title}_all where id_{category_title} = {el[1]}")
        title = cursor.fetchone()
        title = title[0]
        name_product += title
        list_top.append(name_product)
        list_count.append(el[2])
    conn.close()
    cursor.close()
    top_product = pd.Series(list_count, index=list_top)
    top_product.plot(kind="barh", color="#33F7FF")
    plt.savefig('top_7_product.png')

    top_7_product_photo = open('top_7_product.png', 'rb')
    bot.send_photo(message.chat.id, top_7_product_photo, caption=f"Топ 7 товарів")


# Конец
'''
Статистика за місяць
'''
# Конец


# Начало
'''
Другие команды
'''


# Начало


@bot.message_handler(commands=['store'])
def store(message):
    full_storage(message)


# Конец
'''
Другие команды
'''
# Конец


bot.polling(none_stop=True)