# 🤖 FLIXORA AI — The Ultimate JARVIS Experience

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Telegram-v20.7-blue?style=for-the-badge&logo=telegram&logoColor=white" />
  <img src="https://img.shields.io/badge/Database-MongoDB-green?style=for-the-badge&logo=mongodb&logoColor=white" />
  <img src="https://img.shields.io/badge/Deployment-Docker-blue?style=for-the-badge&logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/Maintained%3F-Yes-orange?style=for-the-badge" />
</p>

---

## 🌟 Introduction
**FLIXORA AI** is a high-performance, modular Telegram AI bot system built using the **python-telegram-bot (v20+)** framework. Inspired by JARVIS, it provides a seamless AI chat experience with a professional UI, automated user registration, revenue-generating verification loops, and a manual UPI-based premium system optimized for the Indian market.

---

## 🚀 Key Features

| Feature | Description |
| :--- | :--- |
| 🧠 **Multi-Model AI** | Powered by **OpenRouter**. Dynamically switch between GPT-4o, Claude 3, and Mixtral. |
| 🔑 **Smart Auth** | Mandatory registration system collecting Name, Email, Phone, and DOB. |
| 🔗 **Verification Loop** | Earn revenue! Users must verify via a URL shortener every 24 hours to keep access. |
| 💎 **UPI Premium** | Tiered subscription plans with manual admin approval via UTR & Screenshot. |
| 🛡️ **Pro Admin Panel** | Full control over bans (permanent/temp), premium logs, and global broadcasts. |
| ⚡ **Performance** | Flask Webhook integration for 24/7 stability on **Render** or **Heroku**. |

---

## 🎮 User Interface (UI)
The bot features a dual-menu stylish interface:

**Primary Menu:**
- 📥 `ADD ME TO GROUP` | 📢 `HELP` | 📖 `ABOUT`
- ⭐ `TOP SEARCHING` | 💎 `UPGRADE` | 🤖 `MORE BOTS`

**Secondary Menu:**
- 🧠 `Change Model` | 🗑 `Reset Chat`

**Animated Feedback:**
- 🔍 `Searching...` ➔ ⏳ `Thinking...` ➔ 📝 `Generated Response`

---

## 🛡️ Admin Command Center (Full Control)

Only users listed in `ADMIN_IDS` can access these commands:

> [!IMPORTANT]
> **User Management**
> - `/ban <user_id>` — Permanent ban.
> - `/tban <user_id> <days>` — Temporary ban with auto-unban.
> - `/unban <user_id>` — Remove any existing ban.
> - `/users` — View total, registered, and active user stats.

> [!TIP]
> **Financial & Premium Control**
> - `/premium <user_id> <days>` — Grant premium manually to any user.
> - `/remove_premium <user_id>` — Revoke premium status.
> - `/approve <user_id>` — Approve a pending UPI payment and notify the user.
> - `/reject <user_id> <reason>` — Reject payment and send reason to the user.
> - `/payments` — See all pending payment requests.

> [!CAUTION]
> **Global Broadcast**
> - `/broadcast` — (Reply to a message) Sends the message/media to every registered user.

---

## 💎 Premium Subscription Plans

Our manual UPI payment system (India Optimized) includes:
- ☀️ **Daily Pass**: ₹20 (1 Day Access - Bypass Shorteners)
- 📅 **Weekly Pass**: ₹79 (7 Days Access - Priority AI)
- 🌙 **Monthly Pass**: ₹199 (30 Days - Ultimate Jarvis Experience)

*Users submit UTR numbers and screenshots which admins approve via the command center.*

---

## ⚙️ Environment Configuration (`.env`)

Create a `.env` file in your root directory and fill it as follows:

```env
# --- TELEGRAM CORE ---
BOT_TOKEN=your_bot_token_here
WEBHOOK_URL=https://your-app-name.onrender.com
PORT=10000

# --- DATABASE & SECURITY ---
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/
LOG_CHANNEL=-1001234567890
ADMIN_IDS=12345678,98765432

# --- AI (OpenRouter) ---
OPENROUTER_API_KEY=sk-or-v1-your-key
MODEL_1=openai/gpt-4o-mini
MODEL_2=anthropic/claude-3-haiku
MODEL_3=mistralai/mixtral-8x7b

# --- SHORTENER & UPI ---
SHORTENER_API_URL=https://shrinkme.io/api
SHORTENER_API_TOKEN=your_token_here
UPI_ID=yourname@bank
QR_IMAGE_URL=https://link-to-your-qr.jpg

# --- UI ASSETS ---
WELCOME_IMAGE_URL=https://link-to-welcome-image.jpg
MORE_BOTS_URL=https://t.me/YourBotChannel
