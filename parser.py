import telebot
import requests
from telebot import types

bot = telebot.TeleBot("782829974:AAFkxMdDpodQ-WX7tEh0kPynKZZ4ylK4k8g")

import telebot
import requests
import threading
import time
from telebot import types

bot = telebot.TeleBot("782829974:AAFkxMdDpodQ-WX7tEh0kPynKZZ4ylK4k8g")

COINS = {
    "₿ Bitcoin": "bitcoin",
    "🔷 Ethereum": "ethereum",
    "🟣 Solana": "solana",
    "🐶 Dogecoin": "dogecoin",
    "🔴 XRP": "ripple",
    "🔵 BNB": "binancecoin",
    "🟡 Cardano": "cardano",
    "🟠 Avalanche": "avalanche-2",
    "🔹 Polkadot": "polkadot",
    "🌕 Litecoin": "litecoin",
    "🔗 Chainlink": "chainlink",
    "🦊 Shiba Inu": "shiba-inu",
    "🌐 Polygon": "matic-network",
    "⚡ Tron": "tron",
    "🌊 Stellar": "stellar",
    "🔰 Uniswap": "uniswap",
    "🌀 Monero": "monero",
    "💎 Cosmos": "cosmos",
    "🚀 Pepe": "pepe",
    "🏦 Arbitrum": "arbitrum"
}

# Подписчики на уведомления
subscribers = set()
# Порог роста для уведомлений
ALERT_THRESHOLD = 5.0  # 5%

def get_all_prices():
    try:
        ids = ",".join(COINS.values())
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true"
        response = requests.get(url, timeout=10)
        return response.json()
    except:
        return None

def safe_get(data, coin_id):
    if coin_id not in data:
        return None, None
    if "usd" not in data[coin_id]:
        return None, None
    price = data[coin_id]["usd"]
    change = data[coin_id].get("usd_24h_change", 0)
    return price, change

