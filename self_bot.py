import discord
from discord.ext import commands

# ================================================================
#  COMPATIBILITY LAYER (MEMPERBAIKI ERROR Intents & bot=False)
# ================================================================
# 1. Mock discord.Intents jika tidak ada
if not hasattr(discord, 'Intents'):
    class MockIntents:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        @classmethod
        def default(cls):
            return cls()
        @classmethod
        def all(cls):
            return cls()
        def __setattr__(self, name, value):
            self.__dict__[name] = value
    discord.Intents = MockIntents

# 2. Monkeypatch discord.Client.run untuk mengabaikan parameter 'bot'
original_run = discord.Client.run
def patched_run(self, *args, **kwargs):
    kwargs.pop('bot', None)
    return original_run(self, *args, **kwargs)
discord.Client.run = patched_run

import asyncio
import sys
import config
import time
import random
from datetime import datetime
from collections import deque

# Set encoding
sys.stdout.reconfigure(encoding='utf-8')

# ================================================================
#  LOGGER
# ================================================================
def log(level, msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    emoji = {
        "INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️",
        "ERROR": "❌", "RATE": "⏳", "DEBUG": "🔍", "CRITICAL": "🚨"
    }.get(level, "📌")
    print(f"[{timestamp}] {emoji} {msg}")

# ================================================================
#  INISIALISASI INTENTS (SEKARANG AMAN)
# ================================================================
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", self_bot=True, intents=intents)

# ================================================================
#  VARIABEL KEAMANAN
# ================================================================
forward_queue = asyncio.Queue()
is_processing = False
recent_forwarded = deque(maxlen=100)
forward_count_this_hour = 0
hour_start_time = time.time()
MAX_FORWARD = config.MAX_FORWARD_PER_HOUR
current_cooldown = 2.0
emergency_stop = False
emergency_reason = ""

# ================================================================
#  FUNGSI PROSES FORWARD (NATIVE + AMAN)
# ================================================================
async def process_forward_queue():
    global is_processing, forward_count_this_hour, hour_start_time, current_cooldown, emergency_stop, emergency_reason

    if is_processing:
        return
    if emergency_stop:
        log("CRITICAL", f"🚫 BOT DIHENTIKAN: {emergency_reason}")
        return

    is_processing = True
    log("INFO", "🔄 Memulai proses antrian...")

    try:
        while not forward_queue.empty():
            if emergency_stop:
                break

            # Rate limit per jam
            now = time.time()
            if now - hour_start_time >= 3600:
                forward_count_this_hour = 0
                hour_start_time = now
                log("INFO", "🔄 Counter per jam direset.")

            if forward_count_this_hour >= MAX_FORWARD:
                wait_time = 3600 - (now - hour_start_time)
                log("WARNING", f"⏳ Batas forward/jam ({MAX_FORWARD}). Tunggu {wait_time/60:.1f} menit.")
                await asyncio.sleep(wait_time + 5)
                continue

            message = await forward_queue.get()
            msg_id = f"{message.id}_{message.channel.id}"

            # Anti-duplikat
            if msg_id in recent_forwarded:
                log("DEBUG", f"⏭️ Lewati duplikat: {message.author.name}")
                forward_queue.task_done()
                continue

            # Jeda acak
            delay = random.uniform(config.MIN_DELAY, config.MAX_DELAY)
            log("DEBUG", f"⏳ Jeda {delay:.1f}s sebelum forward...")
            await asyncio.sleep(delay)

            # ============================================================
            #  METODE FORWARD NATIVE (MENGGUNAKAN message.forward)
            # ============================================================
            try:
                target_channel = bot.get_channel(config.TARGET_CHANNEL_ID)
                if not target_channel:
                    target_channel = await bot.fetch_channel(config.TARGET_CHANNEL_ID)

                # Forward asli, label "Forwarded" muncul otomatis, aman lintas channel
                await message.forward(target_channel)

                recent_forwarded.append(msg_id)
                forward_count_this_hour += 1
                log("SUCCESS", f"✅ Forward dari {message.author.name} ({forward_count_this_hour}/{MAX_FORWARD})")

                if current_cooldown > config.MIN_DELAY:
                    current_cooldown = max(config.MIN_DELAY, current_cooldown - 0.5)

            except discord.HTTPException as e:
                if e.status == 429:
                    retry_after = e.retry_after
                    current_cooldown = min(config.MAX_COOLDOWN, current_cooldown * 1.5)
                    log("RATE", f"⚠️ Rate limit! Tunggu {retry_after:.1f}s (cooldown: {current_cooldown:.1f}s)")
                    if current_cooldown >= config.MAX_COOLDOWN:
                        log("CRITICAL", "🚨 Cooldown maksimum! Risiko mute/ban tinggi.")
                    await asyncio.sleep(retry_after + 1)
                    await forward_queue.put(message)
                    await asyncio.sleep(current_cooldown)
                else:
                    log("ERROR", f"❌ Gagal forward (HTTP {e.status})")
                    if e.status in (403, 401):
                        emergency_stop = True
                        emergency_reason = f"Token invalid atau akses ditolak (HTTP {e.status})"
                        log("CRITICAL", f"🚨 {emergency_reason}")
                        break
            except Exception as e:
                log("ERROR", f"❌ Error: {type(e).__name__} - {e}")
                emergency_stop = True
                emergency_reason = f"Error berulang: {type(e).__name__}"
                log("CRITICAL", f"🚨 {emergency_reason} — Bot dihentikan.")
                break

            forward_queue.task_done()
            await asyncio.sleep(0.5)

        if not emergency_stop:
            log("SUCCESS", "🏁 Antrian selesai.")

    finally:
        is_processing = False

# ================================================================
#  EVENT ON_READY
# ================================================================
@bot.event
async def on_ready():
    log("SUCCESS", f"👑 Self-Bot aktif: {bot.user.name} (ID: {bot.user.id})")
    log("INFO", f"📡 Server: {config.SOURCE_GUILD_IDS}")
    log("INFO", f"📡 Channel: {config.SOURCE_CHANNEL_IDS}")
    log("INFO", f"🎯 Target mention: {config.MONITORED_USER_IDS}")
    log("INFO", f"📤 Target Server: {getattr(config, 'TARGET_GUILD_ID', 'Tidak diset')}")
    log("INFO", f"📤 Target Channel: {config.TARGET_CHANNEL_ID}")
    log("INFO", f"🛡️ Maks forward/jam: {MAX_FORWARD}")
    log("SUCCESS", "✅ Bot siap dan AMAN.")

# ================================================================
#  EVENT ON_MESSAGE
# ================================================================
@bot.event
async def on_message(message):
    global emergency_stop
    if emergency_stop or message.author.id == bot.user.id:
        return

    if config.SOURCE_GUILD_IDS and (message.guild is None or message.guild.id not in config.SOURCE_GUILD_IDS):
        return
    if config.SOURCE_CHANNEL_IDS and message.channel.id not in config.SOURCE_CHANNEL_IDS:
        return

    mentioned_ids = {u.id for u in message.mentions}
    if config.MONITORED_USER_IDS:
        if not any(uid in mentioned_ids for uid in config.MONITORED_USER_IDS):
            return
    else:
        if bot.user.id not in mentioned_ids:
            return

    log("INFO", f"🔔 Mention dari {message.author.name} di #{message.channel.name}")
    await forward_queue.put(message)
    await process_forward_queue()

# ================================================================
#  JALANKAN (DENGAN bot=False)
# ================================================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    log("INFO", "🚀 Memulai Self-Bot Forwarder...")
    print("=" * 60)

    if len(config.USER_TOKEN) < 20:
        log("CRITICAL", "❌ Token terlalu pendek. Periksa config.py.")
        sys.exit(1)

    try:
        bot.run(config.USER_TOKEN, bot=False)  # Layer kompatibilitas akan mengabaikan 'bot=False'
    except discord.LoginFailure:
        log("CRITICAL", "❌ Gagal login! Token invalid.")
    except KeyboardInterrupt:
        log("WARNING", "🛑 Bot dimatikan.")
    except Exception as e:
        log("CRITICAL", f"❌ Error fatal: {e}")