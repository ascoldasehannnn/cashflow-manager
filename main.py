import json
import pandas as pd
import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

TOKEN = os.getenv("8623557436:AAFxg39EBNN1i0MTWjhw86ClmjArlo0c8gY")

FILE = "data.json"

BATAS_TRANSAKSI = 500000
BATAS_SALDO = 50000

# ================= DATABASE =================

def load_data():
    try:
        with open(FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)

# ================= PARSE UANG =================

def parse_uang(text):
    text = text.lower().replace("+","").replace("-","")

    if "jt" in text:
        return int(float(text.replace("jt","")) * 1000000)
    if "rb" in text:
        return int(float(text.replace("rb","")) * 1000)
    if "k" in text:
        return int(float(text.replace("k","")) * 1000)

    return int(text)

# ================= TRANSAKSI =================

async def transaksi(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = load_data()
    text = update.message.text.split()

    raw = text[0]

    if raw.startswith("-"):
        jumlah = -parse_uang(raw)
    else:
        jumlah = parse_uang(raw)

    kategori = text[1] if len(text) > 1 else "lainnya"
    catatan = " ".join(text[2:]) if len(text) > 2 else ""

    jenis = "Masuk" if jumlah > 0 else "Keluar"

    now = datetime.now()

    data.append({
        "tanggal": now.strftime("%Y-%m-%d %H:%M"),
        "jenis": jenis,
        "jumlah": abs(jumlah),
        "kategori": kategori,
        "catatan": catatan
    })

    save_data(data)

    df = pd.DataFrame(data)

    pemasukan = df[df["jenis"]=="Masuk"]["jumlah"].sum()
    pengeluaran = df[df["jenis"]=="Keluar"]["jumlah"].sum()
    saldo = pemasukan - pengeluaran

    await update.message.reply_text(
f"""
✅ Tersimpan

📥 {pemasukan}
📤 {pengeluaran}
💰 {saldo}
"""
)

    if abs(jumlah) >= BATAS_TRANSAKSI and jenis == "Keluar":
        await update.message.reply_text("🚨 Pengeluaran besar!")

    if saldo <= BATAS_SALDO:
        await update.message.reply_text("⚠️ Saldo hampir habis!")

# ================= SALDO =================

async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    data = load_data()
    df = pd.DataFrame(data)

    pemasukan = df[df["jenis"]=="Masuk"]["jumlah"].sum()
    pengeluaran = df[df["jenis"]=="Keluar"]["jumlah"].sum()

    saldo = pemasukan - pengeluaran

    await update.message.reply_text(f"💰 Saldo: {saldo}")

# ================= HARI =================

async def hari(update: Update, context: ContextTypes.DEFAULT_TYPE):

    tanggal_input = context.args[0]

    data = load_data()
    df = pd.DataFrame(data)

    df["tanggal"] = pd.to_datetime(df["tanggal"])
    tgl = pd.to_datetime(tanggal_input)

    df = df[df["tanggal"].dt.date == tgl.date()]

    pemasukan = df[df["jenis"]=="Masuk"]["jumlah"].sum()
    pengeluaran = df[df["jenis"]=="Keluar"]["jumlah"].sum()

    await update.message.reply_text(
f"""
📊 Harian ({tanggal_input})

📥 {pemasukan}
📤 {pengeluaran}
💰 {pemasukan - pengeluaran}
"""
)

# ================= BULAN =================

async def bulan(update: Update, context: ContextTypes.DEFAULT_TYPE):

    bulan = int(context.args[0])
    tahun = int(context.args[1])

    data = load_data()
    df = pd.DataFrame(data)

    df["tanggal"] = pd.to_datetime(df["tanggal"])

    df = df[
        (df["tanggal"].dt.month == bulan) &
        (df["tanggal"].dt.year == tahun)
    ]

    pemasukan = df[df["jenis"]=="Masuk"]["jumlah"].sum()
    pengeluaran = df[df["jenis"]=="Keluar"]["jumlah"].sum()

    await update.message.reply_text(
f"""
📊 Bulanan

📥 {pemasukan}
📤 {pengeluaran}
💰 {pemasukan - pengeluaran}
"""
)

# ================= RUN =================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), transaksi))
app.add_handler(CommandHandler("saldo", saldo))
app.add_handler(CommandHandler("hari", hari))
app.add_handler(CommandHandler("bulan", bulan))

app.run_polling()
