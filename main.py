#              ---=== Exchange Bot 0.1.0 ===---
#   В данной версии бот умеет:
#   - определять пары для обмена
#   - проверять корректность вводимой клиентом суммы для обмена
#   - рассчитывать сумму получаемую клиентом
#   - формировать и отправлять заявку оператору

from config import TOKEN, COMISSION_FIAT_DIG, COMISSION_DIG_FIAT, RECEIP_ACCOUNT, BANK, MIN_EXCHANGE_FIAT, MIN_EXCHANGE_DIG, OPERATOR_ID, EXCHANGER_NAME, WALLET_BTC, WALLET_ETH, WALLET_USDT
from pycoingecko import CoinGeckoAPI
from telebot import types
import telebot
import datetime

cg = CoinGeckoAPI()

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def main(message):
    button = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button.add(
               types.KeyboardButton('SBER -> Bitcoin'),
               types.KeyboardButton('Bitcoin -> SBER'),
               types.KeyboardButton('SBER -> Ethereum'),
               types.KeyboardButton('Ethereum -> SBER'),
               types.KeyboardButton('SBER -> USDT'),
               types.KeyboardButton('USDT -> SBER')
               )
    msg = bot.send_message(message.chat.id, f'Привет! Это обменник {EXCHANGER_NAME}!\n'
                                            f'У нас вы можете быстро и легко обменять крипту.\n\n'
                                            f'Мы используем сеть BTC для транзакций Bitcoin и ERC20 для транзакций Ethereum.\n\n'
                                            f'Пожалуйста, внимательно проверяйте вводимые данные!\n'
                                            f'Мы не несём ответственность за некорректно введёные реквизиты и утерянные в следствии этого средства!\n'
                                            f'Помните что блокчейн не имеет возможность отзывать транзакции если вы случайно, неправильно указали кошелёк!\n\n'
                                            f'Выберете нужную пару нажав на кнопку.',
                                            reply_markup=button)

    bot.register_next_step_handler(msg, pair_choice)


## функция выбора пары для обмена
def pair_choice(message):

    global coin_mark
    global coin_id
    global wallet_id
    global comission

    if message.text == 'SBER -> Bitcoin':     
        coin_mark = 'bitcoin'
        coin_id = 'BTC'
        comission = COMISSION_FIAT_DIG
        get_course(message)
    elif message.text == 'Bitcoin -> SBER':
        coin_mark = 'bitcoin'
        coin_id = 'BTC'
        wallet_id = WALLET_BTC
        comission = COMISSION_DIG_FIAT
        get_course(message)
    elif message.text == 'SBER -> Ethereum':
        coin_mark = 'ethereum'
        coin_id = 'ETH'
        comission = COMISSION_FIAT_DIG
        get_course(message)
    elif message.text == 'Ethereum -> SBER':
        coin_mark = 'ethereum'
        coin_id = 'ETH'
        wallet_id = WALLET_ETH
        comission = COMISSION_DIG_FIAT
        get_course(message)
    elif message.text == 'SBER -> USDT':
        coin_mark = 'tether'
        coin_id = 'USDT'
        comission = COMISSION_FIAT_DIG
        get_course(message)
    elif message.text == 'USDT -> SBER':
        coin_mark = 'tether'
        coin_id = 'USDT'
        wallet_id = WALLET_USDT
        comission = COMISSION_DIG_FIAT
        get_course(message)
    else:
        main(message)


## общая функция получения курса и расчёт курса с учётом комиссии
def get_course(message):
    button = types.ReplyKeyboardRemove()
    print(coin_mark)
    price = cg.get_price(ids=coin_mark, vs_currencies='rub')
    
    if comission ==  COMISSION_FIAT_DIG:
        msg = bot.send_message(message.chat.id, f'1 {coin_mark} = {price[coin_mark]["rub"] * COMISSION_FIAT_DIG} RUB \n\nМинимальная сумма обмена составляет {MIN_EXCHANGE_FIAT} RUB.\n' 
                                                f'Пожалуйста введите сумму которую хотите обменять.', reply_markup=button)
        bot.register_next_step_handler(msg, check_amount_checkup)
    else:
        msg = bot.send_message(message.chat.id, f'1 {coin_mark} = {price[coin_mark]["rub"] * COMISSION_DIG_FIAT} RUB \n\nМинимальная сумма обмена составляет {MIN_EXCHANGE_DIG} {coin_id}.\n' 
                                                f'Пожалуйста введите сумму которую хотите обменять.', reply_markup=button)
        bot.register_next_step_handler(msg, check_amount_checkup)


