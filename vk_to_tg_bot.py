import vk_api
import telebot
import time
import logging
from configparser import ConfigParser

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')

config = ConfigParser()
config.read('config.ini')

VK_TOKEN = config.get('VK', 'token')
GROUPS = [int(g.strip()) for g in config.get('VK', 'groups').split(',')]
TG_TOKEN = config.get('TELEGRAM', 'bot_token')
CHANNEL = config.get('TELEGRAM', 'channel')
CHECK_INTERVAL = config.getint('SETTINGS', 'check_interval')

LAST_POST_IDS = [int(id.strip()) for id in config.get('SETTINGS', 'last_post_ids', fallback='0').split(',')]

vk = vk_api.VkApi(token=VK_TOKEN).get_api()
bot = telebot.TeleBot(TG_TOKEN)

# 🎯 НАЗВАНИЯ ВАШИХ ГРУПП
GROUP_NAMES = {
    102632131: "✈️ Сибирский споттинг",
    77477794: "📸 Споттинг в Новосибирске", 
    90641273: "🚂 Западно-Сибирская железная дорога",
    190105113: "🛬 Аэропорт глазами наземных служб",
    207064867: "🌍 Авиация Сибири | споттинг"
}

def get_posts(group_id):
    try:
        return vk.wall.get(owner_id=f'-{group_id}', count=10)['items']
    except:
        return []

def send_post(post, group_id):
    try:
        group_name = GROUP_NAMES.get(group_id, f"Группа {group_id}")
        text = post.get('text', '')[:2800]
        atts = post.get('attachments', [])
        photos = []
        
        # Извлекаем фото
        for att in atts:
            if att.get('type') == 'photo':
                photo = att['photo']
                for size in ['photo_1280', 'photo_807', 'photo_604']:
                    if size in photo:
                        photos.append(photo[size])
                        break
        
        # Ссылка на пост
        url = f"https://vk.com/wall-{abs(post['owner_id'])}_{post['id']}"
        
        # Формируем сообщение
        caption = f"{group_name}\n\n{text}\n\n🔗 <a href='{url}'>Читать на VK</a>"
        
        if photos:
            # Фото + название группы
            if len(caption) > 1024:
                caption = caption[:1021] + "..."
            bot.send_photo(CHANNEL, photos[0], caption=caption, parse_mode='HTML')
            logging.info(f"🖼️  {group_name} → {CHANNEL}")
        else:
            # Текст + название группы
            bot.send_message(CHANNEL, caption, parse_mode='HTML', disable_web_page_preview=False)
            logging.info(f"📝  {group_name} → {CHANNEL}")
        
        return True
    except Exception as e:
        logging.error(f"❌ Ошибка поста {post.get('id')}: {e}")
        return False

def main():
    logging.info(f"🚀 Bot started!")
    logging.info(f"📱 Группы: {[GROUP_NAMES.get(g, g) for g in GROUPS]}")
    logging.info(f"📢 Канал: {CHANNEL}")
    logging.info(f"⏱️  Интервал: {CHECK_INTERVAL}с")
    
    while True:
        for i, gid in enumerate(GROUPS):
            posts = get_posts(gid)
            for post in reversed(posts):
                if post['id'] > LAST_POST_IDS[i]:
                    if send_post(post, gid):
                        LAST_POST_IDS[i] = post['id']
        
        # Сохранение прогресса
        config.set('SETTINGS', 'last_post_ids', ','.join(map(str, LAST_POST_IDS)))
        with open('config.ini', 'w') as f:
            config.write(f)
        
        logging.info(f"😴 Ожидание {CHECK_INTERVAL}с...")
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    main()
