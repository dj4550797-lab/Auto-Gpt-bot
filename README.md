# FLIXORA AI - Advanced Telegram Bot

This is a complete, production-ready Telegram AI assistant bot named FLIXORA AI. It features a modular architecture, webhook deployment, and a rich feature set including user registration, premium monetization, and a full admin panel.

## Features
- **AI Chat**: Powered by OpenRouter, with model selection and conversation memory.
- **Login System**: Secure user registration using `ConversationHandler`.
- **Monetization**: Manual UPI payment system with admin approval.
- **Verification System**: Forces users to verify via a URL shortener every 24 hours.
- **Admin Panel**: Full control over users, payments, and bot broadcasts.
- **High Performance**: Asynchronous operations, response caching, rate limiting.
- **Docker Ready**: Fully configured for deployment on services like Render or Heroku.

## Setup & Deployment

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/flixora-ai-pro.git
    cd flixora-ai-pro
    ```
2.  **Create a `.env` file:**
    Copy the contents of `.env.example` into a new file named `.env` and fill in your credentials.

3.  **Deploy to Render:**
    - Create a new "Web Service" on Render and connect your GitHub repository.
    - Select "Docker" as the environment.
    - Add all the variables from your `.env` file to the "Environment Variables" section on Render.
    - Render will automatically build and deploy the bot.

## Environment Variables
See `.env.example` for the full list of required variables. Key variables include:
- `BOT_TOKEN`
- `MONGO_URI`
- `ADMIN_IDS`
- `LOG_CHANNEL`
- `WEBHOOK_URL`
- `OPENROUTER_API_KEY`