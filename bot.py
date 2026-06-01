"""
Yuk Tashish Telegram Bot
========================
Haydovchi va Admin uchun Mini App ochuvchi bot.
Admin raqami orqali kirish tizimi bilan.
"""

import os
import json
import logging
from datetime import datetime
from functools import wraps

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, ReplyKeyboardMarkup, WebAppInfo, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

# ─── LOGGING ────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s │ %(levelname)s │ %(name)s │ %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── CONFIG (ENV VARIABLES) ─────────────────────────────────
BOT_TOKEN   = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_IDS   = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

# URLs of your hosted HTML pages (e.g. on GitHub Pages or any static host)
DRIVER_APP_URL    = os.getenv("DRIVER_APP_URL",    "https://yoursite.com/haydovchi_ilova.html")
DASHBOARD_APP_URL = os.getenv("DASHBOARD_APP_URL", "https://yoursite.com/yuk_tashish_566.html")

# Simple JSON file "database" (for Railway persistence use /data volume or SQLite)
DB_FILE = os.getenv("DB_FILE", "users.json")

# ─── DATABASE (JSON file) ────────────────────────────────────
def load_db() -> dict:
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"users": {}, "pending": {}}

def save_db(data: dict):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(user_id: int) -> dict | None:
    db = load_db()
    return db["users"].get(str(user_id))

def set_user(user_id: int, data: dict):
    db = load_db()
    db["users"][str(user_id)] = data
    save_db(db)

def add_pending(user_id: int, data: dict):
    db = load_db()
    db["pending"][str(user_id)] = data
    save_db(db)

def remove_pending(user_id: int):
    db = load_db()
    db["pending"].pop(str(user_id), None)
    save_db(db)

def get_all_pending() -> dict:
    return load_db().get("pending", {})

def get_all_users() -> dict:
    return load_db().get("users", {})

# ─── ROLES ──────────────────────────────────────────────────
ROLE_ADMIN    = "admin"
ROLE_DRIVER   = "haydovchi"
ROLE_VIEWER   = "viewer"      # read-only dashboard

STATUS_APPROVED = "approved"
STATUS_PENDING  = "pending"
STATUS_BLOCKED  = "blocked"

# ─── AUTH DECORATORS ────────────────────────────────────────
def require_approved(func):
    @wraps(func)
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        user = get_user(user_id)
        if not user or user.get("status") != STATUS_APPROVED:
            await update.effective_message.reply_text(
                "⛔ Ruxsat yo'q. Kirish uchun /start buyrug'ini yuboring."
            )
            return
        return await func(update, ctx, *args, **kwargs)
    return wrapper

def require_admin(func):
    @wraps(func)
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        user = get_user(user_id)
        if not user or user.get("role") not in (ROLE_ADMIN,) or user.get("status") != STATUS_APPROVED:
            await update.effective_message.reply_text("⛔ Faqat adminlar uchun.")
            return
        return await func(update, ctx, *args, **kwargs)
    return wrapper

# ─── KEYBOARDS ──────────────────────────────────────────────
def driver_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "📱 Reys Hisobotini Ochish",
            web_app=WebAppInfo(url=DRIVER_APP_URL)
        )
    ],[
        InlineKeyboardButton("ℹ️ Holat", callback_data="my_status"),
    ]])

def admin_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "📊 Dashboard Ochish",
            web_app=WebAppInfo(url=DASHBOARD_APP_URL)
        )
    ],[
        InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="list_users"),
        InlineKeyboardButton("⏳ Kutayotganlar",    callback_data="list_pending"),
    ]])

def phone_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Telefon raqamimni yuborish", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )

def approve_keyboard(target_id: int):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Haydovchi", callback_data=f"approve_{target_id}_{ROLE_DRIVER}"),
        InlineKeyboardButton("👁 Viewer",    callback_data=f"approve_{target_id}_{ROLE_VIEWER}"),
        InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{target_id}"),
    ]])

