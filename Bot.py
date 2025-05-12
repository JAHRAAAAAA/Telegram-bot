import os
import re
import tempfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import yt_dlp

import os
TOKEN = os.getenv("BOT_TOKEN")

# Fungsi download media
def download_media(url, audio_only=False):
    with tempfile.TemporaryDirectory() as temp_dir:
        ydl_opts = {
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'format': 'bestaudio/best' if audio_only else 'best',
            'noplaylist': True,
        }

        if audio_only:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            if audio_only:
                filename = os.path.splitext(filename)[0] + ".mp3"

            return filename


# Handler /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Kirimkan link dari YouTube, TikTok, Facebook, Instagram, dll. Saya akan download untukmu!")


# Handler pesan teks (URL)
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    # Validasi URL sederhana
    if not re.match(r'^https?://', url):
        await update.message.reply_text("Silakan kirimkan URL yang valid.")
        return

    # Simpan URL ke user_data
    context.user_data['url'] = url

    # Tombol inline
    keyboard = [
        [
            InlineKeyboardButton("🎥 Download Video", callback_data='video'),
            InlineKeyboardButton("🎵 Download Audio", callback_data='audio')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Pilih format download:", reply_markup=reply_markup)


# Handler tombol inline
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url = context.user_data.get('url')
    choice = query.data  # 'video' or 'audio'

    try:
        await query.edit_message_text("Sedang mendownload...")

        file_path = download_media(url, audio_only=(choice == 'audio'))

        caption = "Ini adalah file yang kamu minta!"
        await query.message.reply_document(document=open(file_path, 'rb'), caption=caption)

        # Hapus file setelah dikirim
        os.remove(file_path)

    except Exception as e:
        await query.message.reply_text(f"Terjadi kesalahan: {e}")


# Main function
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(button_handler))

    await app.run_polling()


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