def get_history(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=7"
        response = requests.get(url, timeout=10)
        data = response.json()
        prices = data["prices"]
        return prices
    except:
        return None

def draw_chart(prices):
    # Простой график из символов
    values = [p[1] for p in prices[-14:]]
    min_val = min(values)
    max_val = max(values)
    if max_val == min_val:
        return "📊 Цена стабильна"

    chart = "📊 График за 7 дней:\n"
    chart += "высокая ┐\n"
    for i, val in enumerate(values):
        normalized = (val - min_val) / (max_val - min_val)
        bars = int(normalized * 8)
        bar = "█" * bars + "░" * (8 - bars)
        chart += f"        |{bar}\n"
    chart += "низкая  └──────────────\n"
    chart += f"Min: ${min_val:,.2f}\n"
    chart += f"Max: ${max_val:,.2f}"
    return chart

# Автопроверка каждые 5 минут
def auto_check():
    while True:
        time.sleep(300)  # 5 минут
        if not subscribers:
            continue
        data = get_all_prices()
        if not data:
            continue
        alerts = []
        for name, coin_id in COINS.items():
            price, change = safe_get(data, coin_id)
            if price is None:
                continue
            if change >= ALERT_THRESHOLD:
                alerts.append((name, price, change))

        if alerts:
            text = "🔔 Внимание! Сильный рост:\n\n"
            for name, price, change in alerts:
                text += f"🚀 {name}\n"
                text += f"   ${price:,.4f} | +{change:.2f}%\n\n"
            for chat_id in subscribers:
                try:
                    bot.send_message(chat_id, text)
                except:
                    pass

# Запускаем автопроверку в фоне
thread = threading.Thread(target=auto_check)
thread.daemon = True
thread.start()

@bot.message_handler(commands=['start'])
def start(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("📊 Все цены"))
    keyboard.add(types.KeyboardButton("🚀 Что растёт"))
    keyboard.add(types.KeyboardButton("📉 Что падает"))
    keyboard.add(types.KeyboardButton("🔔 Включить уведомления"))
    keyboard.add(types.KeyboardButton("📈 График монеты"))
    keyboard.add(types.KeyboardButton("💡 Что купить"))
    bot.send_message(message.chat.id,
    "📈 Крипто трекер!\nВыбери что хочешь узнать:",
    reply_markup=keyboard)

@bot.message_handler(func=lambda message: True)
def handle(message):
    chat_id = message.chat.id

    if message.text == "📊 Все цены":
        bot.send_message(chat_id, "⏳ Загружаю...")
        data = get_all_prices()
        if not data:
            bot.send_message(chat_id, "❌ Ошибка!")
            return
        text = "📊 Цены криптовалют:\n\n"
        for name, coin_id in COINS.items():
            price, change = safe_get(data, coin_id)
            if price is None:
                continue
            arrow = "🟢" if change > 0 else "🔴"
            text += f"{arrow} {name}\n"
            text += f"   ${price:,.4f} | {change:+.2f}%\n\n"
        bot.send_message(chat_id, text)

    elif message.text == "🚀 Что растёт":
        bot.send_message(chat_id, "⏳ Загружаю...")
        data = get_all_prices()
        if not data:
            bot.send_message(chat_id, "❌ Ошибка!")
            return
        results = []
        for name, coin_id in COINS.items():
            price, change = safe_get(data, coin_id)
            if price is None:
                continue
            if change > 0:
                results.append((name, price, change))
        results.sort(key=lambda x: x[2], reverse=True)
        text = "🚀 Растёт за 24 часа:\n\n"
        for name, price, change in results:
            text += f"🟢 {name}\n"
            text += f"   ${price:,.4f} | +{change:.2f}%\n\n"
        bot.send_message(chat_id, text)

    elif message.text == "📉 Что падает":
        bot.send_message(chat_id, "⏳ Загружаю...")
        data = get_all_prices()
        if not data:
            bot.send_message(chat_id, "❌ Ошибка!")
            return
        results = []
        for name, coin_id in COINS.items():
            price, change = safe_get(data, coin_id)
            if price is None:
                continue
            if change < 0:
                results.append((name, price, change))
        results.sort(key=lambda x: x[2])
        text = "📉 Падает за 24 часа:\n\n"
        for name, price, change in results:
            text += f"🔴 {name}\n"
            text += f"   ${price:,.4f} | {change:.2f}%\n\n"
        bot.send_message(chat_id, text)

    elif message.text == "🔔 Включить уведомления":
        if chat_id in subscribers:
            subscribers.remove(chat_id)
            bot.send_message(chat_id,
            "🔕 Уведомления выключены!")
        else:
            subscribers.add(chat_id)
            bot.send_message(chat_id,
            f"🔔 Уведомления включены!\n"
            f"Буду писать когда монета вырастет на {ALERT_THRESHOLD}%+")

    elif message.text == "📈 График монеты":
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for name in COINS:
            keyboard.add(types.KeyboardButton(f"📈 {name}"))
        keyboard.add(types.KeyboardButton("🏠 Главное меню"))
        bot.send_message(chat_id,
        "Выбери монету для графика:",
        reply_markup=keyboard)

    elif message.text == "🏠 Главное меню":
        start(message)

    elif message.text == "💡 Что купить":
        bot.send_message(chat_id, "⏳ Анализирую...")
        data = get_all_prices()
        if not data:
            bot.send_message(chat_id, "❌ Ошибка!")
            return
        results = []
        for name, coin_id in COINS.items():
            price, change = safe_get(data, coin_id)
            if price is None:
                continue
            results.append((name, coin_id, price, change))
        results.sort(key=lambda x: x[3], reverse=True)
        top = results[0]
        worst = results[-1]
        text = "💡 Анализ рынка:\n\n"
        text += f"🏆 Лучший рост:\n"
        text += f"{top[0]}\n"
        text += f"${top[2]:,.4f} | +{top[3]:.2f}%\n\n"
        text += f"⚠️ Осторожно:\n"
        text += f"{worst[0]}\n"
        text += f"${worst[2]:,.4f} | {worst[3]:.2f}%\n\n"
        text += "⚠️ Это не финансовый совет!\nВсегда делай собственный анализ!"
        bot.send_message(chat_id, text)

    elif message.text.startswith("📈 "):
        coin_name = message.text[3:]
        if coin_name in COINS:
            bot.send_message(chat_id, "⏳ Строю график...")
            coin_id = COINS[coin_name]
            prices = get_history(coin_id)
            if not prices:
                bot.send_message(chat_id, "❌ Ошибка!")
                return
            chart = draw_chart(prices)
            bot.send_message(chat_id,
            f"📈 {coin_name}\n\n{chart}")

bot.polling()
bot = telebot.TeleBot("782829974:AAFkxMdDpodQ-WX7tEh0kPynKZZ4ylK4k8g")
import os
bot = telebot.TeleBot(os.getenv("782829974:AAFkxMdDpodQ-WX7tEh0kPynKZZ4ylK4k8g"))