# ─── /start ─────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    user_id = user.id
    existing = get_user(user_id)

    # Already approved
    if existing and existing.get("status") == STATUS_APPROVED:
        role = existing.get("role")
        name = existing.get("name", user.first_name)
        if role == ROLE_ADMIN:
            await update.message.reply_text(
                f"👋 Xush kelibsiz, {name}!\n\n"
                "Siz *Admin* sifatida kirdiniz.\n"
                "Dashboard yoki foydalanuvchilarni boshqarish uchun quyidagi tugmalardan foydalaning.",
                parse_mode="Markdown",
                reply_markup=admin_keyboard()
            )
        else:
            await update.message.reply_text(
                f"👋 Xush kelibsiz, {name}!\n\n"
                "✅ Hisobot ilovasiga kirish uchun quyidagi tugmani bosing.",
                reply_markup=driver_keyboard()
            )
        return

    # Blocked
    if existing and existing.get("status") == STATUS_BLOCKED:
        await update.message.reply_text("⛔ Siz bloklangansiz. Admin bilan bog'laning.")
        return

    # Pending
    pending = get_all_pending()
    if str(user_id) in pending:
        await update.message.reply_text(
            "⏳ Arizangiz ko'rib chiqilmoqda.\n"
            "Admin tasdiqlash kerak. Biroz kuting."
        )
        return

    # New user — ask phone
    await update.message.reply_text(
        f"👋 Salom, *{user.first_name}*!\n\n"
        "Bu bot yuk tashish hisobotlarini yuritish uchun.\n\n"
        "📱 Kirish uchun telefon raqamingizni yuboring:",
        parse_mode="Markdown",
        reply_markup=phone_keyboard()
    )

