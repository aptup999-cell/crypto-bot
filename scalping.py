import telebot
import requests
import threading
import time
from telebot import types

bot = telebot.TeleBot("782829974:AAFkxMdDpodQ-WX7tEh0kPynKZZ4ylK4k8g")

ADMIN_ID = 582726993

# Монеты для скальпинга
COINS = {
    "₿ Bitcoin": "BTCUSDT",
    "🔷 Ethereum": "ETHUSDT",
    "🟣 Solana": "SOLUSDT",
    "🔴 XRP": "XRPUSDT",
    "🐶 Dogecoin": "DOGEUSDT",
    "🔵 BNB": "BNBUSDT",
    "🟠 Avalanche": "AVAXUSDT",
    "🔗 Chainlink": "LINKUSDT",
    "🌐 Polygon": "MATICUSDT",
    "⚡ Tron": "TRXUSDT",
    "🌊 Stellar": "XLMUSDT",
    "🔰 Uniswap": "UNIUSDT",
    "🌀 Monero": "XMRUSDT",
    "💎 Cosmos": "ATOMUSDT",
    "🏦 Arbitrum": "ARBUSDT",
    "🔹 Polkadot": "DOTUSDT",
    "🟡 Cardano": "ADAUSDT",
    "🚀 Pepe": "PEPEUSDT",
    "🦊 Shiba Inu": "SHIBUSDT",
    "🌕 Litecoin": "LTCUSDT",
    "🔮 Sui": "SUIUSDT",
    "🌍 Near": "NEARUSDT",
    "⚙️ Filecoin": "FILUSDT",
    "🎮 Sandbox": "SANDUSDT",
    "🏗 Injective": "INJUSDT",
    "🔥 Optimism": "OPUSDT",
    "🌱 Aptos": "APTUSDT",
    "💫 Render": "RENDERUSDT",
    "🦁 Sei": "SEIUSDT",
    "🧬 Fetch AI": "FETUSDT"
}


subscribers = set()

def get_price_binance(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        r = requests.get(url, timeout=10)
        data = r.json()
        return {
            "price": float(data["lastPrice"]),
            "change": float(data["priceChangePercent"]),
            "volume": float(data["volume"]),
            "high": float(data["highPrice"]),
            "low": float(data["lowPrice"])
        }
    except:
        return None

def get_rsi(symbol):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&limit=15"
        r = requests.get(url, timeout=10)
        candles = r.json()
        closes = [float(c[4]) for c in candles]

        gains = []
        losses = []
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i-1]
            if diff > 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(diff))

        avg_gain = sum(gains) / len(gains)
        avg_loss = sum(losses) / len(losses)

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)
    except:
        return None

def get_support_resistance(symbol):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=24"
        r = requests.get(url, timeout=10)
        candles = r.json()
        highs = [float(c[2]) for c in candles]
        lows = [float(c[3]) for c in candles]
        resistance = max(highs)
        support = min(lows)
        return support, resistance
    except:
        return None, None

def get_signal(rsi, change):
    if rsi is None:
        return "❓ Нет данных"
    if rsi < 30:
        return "🟢 ПОКУПАТЬ — перепродан!"
    elif rsi > 70:
        return "🔴 ПРОДАВАТЬ — перекуплен!"
    elif rsi < 45 and change > 0:
        return "🟡 Возможен рост"
    elif rsi > 55 and change < 0:
        return "🟡 Возможно падение"
    else:
        return "⚪ Нейтрально — ждать"

# Авто мониторинг каждую минуту
def auto_monitor():
    while True:
        time.sleep(60)
        if not subscribers:
            continue
        for name, symbol in COINS.items():
            data = get_price_binance(symbol)
            rsi = get_rsi(symbol)
            if not data or rsi is None:
                continue
            signal = get_signal(rsi, data["change"])
            if "ПОКУПАТЬ" in signal or "ПРОДАВАТЬ" in signal:
                support, resistance = get_support_resistance(symbol)
                price = data["price"]
                text = f"🚨 Сигнал! {name}\n\n"
                text += f"💵 Цена: ${price:,.4f}\n"
                text += f"📊 RSI: {rsi}\n"
                text += f"📈 Изменение: {data['change']:+.2f}%\n"
                text += f"🎯 Сигнал: {signal}\n"
                if support and resistance:
                    text += f"\n🟢 Поддержка: ${support:,.4f}"
                    text += f"\n🔴 Сопротивление: ${resistance:,.4f}"
                    if abs(price - support) / price < 0.02:
                        text += "\n⚠️ Цена близко к поддержке!"
                    if abs(price - resistance) / price < 0.02:
                        text += "\n⚠️ Цена близко к сопротивлению!"
                for chat_id in subscribers:
                    try:
                        bot.send_message(chat_id, text)
                    except:
                        pass

