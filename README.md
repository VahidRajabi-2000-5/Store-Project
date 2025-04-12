# 🛒 Store Project

پروژه فروشگاه آنلاین با استفاده از Django و Django REST Framework توسعه داده شده. این پروژه شامل مدیریت محصولات، دسته‌بندی‌ها، نظرات کاربران، سفارشات، تخفیف‌ها، سبد خرید و ... است.

---

## 🚀 اجرای پروژه روی لوکال

### 🧱 پیش‌نیازها

- Python 3.10 یا بالاتر
- pipenv
- MySQL (نصب شده و فعال)
- ایجاد یک دیتابیس MySQL با نام دلخواه (مثلاً `store_db`)
- تنظیمات اتصال به MySQL در `settings.py`

### 🛠️ مراحل نصب

```bash
# 1. کلون کردن پروژه
git clone git@github.com:VahidRajabi-2000-5/Store-Project.git
cd Store-Project

# 2. نصب وابستگی‌ها و ساخت محیط مجازی با pipenv
pipenv install

# 3. فعال‌سازی محیط مجازی
pipenv shell

# 4. نصب پکیج mysqlclient (ممکن است به نصب libmysqlclient-dev هم نیاز باشد)
pipenv install mysqlclient

# 5. اجرای مهاجرت‌ها
python manage.py makemigrations
python manage.py migrate

# 6. ساخت ادمین (اختیاری)
python manage.py createsuperuser

# 7. اجرای سرور
python manage.py runserver
```

📍 حالا پروژه از آدرس زیر قابل دسترسیه:  
[http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## ⚙️ تنظیمات اتصال به MySQL

در فایل `store_project/settings.py` قسمت `DATABASES` باید به شکل زیر تنظیم شده باشد:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'store_db',
        'USER': 'your_mysql_user',
        'PASSWORD': 'your_mysql_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

---

## 📁 ساختار اصلی پروژه

```
store_project/
├── store/              # اپلیکیشن اصلی فروشگاه
│   ├── models.py       # مدل‌ها: Product, Category, Order, Comment ...
│   ├── views.py        # ویوها و API ها
│   ├── serializers.py  # سریالایزرها برای REST API
│   └── urls.py         # آدرس‌دهی اپلیکیشن
├── store_project/      # تنظیمات اصلی پروژه Django
│   ├── settings.py
│   └── urls.py
├── manage.py
├── Pipfile
├── Pipfile.lock
└── ...
```

---

## 🧰 تکنولوژی‌های استفاده‌شده

- Django 🌐
- Django REST Framework 🔗
- Python 3.10 🐍
- MySQL 🛢️
- pipenv برای مدیریت محیط مجازی و پکیج‌ها
- Git & GitHub برای کنترل نسخه

---

## 📡 API Endpoints

برخی از مسیرهای مهم API:

| Endpoint                            | Method | توضیحات                 
| ----------------------------------- | ------ | ----------------------- 
| `/api/store/products/`              | GET    | لیست محصولات            
| `/api/store/products/<id>/`         | GET    | جزئیات یک محصول         
| `/api/store/categories/`            | GET    | لیست دسته‌بندی‌ها       
| `/api/store/orders/`                | POST   | ساخت سفارش جدید         
| `/api/store/carts/`                 | GET    | مشاهده سبد خرید         
| `/apistore/carts/{id}/items/`       | POST   | افزودن آیتم به سبد خرید 
| `/api/store/products/{id}/comments` | POST   | ثبت نظر جدید            
| `/api/store/discounts/`             | GET    | دریافت لیست تخفیف‌ها    

📌 همه‌ی Endpointها از طریق DRF browsable API در دسترس هستند.

---

## 🧑‍💻 توسعه‌دهنده

- 👤 **وحید رجبی**
- 🔗 [گیت‌هاب من](https://github.com/VahidRajabi-2000-5)

---

## 📃 لایسنس

این پروژه به صورت آموزشی ساخته شده و استفاده از آن آزاد است.
