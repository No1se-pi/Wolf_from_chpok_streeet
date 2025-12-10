from telebot import TeleBot, types
import time 
from api.lis_skins import LisSkinsAPI
from api.cs_market import CSMarketAPI
from utils.helpers import format_results, validate_price_input
import config

# Состояния для бота
user_states = {}

def setup_handlers(bot: TeleBot):
    
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('🔍 Поиск скинов')
        markup.add('⚙️ Настройки')
        
        welcome_text = (
            "👋 Привет! Я бот для поиска скинов CS2!\n\n"
            "Я могу искать скины на следующих маркетах:\n"
            "• Lis Skins (lis-skins.ru)\n"
            "• CS.Money (cs.money)\n\n"
            "Используйте кнопки ниже или команды:\n"
            "/search - Поиск скинов\n"
            "/help - Помощь\n"
        )
        
        bot.send_message(
            message.chat.id,
            welcome_text,
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    @bot.message_handler(commands=['search'])
    def start_search(message):
        user_states[message.chat.id] = 'waiting_skin_name'
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('❌ Отмена')
        
        bot.send_message(
            message.chat.id,
            "🔍 Введите название скина для поиска (например: 'AK-47 Redline'):",
            reply_markup=markup
        )
    
    @bot.message_handler(func=lambda message: message.text == '🔍 Поиск скинов')
    def search_button(message):
        start_search(message)
    
    @bot.message_handler(func=lambda message: message.text == '❌ Отмена')
    def cancel_search(message):
        if message.chat.id in user_states:
            del user_states[message.chat.id]
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('🔍 Поиск скинов')
        markup.add('⚙️ Настройки')
        
        bot.send_message(
            message.chat.id,
            "❌ Поиск отменен",
            reply_markup=markup
        )
    
    @bot.message_handler(func=lambda message: user_states.get(message.chat.id) == 'waiting_skin_name')
    def get_skin_name(message):
        skin_name = message.text.strip()
        if not skin_name or skin_name == '❌ Отмена':
            cancel_search(message)
            return
        
        user_states[message.chat.id] = {
            'state': 'waiting_price_filter',
            'skin_name': skin_name
        }
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Без фильтра цены', '❌ Отмена')
        
        bot.send_message(
            message.chat.id,
            f"🔍 Ищем: *{skin_name}*\n\n"
            "💰 Введите максимальную цену (например: 1000) или 'Без фильтра цены':",
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    @bot.message_handler(func=lambda message: 
                         user_states.get(message.chat.id, {}).get('state') == 'waiting_price_filter')
    def get_price_filter(message):
        user_data = user_states.get(message.chat.id, {})
        skin_name = user_data.get('skin_name', '')
        
        if message.text == '❌ Отмена':
            cancel_search(message)
            return
        
        max_price = None
        if message.text != 'Без фильтра цены':
            max_price = validate_price_input(message.text)
            if max_price is None:
                bot.send_message(
                    message.chat.id,
                    "❌ Неверный формат цены. Введите число или 'Без фильтра цены':"
                )
                return
        
        user_states[message.chat.id] = {
            'state': 'waiting_market',
            'skin_name': skin_name,
            'max_price': max_price
        }
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add('Все маркеты', 'Lis Skins', 'CS.Money', '❌ Отмена')
        
        bot.send_message(
            message.chat.id,
            f"🔍 Ищем: *{skin_name}*\n"
            f"💰 Макс. цена: {'Не указана' if not max_price else f'{max_price} RUB'}\n\n"
            "🏪 Выберите маркет для поиска:",
            reply_markup=markup,
            parse_mode='Markdown'
        )
    
    @bot.message_handler(func=lambda message: 
                         user_states.get(message.chat.id, {}).get('state') == 'waiting_market')
    def perform_search(message):
        user_data = user_states.get(message.chat.id, {})
        
        if message.text == '❌ Отмена':
            cancel_search(message)
            return
        
        skin_name = user_data.get('skin_name', '')
        max_price = user_data.get('max_price')
        market_filter = None
        
        if message.text == 'Lis Skins':
            market_filter = 'Lis Skins'
        elif message.text == 'CS.Money':
            market_filter = 'CS.Money'
        
        # Удаляем состояние
        if message.chat.id in user_states:
            del user_states[message.chat.id]
        
        # Отправляем сообщение о начале поиска
        search_msg = bot.send_message(
            message.chat.id,
            f"🔎 *Ищу скины...*\n\n"
            f"Название: *{skin_name}*\n"
            f"Маркет: *{market_filter or 'Все'}*\n"
            f"Макс. цена: *{max_price or 'Не указана'}*",
            parse_mode='Markdown'
        )
        
        # Выполняем поиск
        all_results = []
        
        if not market_filter or market_filter == 'Lis Skins':
            lis_results = LisSkinsAPI.search_skins(skin_name, max_price)
            all_results.extend(lis_results)
        
        if not market_filter or market_filter == 'CS.Money':
            cs_results = CSMarketAPI.search_skins(skin_name, max_price)
            all_results.extend(cs_results)
        
        # Форматируем и отправляем результаты
        if all_results:
            response = format_results(all_results, market_filter)
            
            # Проверяем длину сообщения (Telegram ограничение 4096 символов)
            if len(response) > 4000:
                response = response[:4000] + "\n\n⚠️ Результаты обрезаны из-за ограничения Telegram"
            
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=search_msg.message_id,
                text=response,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
        else:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=search_msg.message_id,
                text="🚫 *Скины не найдены*\n\nПопробуйте изменить параметры поиска.",
                parse_mode='Markdown'
            )
        
        # Возвращаем основную клавиатуру
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('🔍 Поиск скинов')
        markup.add('⚙️ Настройки')
        
        bot.send_message(
            message.chat.id,
            "Что дальше?",
            reply_markup=markup
        )
    
    @bot.message_handler(commands=['help'])
    def send_help(message):
        help_text = (
            "📖 *Помощь по использованию бота*\n\n"
            "*/start* - Главное меню\n"
            "*/search* - Начать поиск скинов\n"
            "*/help* - Эта справка\n\n"
            "*Как искать:*\n"
            "1. Нажмите '🔍 Поиск скинов' или /search\n"
            "2. Введите название скина\n"
            "3. Укажите максимальную цену (опционально)\n"
            "4. Выберите маркет для поиска\n\n"
            "*Поддерживаемые маркеты:*\n"
            "• Lis Skins (lis-skins.ru)\n"
            "• CS.Money (cs.money)\n\n"
            "Бот покажет самые дешевые варианты!"
        )
        
        bot.send_message(
            message.chat.id,
            help_text,
            parse_mode='Markdown'
        )
    
    @bot.message_handler(func=lambda message: True)
    def handle_other(message):
        if message.chat.id not in user_states:
            bot.send_message(
                message.chat.id,
                "Используйте кнопки или команды:\n"
                "/start - Главное меню\n"
                "/search - Поиск скинов\n"
                "/help - Помощь"
            )

    @bot.message_handler(commands=['test'])
    def test_search(message):
        """Тестовая команда для проверки поиска"""
        test_msg = bot.send_message(
            message.chat.id,
            "🔍 *Тестирую поиск...*",
            parse_mode='Markdown'
        )
        
        # Тестовые поиски
        test_skins = [
            ("AK-47 Redline", 5000),
            ("Desert Eagle", 1000),
            ("AWP", 10000)
        ]
        
        for skin_name, max_price in test_skins:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=test_msg.message_id,
                text=f"🔍 *Тестирую поиск:* {skin_name} (макс. {max_price} руб)",
                parse_mode='Markdown'
            )
            
            # Тест Lis Skins
            lis_results = LisSkinsAPI.search_skins(skin_name, max_price)
            time.sleep(1)
            
            # Тест CS.Money
            cs_results = CSMarketAPI.search_skins(skin_name, max_price)
            time.sleep(1)
            
            all_results = lis_results + cs_results
            
            if all_results:
                response = f"✅ *{skin_name}:* найдено {len(all_results)} скинов\n"
                for skin in all_results[:3]:
                    response += f"• {skin['name'][:30]}: {skin['price']} руб ({skin['market']})\n"
                bot.send_message(message.chat.id, response, parse_mode='Markdown')
            else:
                bot.send_message(message.chat.id, f"❌ *{skin_name}:* скины не найдены", parse_mode='Markdown')
        
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=test_msg.message_id,
            text="✅ *Тестирование завершено*",
            parse_mode='Markdown'
        )   