thread = threading.Thread(target=auto_monitor)
thread.daemon = True
thread.start()

@bot.message_handler(commands=['start'])
def start(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("📊 Анализ монеты"))
    keyboard.add(types.KeyboardButton("🔔 Включить сигналы"))
    keyboard.add(types.KeyboardButton("💰 Все цены"))
    bot.send_message(message.chat.id,
    "📈 Скальпинг бот!\n\n"
    "Анализирую RSI, объём, поддержку и сопротивление\n"
    "Даю сигналы когда покупать и продавать! 🎯",
    reply_markup=keyboard)

@bot.message_handler(func=lambda message: True)
def handle(message):
    chat_id = message.chat.id

    if message.text == "📊 Анализ монеты":
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for name in COINS:
            keyboard.add(types.KeyboardButton(f"🔍 {name}"))
        keyboard.add(types.KeyboardButton("🏠 Меню"))
        bot.send_message(chat_id, "Выбери монету:", reply_markup=keyboard)

    elif message.text == "🏠 Меню":
        start(message)

    elif message.text == "🔔 Включить сигналы":
        if chat_id in subscribers:
            subscribers.remove(chat_id)
            bot.send_message(chat_id, "🔕 Сигналы выключены!")
        else:
            subscribers.add(chat_id)
            bot.send_message(chat_id,
            "🔔 Сигналы включены!\n"
            "Буду писать каждую минуту когда RSI даёт сигнал! 🎯")

    elif message.text == "💰 Все цены":
        bot.send_message(chat_id, "⏳ Загружаю...")
        text = "💰 Цены в реальном времени:\n\n"
        for name, symbol in COINS.items():
            data = get_price_binance(symbol)
            if not data:
                continue
            arrow = "🟢" if data["change"] > 0 else "🔴"
            text += f"{arrow} {name}\n"
            text += f"   ${data['price']:,.4f} | {data['change']:+.2f}%\n\n"
        bot.send_message(chat_id, text)

    elif message.text.startswith("🔍 "):
        coin_name = message.text[3:]
        if coin_name in COINS:
            bot.send_message(chat_id, "⏳ Анализирую...")
            symbol = COINS[coin_name]
            data = get_price_binance(symbol)
            rsi = get_rsi(symbol)
            support, resistance = get_support_resistance(symbol)

            if not data:
                bot.send_message(chat_id, "❌ Ошибка!")
                return

            signal = get_signal(rsi, data["change"] if data else 0)
            price = data["price"]

            text = f"📊 Анализ {coin_name}:\n\n"
            text += f"💵 Цена: ${price:,.4f}\n"
            text += f"📈 Изменение 24ч: {data['change']:+.2f}%\n"
            text += f"📊 Объём: {data['volume']:,.0f}\n"
            text += f"⬆️ Максимум 24ч: ${data['high']:,.4f}\n"
            text += f"⬇️ Минимум 24ч: ${data['low']:,.4f}\n\n"

            if rsi:
                text += f"📉 RSI (1м): {rsi}\n"
                if rsi < 30:
                    text += "   ⚡ Перепродан — сигнал на покупку!\n"
                elif rsi > 70:
                    text += "   ⚡ Перекуплен — сигнал на продажу!\n"
                else:
                    text += "   ⚪ Нейтральная зона\n"

            if support and resistance:
                text += f"\n🟢 Поддержка: ${support:,.4f}\n"
                text += f"🔴 Сопротивление: ${resistance:,.4f}\n"
                if abs(price - support) / price < 0.02:
                    text += "⚠️ Цена близко к поддержке!\n"
                if abs(price - resistance) / price < 0.02:
                    text += "⚠️ Цена близко к сопротивлению!\n"

            text += f"\n🎯 Сигнал: {signal}"
            bot.send_message(chat_id, text)

bot.polling()
