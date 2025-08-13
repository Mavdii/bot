# 🕌 Islamic Azkar Telegram Bot

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://core.telegram.org/bots)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **بوت تيليجرام احترافي لإرسال الأذكار الإسلامية والتذكيرات الدينية للمجموعات**

A professional Telegram bot for sending Islamic remembrances (Azkar) and religious reminders to groups with automated scheduling and comprehensive admin management.

## ✨ Features | المميزات

### 🤖 Core Features
- **📿 Automated Azkar Delivery** - إرسال الأذكار تلقائياً
- **🌅 Morning & Evening Azkar** - أذكار الصباح والمساء
- **🕌 Prayer Time Reminders** - تذكيرات أوقات الصلاة
- **🎲 Smart Content Rotation** - تناوب ذكي للمحتوى
- **📱 Multi-Media Support** - دعم النصوص والصور والصوتيات

### 👑 Admin Features
- **🔧 Comprehensive Admin Panel** - لوحة تحكم شاملة
- **📝 Content Management** - إدارة المحتوى
- **📊 Real-time Statistics** - إحصائيات فورية
- **👥 Group Management** - إدارة المجموعات
- **🔒 Secure File Handling** - معالجة آمنة للملفات

### 🏗️ Technical Features
- **🔄 Modular Architecture** - هيكل معياري
- **⚡ Async/Await Support** - دعم البرمجة غير المتزامنة
- **🛡️ Error Handling** - معالجة شاملة للأخطاء
- **📝 Comprehensive Logging** - نظام سجلات متكامل
- **🔧 Environment Configuration** - تكوين متغيرات البيئة

## 🚀 Quick Start | البدء السريع

### Prerequisites | المتطلبات

- Python 3.11 or higher
- Telegram Bot Token ([Get one from @BotFather](https://t.me/botfather))
- Your Telegram User ID ([Get it from @userinfobot](https://t.me/userinfobot))

### Installation | التثبيت

1. **Clone the repository | استنساخ المستودع**
   ```bash
   git clone https://github.com/Mavdii/bot.git
   cd bot
   ```

2. **Create virtual environment | إنشاء بيئة افتراضية**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies | تثبيت التبعيات**
   ```bash
   pip install -e .
   ```

4. **Configure environment | تكوين البيئة**
   ```bash
   cp .env.example .env
   # Edit .env with your bot token and admin ID
   ```

5. **Run the bot | تشغيل البوت**
   ```bash
   python main.py
   ```

## ⚙️ Configuration | التكوين

### Environment Variables | متغيرات البيئة

Create a `.env` file in the project root:

```env
# Bot Configuration
BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_telegram_user_id
CHANNEL_LINK=https://t.me/your_channel

# Scheduling (optional)
TIMEZONE=Africa/Cairo
RANDOM_CONTENT_INTERVAL=5
MORNING_AZKAR_TIMES=05:30,07:00,08:00
EVENING_AZKAR_TIMES=18:00,19:00,20:00

# Logging (optional)
LOG_LEVEL=INFO
LOG_FILE=./logs/azkar_bot.log
```

### Content Setup | إعداد المحتوى

1. **Add Azkar texts | إضافة نصوص الأذكار**
   - Edit `data/content/azkar.txt`
   - Separate each azkar with `---`

2. **Add media files | إضافة ملفات الوسائط**
   ```
   data/content/
   ├── images/     # Random images
   ├── voices/     # Voice messages  
   ├── audios/     # Audio files
   ├── morning/    # Morning azkar images
   ├── evening/    # Evening azkar images
   └── prayers/    # Prayer-related images
   ```

## 📖 Usage | الاستخدام

### For Users | للمستخدمين

1. **Add bot to your group | إضافة البوت للمجموعة**
2. **Grant send messages permission | منح صلاحية إرسال الرسائل**
3. **Bot starts automatically | البوت يبدأ تلقائياً**

### For Admins | للمشرفين

Send `/admin` to access the admin panel with features:

- 📝 Add new azkar texts
- 🖼️ Upload images
- 🎙️ Upload voice messages
- 🎵 Upload audio files
- 📊 View statistics
- 👥 Manage groups

## 🏗️ Project Structure | هيكل المشروع

```
telegram-azkar-bot/
├── src/azkar_bot/           # Main package
│   ├── core/                # Core components
│   │   ├── bot.py          # Main bot class
│   │   ├── config.py       # Configuration management
│   │   └── scheduler.py    # Scheduling system
│   ├── handlers/           # Message handlers
│   │   ├── admin.py        # Admin operations
│   │   ├── messages.py     # Message processing
│   │   └── callbacks.py    # Callback queries
│   ├── services/           # Business logic
│   │   ├── content_manager.py
│   │   ├── file_manager.py
│   │   └── group_manager.py
│   ├── models/             # Data models
│   │   ├── content.py
│   │   └── group.py
│   └── utils/              # Utilities
│       ├── logger.py
│       ├── helpers.py
│       └── constants.py
├── data/                   # Data storage
│   ├── content/           # Content files
│   └── groups/            # Group data
├── tests/                 # Test suite
├── docs/                  # Documentation
└── scripts/               # Utility scripts
```

## 🔧 Development | التطوير

### Setup Development Environment | إعداد بيئة التطوير

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Format code
black src/
flake8 src/
```

### Running Tests | تشغيل الاختبارات

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/azkar_bot

# Run specific test file
pytest tests/test_content_manager.py
```

## 📊 Monitoring | المراقبة

### Logs | السجلات

- **Console Output**: Real-time logging to console
- **File Logging**: Rotating log files in `logs/` directory
- **Structured Logging**: JSON format for easy parsing

### Statistics | الإحصائيات

Access via admin panel:
- Active groups count
- Messages sent statistics
- Content library size
- Error tracking

## 🐳 Docker Deployment | النشر باستخدام Docker

```bash
# Build image
docker build -t azkar-bot .

# Run container
docker run -d \
  --name azkar-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  azkar-bot
```

## 🤝 Contributing | المساهمة

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow | سير عمل التطوير

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Ensure all tests pass
6. Submit a pull request

## 📄 License | الترخيص

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author | المطور

**Omar Mahdy**
- 📧 Email: [omarelmhdi@gmail.com](mailto:omarelmhdi@gmail.com)
- 📱 Telegram: [@Mavdiii](https://t.me/Mavdiii)
- 🐙 GitHub: [@Mavdii](https://github.com/Mavdii)

## 🙏 Acknowledgments | شكر وتقدير

- Islamic content sources and scholars
- Telegram Bot API community
- Python asyncio community
- All contributors and users

## 📞 Support | الدعم

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/Mavdii/bot/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/Mavdii/bot/discussions)
- 📧 **Email Support**: [omarelmhdi@gmail.com](mailto:omarelmhdi@gmail.com)
- 💬 **Telegram**: [@Mavdiii](https://t.me/Mavdiii)

---

<div align="center">

**جعله الله في ميزان حسناتكم** 🤲

*May Allah accept this work and make it beneficial for the Muslim community*

**⭐ إذا أعجبك المشروع، لا تنس إعطاؤه نجمة!**

</div>