# ─── PHONE CONTACT HANDLER ──────────────────────────────────
async def handle_contact(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    contact = update.message.contact

    # Security: make sure they're sending their own number
    if contact.user_id and contact.user_id != user.id:
        await update.message.reply_text("❌ O'z raqamingizni yuboring.", reply_markup=ReplyKeyboardRemove())
        return

    phone = contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone

    pending_data = {
        "id":       user.id,
        "name":     user.full_name,
        "username": f"@{user.username}" if user.username else "—",
        "phone":    phone,
        "time":     datetime.now().strftime("%d.%m.%Y %H:%M"),
    }
    add_pending(user.id, pending_data)

    await update.message.reply_text(
        f"✅ Raqamingiz qabul qilindi: *{phone}*\n\n"
        "⏳ Admin tasdiqlashini kuting. Xabar beramiz.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )

    # Notify all admins
    msg = (
        f"🔔 *Yangi kirish so'rovi*\n\n"
        f"👤 Ism: {pending_data['name']}\n"
        f"📱 Tel: `{phone}`\n"
        f"🆔 ID: `{user.id}`\n"
        f"🔗 Username: {pending_data['username']}\n"
        f"🕐 Vaqt: {pending_data['time']}"
    )
    for admin_id in get_admins():
        try:
            await ctx.bot.send_message(
                chat_id=admin_id,
                text=msg,
                parse_mode="Markdown",
                reply_markup=approve_keyboard(user.id)
            )
        except Exception as e:
            logger.warning(f"Admin {admin_id} ga xabar yuborilmadi: {e}")

def get_admins() -> list[int]:
    """Returns env admins + DB admins."""
    result = set(ADMIN_IDS)
    for uid, udata in get_all_users().items():
        if udata.get("role") == ROLE_ADMIN and udata.get("status") == STATUS_APPROVED:
            result.add(int(uid))
    return list(result)

# ─── CALLBACK: Approve / Reject ─────────────────────────────
async def handle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    data    = query.data
    admin   = update.effective_user

    await query.answer()

    # ── Approve
    if data.startswith("approve_"):
        parts     = data.split("_")
        target_id = int(parts[1])
        role      = parts[2]

        pending = get_all_pending()
        info    = pending.get(str(target_id), {})
        if not info:
            await query.edit_message_text("⚠️ Bu foydalanuvchi allaqachon ko'rib chiqilgan.")
            return

        set_user(target_id, {
            "id":       target_id,
            "name":     info.get("name", ""),
            "username": info.get("username", ""),
            "phone":    info.get("phone", ""),
            "role":     role,
            "status":   STATUS_APPROVED,
            "approved_by": admin.id,
            "approved_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
        })
        remove_pending(target_id)

        role_label = "🚛 Haydovchi" if role == ROLE_DRIVER else "👁 Viewer"
        await query.edit_message_text(
            f"✅ Tasdiqlandi: *{info.get('name')}* — {role_label}\n"
            f"📱 {info.get('phone')}",
            parse_mode="Markdown"
        )

        # Notify user
        kb = driver_keyboard() if role == ROLE_DRIVER else InlineKeyboardMarkup([[
            InlineKeyboardButton("📊 Dashboard", web_app=WebAppInfo(url=DASHBOARD_APP_URL))
        ]])
        try:
            await ctx.bot.send_message(
                chat_id=target_id,
                text=f"🎉 *Kirishingiz tasdiqlandi!*\n\n"
                     f"Siz *{role_label}* sifatida ro'yxatdan o'tdingiz.\n"
                     "Ilovani ochish uchun quyidagi tugmani bosing:",
                parse_mode="Markdown",
                reply_markup=kb
            )
        except Exception as e:
            logger.warning(f"Foydalanuvchi {target_id} ga xabar yuborilmadi: {e}")

    # ── Reject
    elif data.startswith("reject_"):
        target_id = int(data.split("_")[1])
        pending   = get_all_pending()
        info      = pending.get(str(target_id), {})
        remove_pending(target_id)

        await query.edit_message_text(
            f"❌ Rad etildi: *{info.get('name', target_id)}*",
            parse_mode="Markdown"
        )
        try:
            await ctx.bot.send_message(
                chat_id=target_id,
                text="❌ Kirish so'rovingiz rad etildi.\n"
                     "Savol bo'lsa, admin bilan bog'laning."
            )
        except:
            pass

    # ── My status
    elif data == "my_status":
        user_id = update.effective_user.id
        user    = get_user(user_id)
        if user:
            role   = "🚛 Haydovchi" if user["role"] == ROLE_DRIVER else "👁 Viewer" if user["role"] == ROLE_VIEWER else "🔑 Admin"
            status = "✅ Faol" if user["status"] == STATUS_APPROVED else "⛔ Bloklangan"
            await query.edit_message_text(
                f"👤 *{user['name']}*\n"
                f"📱 {user.get('phone','—')}\n"
                f"🏷 Rol: {role}\n"
                f"🔒 Holat: {status}\n"
                f"📅 Tasdiqlangan: {user.get('approved_at','—')}",
                parse_mode="Markdown",
                reply_markup=driver_keyboard() if user["role"]==ROLE_DRIVER else admin_keyboard()
            )

    # ── List users (admin)
    elif data == "list_users":
        user_id = update.effective_user.id
        if user_id not in get_admins():
            await query.answer("Faqat adminlar uchun.", show_alert=True)
            return
        users = get_all_users()
        if not users:
            text = "Hech qanday foydalanuvchi yo'q."
        else:
            lines = ["👥 *Foydalanuvchilar:*\n"]
            for u in users.values():
                r = "🚛" if u["role"]==ROLE_DRIVER else "👁" if u["role"]==ROLE_VIEWER else "🔑"
                s = "✅" if u["status"]==STATUS_APPROVED else "⛔"
                lines.append(f"{s}{r} {u['name']} — `{u.get('phone','—')}`")
            text = "\n".join(lines)
        await query.edit_message_text(text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Orqaga", callback_data="back_admin")
            ]]))

    # ── List pending (admin)
    elif data == "list_pending":
        user_id = update.effective_user.id
        if user_id not in get_admins():
            await query.answer("Faqat adminlar uchun.", show_alert=True)
            return
        pending = get_all_pending()
        if not pending:
            text = "⏳ Kutayotgan so'rov yo'q."
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Orqaga", callback_data="back_admin")
            ]]))
        else:
            for uid, info in pending.items():
                kb = approve_keyboard(int(uid))
                await ctx.bot.send_message(
                    chat_id=update.effective_user.id,
                    text=f"⏳ *Kutayotgan so'rov*\n\n"
                         f"👤 {info['name']}\n📱 `{info['phone']}`\n🕐 {info['time']}",
                    parse_mode="Markdown",
                    reply_markup=kb
                )
            await query.edit_message_text(
                f"📋 {len(pending)} ta so'rov yuborildi.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀️ Orqaga", callback_data="back_admin")
                ]])
            )

    # ── Back to admin
    elif data == "back_admin":
        await query.edit_message_text(
            "🔑 Admin panel:",
            reply_markup=admin_keyboard()
        )