## функция проверки корректности введённой суммы обмена 
def check_amount_checkup(message):
    try:
        global money_for_exchange
        money_for_exchange = float(message.text)
        price = cg.get_price(ids=coin_mark, vs_currencies='rub')

        if comission == COMISSION_FIAT_DIG:
            if money_for_exchange >=  MIN_EXCHANGE_FIAT:
                msg = bot.send_message(message.chat.id, f'Вы получите {money_for_exchange / (price[coin_mark]["rub"] * comission)} {coin_id}.\n'
                                                        f'Пожалуйста, укажите адрес вашего кошелька.\n')
                bot.register_next_step_handler(msg, wallet_checkup)
            else:
                msg = bot.send_message(message.chat.id, f'Минимальная сумма обмена состовляет {MIN_EXCHANGE_FIAT} RUB\n')
                bot.register_next_step_handler(msg, get_course)
        else:
            if money_for_exchange >=  MIN_EXCHANGE_DIG:
                msg = bot.send_message(message.chat.id, f'Вы получите {money_for_exchange * price[coin_mark]["rub"] * comission} RUB.\n'
                                                        f'Пожалуйста, укажите номер вашей карты.\n')
                bot.register_next_step_handler(msg, wallet_checkup)
            else:
                msg = bot.send_message(message.chat.id, f'Минимальная сумма обмена состовляет {MIN_EXCHANGE_DIG} {coin_id}\n')
                bot.register_next_step_handler(msg, get_course)

    except ValueError:
        bot.send_message(message.chat.id, 'Пожалуйста введите корректные данные.')
        get_course(message)


## функция приёма кошелька и запроса на оплату заявки 
def wallet_checkup(message):

    global client_wallet
    client_wallet = str(message.text)
    button = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button.add(types.KeyboardButton('Подтверждаю оплату'))

    if comission == COMISSION_FIAT_DIG:
        price = cg.get_price(ids=coin_mark, vs_currencies='rub')
        msg = bot.send_message(message.chat.id, f'Вы обмениваете {money_for_exchange} RUB на {money_for_exchange / (price[coin_mark]["rub"] * comission)} {coin_id}.\n'
                                                f'Ваш кошелёк: {client_wallet}\n\n'
                                                f'Мы ожидаем от вас перевода по реквизитам: \n'                                    
                                                f'{RECEIP_ACCOUNT}\n'
                                                f'на карту {BANK} в размере {money_for_exchange} RUB\n'
                                                f'После перевода, нажмите кнопку "Подтверждаю оплату"',
                                                reply_markup=button)
        bot.register_next_step_handler(msg, end_operation)
    else: 
        price = cg.get_price(ids=coin_mark, vs_currencies='rub')
        msg = bot.send_message(message.chat.id, f'Вы обмениваете {money_for_exchange} {coin_id} на {money_for_exchange * price[coin_mark]["rub"] * comission} RUB.\n'
                                                f'Ваша карта: {client_wallet}\n\n'
                                                f'Мы ожидаем от вас перевода на кошелёк:\n'
                                                f'{wallet_id}\n'
                                                f'В размере:\n'
                                                f'{money_for_exchange} {coin_id}\n\n'
                                                f'После перевода, нажмите кнопку "Подтверждаю оплату"',
                                                reply_markup=button)
        bot.register_next_step_handler(msg, end_operation)


## функция формирования заявки для оператора (окончание сделки)
def end_operation(message):

    price = cg.get_price(ids=coin_mark, vs_currencies='rub')
    button = types.ReplyKeyboardRemove()

    if message.text == 'Подтверждаю оплату':
        bot.send_message(message.chat.id, f'Ваша заявка была создана {datetime.datetime.now()}.\n'
                                          f'Обычно обмен занимает до 30 минут.\n'
                                          f'Спасибо за использование нашего обменника {EXCHANGER_NAME}!\n\n'
                                          f'Если хотите произвести обмен ещё раз, перезапустите бота командой /start\n',
                                          reply_markup=button)
        # сообщение оператору
        if comission == COMISSION_FIAT_DIG:
            bot.send_message(OPERATOR_ID, f'Сумма обмена: {money_for_exchange} RUB\n'
                                              f'Сумма к получению: {money_for_exchange / (price[coin_mark]["rub"] * comission)} {coin_id}\n'
                                              f'На кошелёк {client_wallet}\n\n'
                                              f'Время заявки: {datetime.datetime.now()}')           
        else:
            bot.send_message(OPERATOR_ID, f'Сумма обмена: {money_for_exchange} {coin_id}\n'
                                              f'Сумма к получению: {money_for_exchange * price[coin_mark]["rub"] * comission} RUB\n'
                                              f'На карту {client_wallet}\n\n'
                                              f'Время заявки: {datetime.datetime.now()}')
    else:
        bot.send_message(message.chat.id, f'Подтвердите оплату нажав кнопку "Подтверждаю оплату"\n' 
                                          f'Или перезапустите бота командой /start если хотите уточнить свои данные для обмена.\n')
        bot.register_next_step_handler(message, end_operation)

bot.polling()