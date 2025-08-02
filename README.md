# ربات تلگرام مدیریت مدل‌ها و عکاسان

این ربات برای مدیریت و اتصال تأمین‌کنندگان (مدل‌ها و عکاسان) با درخواست‌کنندگان طراحی شده است.

## ویژگی‌ها

### برای تأمین‌کنندگان:
- ثبت‌نام مرحله‌ای با wizard
- ثبت اطلاعات کامل شامل مشخصات ظاهری، سبک کاری، محدوده قیمت
- مشاهده و مدیریت درخواست‌ها
- ویرایش پروفایل

### برای درخواست‌کنندگان:
- جستجوی پیشرفته با فیلترهای متعدد
- مشاهده لیست تأمین‌کنندگان با صفحه‌بندی
- ارسال درخواست وقت
- دریافت نوتیفیکیشن

## نصب و راه‌اندازی

### پیش‌نیازها:
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### نصب محلی:

1. کلون کردن پروژه:
```bash
git clone https://github.com/your-repo/telegram-bot.git
cd telegram-bot

2. ایجاد محیط مجازی:
bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# یا
venv\Scripts\activate  # Windows

3. نصب وابستگی‌ها:
bash
pip install -r requirements.txt

4. تنظیم متغیرهای محیطی:
bash
cp .env.example .env
# ویرایش فایل .env و تنظیم مقادیر

5. اجرای migrations:
bash
alembic upgrade head

6. اجرای ربات:
bash
python main.py

### نصب با Docker:

1. Build و اجرا:
bash
docker-compose up -d

2. مشاهده لاگ‌ها:
bash
docker-compose logs -f bot

## ساختار پروژه


telegram_bot/
├── config/          # تنظیمات
├── database/        # مدل‌ها و اتصال دیتابیس
├── handlers/        # هندلرهای ربات
├── keyboards/       # کیبوردها
├── middlewares/     # میدلورها
├── states/          # FSM states
├── utils/           # توابع کمکی
└── tests/           # تست‌ها

## تنظیمات Webhook (اختیاری)

برای استفاده از webhook به جای polling:

1. تنظیم دامنه با SSL
2. تغییر `main.py` برای پشتیبانی از webhook
3. اجرا با gunicorn یا uvicorn

مثال:
python
# در main.py
if settings.use_webhook:
await bot.set_webhook(
url=f"{settings.webhook_url}/{settings.webhook_path}",
drop_pending_updates=True
)
    
app = web.Application()
webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
webhook_handler.register(app, path=f"/{settings.webhook_path}")
setup_application(app, dp, bot=bot)
    
web.run_app(app, host="0.0.0.0", port=8080)
else:
await dp.start_polling(bot)

## مشارکت

لطفاً برای مشارکت در پروژه:
1. Fork کنید
2. Branch جدید ایجاد کنید
3. تغییرات را Commit کنید
4. Push کنید
5. Pull Request ایجاد کنید

## لایسنس

این پروژه تحت لایسنس MIT منتشر شده است.


### `.gitignore`:
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Database
*.db
*.sqlite3
postgres_data/

# Logs
logs/
*.log

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/

# Distribution
build/
dist/
*.egg-info/
.eggs/

# Docker
.dockerignore

# OS
.DS_Store
Thumbs.db

# Project specific
media/
static/
temp/
