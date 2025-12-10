import telebot
import config
from handlers.main_handlers import setup_handlers

def main():
    # Проверка токена
    if not config.Config.BOT_TOKEN:
        print("❌ Ошибка: BOT_TOKEN не установлен!")
        print("Создайте файл .env и добавьте:")
        print("BOT_TOKEN=ваш_токен_бота")
        return
    
    # Инициализация бота
    bot = telebot.TeleBot(config.Config.BOT_TOKEN)
    
    # Настройка обработчиков
    setup_handlers(bot)
    
    print("🤖 Бот запущен...")
    print("Бот работает в режиме опроса (polling)")
    
    # Запуск бота
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"❌ Ошибка при работе бота: {e}")

if __name__ == "__main__":
    main()