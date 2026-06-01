# 🚛 Yuk Tashish Bot — O'rnatish Qo'llanmasi

## 1-QADAM: Telegram Bot yaratish

1. Telegramda **@BotFather** ga yozing
2. `/newbot` yuboring
3. Bot nomi kiriting: masalan `Yuk Hisobi`
4. Username kiriting: masalan `yuk_hisobi_bot`
5. Olingan **TOKEN** ni saqlang: `7123456789:AAHxxxxxxxxxxxxxx`

---

## 2-QADAM: HTML fayllarni internetga joylashtirish

HTML fayllar HTTPS orqali ochilishi **SHART** (Telegram Mini App talabi).

### Eng oson yo'l: GitHub Pages (BEPUL)

1. **github.com** da hisob yarating
2. Yangi repository yarating: `yuk-hisobi`
3. `haydovchi_ilova.html` va `yuk_tashish_566.html` fayllarini yuklang
4. **Settings → Pages → Source: main branch** → Save

URL ko'rinishi:
```
https://yourusername.github.io/yuk-hisobi/haydovchi_ilova.html
https://yourusername.github.io/yuk-hisobi/yuk_tashish_566.html
```

---

## 3-QADAM: Botni Railway.app ga joylash (BEPUL)

### 3.1 Railway hisob yaratish
1. **railway.app** ga kiring
2. GitHub bilan ro'yxatdan o'ting

### 3.2 Loyihani yuklash
1. `New Project` → `Deploy from GitHub repo`
2. Yoki `New Project` → `Empty Project` → `Add Service` → `GitHub Repo`

**Yoki** to'g'ridan-to'g'ri:
```bash
# Lokal kompyuterdan deploy qilish
npm install -g @railway/cli
railway login
railway new
railway up
```

### 3.3 Environment Variables o'rnatish
Railway dashboard → `Variables` bo'limiga quyidagilarni qo'shing:

| Kalit               | Qiymat                                           |
|---------------------|--------------------------------------------------|
| `BOT_TOKEN`         | `7123456789:AAHxxxxxxxxxxxxxx` (BotFather dan)   |
| `ADMIN_IDS`         | `123456789` (Sizning Telegram ID raqamingiz)     |
| `DRIVER_APP_URL`    | `https://yourusername.github.io/.../haydovchi_ilova.html` |
| `DASHBOARD_APP_URL` | `https://yourusername.github.io/.../yuk_tashish_566.html` |

> **Telegram ID topish:** @userinfobot ga `/start` yuboring

---

## 4-QADAM: Mini App sifatida sozlash (ixtiyoriy lekin tavsiya etiladi)

Bu qadam HTML fayllarni Telegram ichida to'liq ekranda ochadi.

1. **@BotFather** ga `/mybots` yuboring
2. Botingizni tanlang
3. **Bot Settings → Menu Button → Edit Menu Button URL**
4. Haydovchi URL ni kiriting

---

## 5-QADAM: Kirish jarayoni

### Haydovchi uchun:
1. Botni Telegramda topadi: `@yuk_hisobi_bot`
2. `/start` yuboring
3. `📱 Telefon raqamimni yuborish` tugmasini bosadi
4. **Admin tasdiqlaydi** → haydovchi bildirishnoma oladi
5. `📱 Reys Hisobotini Ochish` tugmasi paydo bo'ladi

### Admin uchun:
- `ADMIN_IDS` da ID si bo'lgan kishi avtomatik admin
- Yoki `/addadmin <id>` buyrug'i bilan qo'shish mumkin

---

## 6-QADAM: Bot buyruqlari

| Buyruq | Tavsif |
|--------|--------|
| `/start` | Botni ishga tushirish |
| `/help` | Yordam |
| `/users` | Barcha foydalanuvchilar (admin) |
| `/block <id>` | Foydalanuvchini bloklash (admin) |
| `/unblock <id>` | Blokdan chiqarish (admin) |
| `/addadmin <id>` | Admin qilish (asosiy admin) |

---

## Tizim qanday ishlaydi

```
Haydovchi /start yuboradi
    ↓
Telefon raqamini yuboradi
    ↓
Admin Telegram'da bildirishnoma oladi
    ↓
Admin [✅ Haydovchi] tugmasini bosadi
    ↓
Haydovchi bildirishnoma oladi + Mini App tugmasi paydo bo'ladi
    ↓
Haydovchi [📱 Reys Hisobotini Ochish] ni bosadi
    ↓
HTML ilova Telegram ichida ochiladi
    ↓
Hisobotni to'ldiradi → Telegram orqali yuboradi
    ↓
Admin dashboardga [📥 Import] tugmasi orqali import qiladi
```

---

## Muammolarni hal qilish

**Bot ishlamayapti:**
- `BOT_TOKEN` to'g'ri ekanini tekshiring
- Railway logs ni ko'ring

**Mini App ochilmayapti:**
- URL HTTPS bo'lishi shart
- GitHub Pages to'g'ri joylashtirilganini tekshiring

**Telefon raqam so'ralmayapti:**
- Faqat mobil ilovada ishlaydi (Desktop Telegram da ishlamaydi)
