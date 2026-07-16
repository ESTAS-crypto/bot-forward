# ================================================================
#  KONFIGURASI SELF-BOT FORWARDER
# ================================================================

# TOKEN AKUN DISCORD (WAJIB RESET PASSWORD DULU, AMBIL TOKEN BARU!)
USER_TOKEN = "MTA2MDI1NzQzMjgyMTA1OTYxNg.GL_3HL.W50EU6DVS3uvmnotW3fWEXGj81d_P90vRIuVUc"

# ================================================================
#  SUMBER — Server & Channel yang dipantau mention-nya
# ================================================================

# Server ID tempat mention dipantau (kosong = semua server)
SOURCE_GUILD_IDS = [1029716623977873501]

# Channel ID tempat mention dipantau (kosong = semua channel)
SOURCE_CHANNEL_IDS = [1140437767084576918]

# ================================================================
#  USER YANG DIPANTAU — Siapa yang kalau di-mention akan di-forward
#  Kosong = pantau mention ke akun self-bot sendiri
# ================================================================

MONITORED_USER_IDS = [1031011414053228625]  # User ID leonardo

# ================================================================
#  TUJUAN — Channel tempat pesan di-forward
# ================================================================

TARGET_GUILD_ID = 1521513456241475645 # Server ID tujuan
TARGET_CHANNEL_ID = 1521566079309058169

# ================================================================
#  PENGATURAN KEAMANAN (JANGAN DIUBAH KECUALI PAHAM RISIKO)
# ================================================================

# Maksimum forward per jam (30 = sangat aman)
MAX_FORWARD_PER_HOUR = 30

# Jeda minimum dan maksimum antar forward (detik) — acak agar tidak terdeteksi
MIN_DELAY = 2.0
MAX_DELAY = 3.0

# Jika kena rate limit (HTTP 429), cooldown akan dikalikan dengan faktor ini
COOLDOWN_MULTIPLIER = 1.5

# Batas maksimum cooldown (detik)
MAX_COOLDOWN = 60.0