# ─── /users COMMAND (admin only) ────────────────────────────
async def cmd_users(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in get_admins():
        await update.message.reply_text("⛔ Faqat adminlar uchun.")
        return
    users = get_all_users()
    if not users:
        await update.message.reply_text("Hech qanday foydalanuvchi yo'q.")
        return
    lines = ["👥 *Barcha foydalanuvchilar:*\n"]
    for u in users.values():
        r = "🚛H" if u["role"]==ROLE_DRIVER else "👁V" if u["role"]==ROLE_VIEWER else "🔑A"
        s = "✅" if u["status"]==STATUS_APPROVED else "⛔"
        lines.append(f"{s} {r} | {u['name']} | `{u.get('phone','—')}` | ID:`{u['id']}`")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

# ─── /block & /unblock (admin only) ─────────────────────────
async def cmd_block(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in get_admins():
        await update.message.reply_text("⛔ Faqat adminlar uchun.")
        return
    if not ctx.args:
        await update.message.reply_text("Foydalanish: /block <user_id>")
        return
    try:
        target_id = int(ctx.args[0])
        user = get_user(target_id)
        if not user:
            await update.message.reply_text("Foydalanuvchi topilmadi.")
            return
        user["status"] = STATUS_BLOCKED
        set_user(target_id, user)
        await update.message.reply_text(f"⛔ {user['name']} bloklandi.")
        try:
            await ctx.bot.send_message(target_id, "⛔ Sizning kirishingiz bloklandi.")
        except: pass
    except ValueError:
        await update.message.reply_text("Noto'g'ri ID.")

async def cmd_unblock(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in get_admins():
        await update.message.reply_text("⛔ Faqat adminlar uchun.")
        return
    if not ctx.args:
        await update.message.reply_text("Foydalanish: /unblock <user_id>")
        return
    try:
        target_id = int(ctx.args[0])
        user = get_user(target_id)
        if not user:
            await update.message.reply_text("Foydalanuvchi topilmadi.")
            return
        user["status"] = STATUS_APPROVED
        set_user(target_id, user)
        await update.message.reply_text(f"✅ {user['name']} blokdan chiqarildi.")
        try:
            await ctx.bot.send_message(target_id, "✅ Kirishingiz tiklandi. /start yuboring.")
        except: pass
    except ValueError:
        await update.message.reply_text("Noto'g'ri ID.")

# ─── /addadmin (only for ENV admins) ────────────────────────
async def cmd_addadmin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    if not ctx.args:
        await update.message.reply_text("Foydalanish: /addadmin <user_id>")
        return
    try:
        target_id = int(ctx.args[0])
        user = get_user(target_id)
        if not user:
            await update.message.reply_text("Avval foydalanuvchi ro'yxatdan o'tishi kerak.")
            return
        user["role"]   = ROLE_ADMIN
        user["status"] = STATUS_APPROVED
        set_user(target_id, user)
        await update.message.reply_text(f"🔑 {user['name']} admin qilindi.")
        try:
            await ctx.bot.send_message(target_id,
                "🔑 Siz admin qildingiz! /start yuboring.",)
        except: pass
    except ValueError:
        await update.message.reply_text("Noto'g'ri ID.")

# ─── /help ──────────────────────────────────────────────────
async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_admin = user_id in get_admins()

    text = (
        "*Yuk Tashish Bot — Yordam*\n\n"
        "📌 */start* — Botni ishga tushirish\n"
        "📌 */help* — Yordam\n"
    )
    if is_admin:
        text += (
            "\n*Admin buyruqlari:*\n"
            "👥 */users* — Barcha foydalanuvchilar\n"
            "⛔ */block <id>* — Foydalanuvchini bloklash\n"
            "✅ */unblock <id>* — Blokdan chiqarish\n"
            "🔑 */addadmin <id>* — Admin qilish\n"
        )
    await update.message.reply_text(text, parse_mode="Markdown")

# ─── Unknown messages ────────────────────────────────────────
async def handle_unknown(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id  = update.effective_user.id
    existing = get_user(user_id)
    if existing and existing.get("status") == STATUS_APPROVED:
        role = existing.get("role")
        if role == ROLE_ADMIN:
            await update.message.reply_text("Admin panel:", reply_markup=admin_keyboard())
        else:
            await update.message.reply_text("Ilovani ochish:", reply_markup=driver_keyboard())
    else:
        await update.message.reply_text("/start buyrug'ini yuboring.")

# ─── MAIN ────────────────────────────────────────────────────
def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        raise ValueError("BOT_TOKEN environment variable o'rnatilmagan!")

    app = Application.builder().token(BOT_TOKEN).build()

    # Auto-register ENV admins
    for admin_id in ADMIN_IDS:
        existing = get_user(admin_id)
        if not existing:
            set_user(admin_id, {
                "id":       admin_id,
                "name":     f"Admin_{admin_id}",
                "username": "—",
                "phone":    "—",
                "role":     ROLE_ADMIN,
                "status":   STATUS_APPROVED,
                "approved_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
            })
            logger.info(f"ENV admin ro'yxatga qo'shildi: {admin_id}")

    # Handlers
    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("help",      cmd_help))
    app.add_handler(CommandHandler("users",     cmd_users))
    app.add_handler(CommandHandler("block",     cmd_block))
    app.add_handler(CommandHandler("unblock",   cmd_unblock))
    app.add_handler(CommandHandler("addadmin",  cmd_addadmin))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown))

    logger.info("Bot ishga tushdi...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
