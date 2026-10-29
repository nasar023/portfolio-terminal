from database import (
    load_data, save_data, load_cash, save_cash, 
    load_bank_cash, save_bank_cash, load_mutasi, save_mutasi, 
    add_mutasi_record, load_watchlist, save_watchlist, 
    load_dividends, save_dividends, load_alerts, save_alerts, 
    load_macro_config, save_macro_config
)

import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import os
import time

from views import dashboard, portofolio, simulasi, watchlist, dividen, alert, kalender, riwayat, laporan, berita

# --- SETTING HALAMAN ---
st.set_page_config(page_title="Portfolio Tracker Institutional Pro", layout="wide")

# Custom CSS untuk kerapian dan estetika terminal
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1a1f2c;
        border-radius: 8px;
        padding: 10px 20px;
        color: white;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563eb !important;
    }
    input, select, div[data-baseweb="calendar"] {
        translate: no;
    }
    </style>
""", unsafe_allow_html=True)

# --- FITUR AUTO-REFRESH OTOMATIS TIAP 1 MENIT ---
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=60000, key="auto_refresh_terminal")
except ImportError:
    st.sidebar.caption("💡 Tips: Install `streamlit-autorefresh` via terminal (`pip install streamlit-autorefresh`) untuk auto-refresh harga real-time.")

st.title("📈 Institutional Portfolio & Macro Terminal (BEI & Crypto)")
st.markdown("Terminal investasi kelas profesional dengan analisis makro global, aset kripto (USDT), grafik interaktif candlestick, kalender korporasi, dan *price alert*.")

df_transaksi = load_data()
buying_power = load_cash()
bank_cash = load_bank_cash()
df_mutasi = load_mutasi()
df_watchlist = load_watchlist()
df_dividen = load_dividends()
df_alerts = load_alerts()
df_macros = load_macro_config()

# --- AMBIL KURS USD/IDR TERBARU ---
try:
    usd_idr_bar = yf.Ticker("IDR=X").history(period="2d")
    current_usd = float(usd_idr_bar['Close'].iloc[-1]) if not usd_idr_bar.empty else 15500.0
except Exception:
    current_usd = 15500.0

# --- SIDEBAR: PENGATURAN MACRO BAR (SIMPEL DENGAN POPOVER) ---
st.sidebar.markdown("### 🌐 Macro Bar")
with st.sidebar.popover("⚙️ Kelola Aset Tampilan Atas"):
    st.markdown("#### Tambah / Hapus Aset Macro Bar")
    new_m_simbol = st.text_input("Simbol Yahoo (cth: TLKM.JK / DOGE-USD)", value="ASII.JK").strip()
    new_m_label = st.text_input("Label Tampilan", value="ASII").strip()
    new_m_tipe = st.selectbox("Jenis Aset", ["Stock", "Crypto", "Index", "Forex", "Commodity"])
    
    if st.button("Tambah Aset"):
        if new_m_simbol and new_m_simbol not in df_macros["Simbol"].values:
            new_row = pd.DataFrame({"Simbol": [new_m_simbol], "Label": [new_m_label], "Tipe": [new_m_tipe]})
            df_macros = pd.concat([df_macros, new_row], ignore_index=True)
            save_macro_config(df_macros)
            st.success(f"Aset {new_m_label} ditambahkan!")
            st.rerun()
            
    del_macro_target = st.selectbox("Pilih Aset Dihapus", ["-- Pilih --"] + list(df_macros["Label"]))
    if del_macro_target != "-- Pilih --":
        if st.button("Hapus Aset Ini"):
            df_macros = df_macros[df_macros["Label"] != del_macro_target]
            save_macro_config(df_macros)
            st.success("Aset dihapus!")
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("🏦 Manajemen Saldo & RDN")

st.sidebar.metric("💳 Saldo Rekening Utama/Bank", f"Rp {bank_cash:,.0f}".replace(",", "X").replace(".", ",").replace("X", "."))
st.sidebar.metric("💰 Saldo RDN / Buying Power", f"Rp {buying_power:,.0f}".replace(",", "X").replace(".", ",").replace("X", "."))

with st.sidebar.expander("⚙️ Kelola Kas & RDN (Transfer/Top Up)"):
    tab_m1, tab_m2, tab_m3 = st.tabs(["💸 Transfer RDN", "💳 Mutasi Bank", "✏️ Atur Manual"])
    
    with tab_m1:
        st.caption("Kelola Arus Dana Bank ⇄ RDN")
        tr_direction = st.selectbox("Arah Transfer", ["Bank ke RDN (Top Up)", "RDN ke Bank (Tarik Dana)"])
        tr_tanggal = st.date_input("Tanggal Transfer", key="tr_date")
        tr_amount_str = st.text_input("Jumlah Nominal (Rp)", value="1.000.000", key="input_tr_rdn")
        
        try:
            clean_tr = tr_amount_str.replace(".", "").replace(",", "").strip()
            val_tr = float(clean_tr) if clean_tr else 0.0
            formatted_tr_prev = f"Rp {val_tr:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
            st.caption(f"Nominal terbaca: **{formatted_tr_prev}**")
        except ValueError:
            val_tr = 0.0
            st.warning("Format angka tidak valid.")

        if st.button("Eksekusi Transfer RDN"):
            if val_tr <= 0:
                st.error("Masukkan jumlah nominal yang valid!")
            elif tr_direction == "Bank ke RDN (Top Up)" and val_tr > bank_cash:
                st.error("Saldo Rekening Bank tidak mencukupi!")
            elif tr_direction == "RDN ke Bank (Tarik Dana)" and val_tr > buying_power:
                st.error("Saldo RDN / Buying Power tidak mencukupi!")
            else:
                if tr_direction == "Bank ke RDN (Top Up)":
                    bank_cash -= val_tr
                    buying_power += val_tr
                    save_bank_cash(bank_cash)
                    save_cash(buying_power)
                    add_mutasi_record(str(tr_tanggal), "TOP UP RDN", "Transfer dari Bank ke RDN", val_tr)
                    st.success(f"Berhasil top up RDN sebesar {formatted_tr_prev}!")
                else:
                    buying_power -= val_tr
                    bank_cash += val_tr
                    save_cash(buying_power)
                    save_bank_cash(bank_cash)
                    add_mutasi_record(str(tr_tanggal), "TARIK RDN", "Penarikan dana RDN ke Rekening Bank", val_tr)
                    st.success(f"Berhasil tarik dana RDN sebesar {formatted_tr_prev}!")
                st.rerun()

    with tab_m2:
        st.caption("Kelola Rekening Utama (Top Up / Tarik)")
        st_tanggal = st.date_input("Tanggal Transaksi", key="st_date_bank")
        st_tipe = st.selectbox("Jenis Transaksi", ["TOP UP", "TARIK"], key="st_tipe_bank_select")
        st_amount_str = st.text_input("Jumlah Nominal (Rp)", value="1.000.000", key="input_st_tarik_bank")
        
        try:
            clean_st = st_amount_str.replace(".", "").replace(",", "").strip()
            val_st = float(clean_st) if clean_st else 0.0
            formatted_st_prev = f"Rp {val_st:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
            st.caption(f"Nominal terbaca: **{formatted_st_prev}**")
        except ValueError:
            val_st = 0.0
            st.warning("Format angka tidak valid.")

        if st.button("Eksekusi Kas Bank", key="btn_eksekusi_kas_bank"):
            if val_st <= 0:
                st.error("Masukkan jumlah nominal yang valid!")
            elif st_tipe == "TARIK" and val_st > bank_cash:
                st.error("Saldo Rekening Bank tidak mencukupi untuk ditarik!")
            else:
                if st_tipe == "TOP UP":
                    bank_cash += val_st
                    save_bank_cash(bank_cash)
                    add_mutasi_record(str(st_tanggal), "TOP UP", "Top up dana ke Rekening Utama", val_st)
                    st.success(f"Berhasil top up {formatted_st_prev}!")
                else:
                    bank_cash -= val_st
                    save_bank_cash(bank_cash)
                    add_mutasi_record(str(st_tanggal), "TARIK", "Tarik dana dari Rekening Utama", val_st)
                    st.success(f"Berhasil tarik {formatted_st_prev}!")
                st.rerun()
                
    with tab_m3:
        st.caption("Ubah Saldo Paksa (Darurat)")
        new_bank_input = st.number_input("Saldo Bank (Rp)", min_value=0, value=int(bank_cash), step=500000)
        new_rdn_input = st.number_input("Saldo RDN (Rp)", min_value=0, value=int(buying_power), step=500000)
        if st.button("Simpan Perubahan Saldo"):
            bank_cash = float(new_bank_input)
            buying_power = float(new_rdn_input)
            save_bank_cash(bank_cash)
            save_cash(buying_power)
            add_mutasi_record(str(pd.Timestamp.today().date()), "PENYESUAIAN MANUAL", "Penyesuaian saldo paksa sistem", 0)
            st.success("Saldo berhasil diperbarui!")
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("📝 Catat Transaksi Baru")

kategori_asset = st.sidebar.selectbox("Pasar / Kategori Aset", ["Saham BEI", "Kripto (USDT)"], key="select_kategori")

# --- FUNGSI FORMAT OTOMATIS INPUT TRANSAKSI ---
def fmt_trx_jml():
    raw = st.session_state.get("in_trx_jml", "1")
    digits = "".join([c for c in raw if c.isdigit()])
    if digits:
        st.session_state.in_trx_jml = f"{int(digits):,}".replace(",", ".")
    else:
        st.session_state.in_trx_jml = "1"

def fmt_trx_hrg():
    raw = st.session_state.get("in_trx_hrg", "5.000")
    digits = "".join([c for c in raw if c.isdigit()])
    if digits:
        st.session_state.in_trx_hrg = f"{int(digits):,}".replace(",", ".")
    else:
        st.session_state.in_trx_hrg = "0"

if "in_trx_jml" not in st.session_state:
    st.session_state.in_trx_jml = "1"
if "in_trx_hrg" not in st.session_state:
    st.session_state.in_trx_hrg = "5.000"

tanggal = st.sidebar.date_input("Tanggal Transaksi")

if kategori_asset == "Saham BEI":
    kode_input = st.sidebar.text_input("Kode Saham", value="BBRI").upper().strip()
else:
    kode_input = st.sidebar.text_input("Koin Kripto", value="BTC").upper().strip()
    
tipe = st.sidebar.selectbox("Tipe Transaksi", ["BELI", "JUAL"])

if kategori_asset == "Saham BEI":
    jumlah_unit_str = st.sidebar.text_input("Jumlah Lot (1 Lot = 100 lembar)", key="in_trx_jml", on_change=fmt_trx_jml)
    label_harga = "Harga per Lembar (Rp)"
    mata_uang_input = "IDR"
else:
    jumlah_unit_str = st.sidebar.text_input("Jumlah Koin / Unit", key="in_trx_jml", on_change=fmt_trx_jml)
    mata_uang_input = st.sidebar.selectbox("Mata Uang Harga", ["USDT", "IDR (Rupiah)"])
    label_harga = "Harga per Koin (USDT)" if mata_uang_input == "USDT" else "Harga per Koin (Rp)"

harga_str = st.sidebar.text_input(label_harga, key="in_trx_hrg", on_change=fmt_trx_hrg)
persen_fee_str = st.sidebar.text_input("Estimasi Fee (%)", value="0,15")

try:
    c_preview_jml = float(jumlah_unit_str.replace(".", "").replace(",", ".").strip()) if jumlah_unit_str else 0.0
    c_preview_hrg = float(harga_str.replace(".", "").replace(",", ".").strip()) if harga_str else 0.0
    st.sidebar.caption(f"Terbaca: **{c_preview_jml:,.2f}** unit | Harga: **Rp {c_preview_hrg:,.0f}**".replace(",", "X").replace(".", ",").replace("X", "."))
except ValueError:
    pass

submit_button = st.sidebar.button(label="Eksekusi Transaksi", key="btn_eksekusi_trx")

# --- HITUNG KEPEMILIKAN & REALIZED P/L (MULTI-ASET AMAN) ---
def calculate_portfolio_and_realized(df):
    if df.empty:
        return {}, 0.0
    
    portfolio = {}
    realized_pl = 0.0
    df_sorted = df.sort_values(by="ID") if "ID" in df.columns else df
    
    for _, row in df_sorted.iterrows():
        ticker = row["Kode Saham"]
        unit = row["Jumlah Unit"] if "Jumlah Unit" in row else row.get("Jumlah Lot", 0)
        total_trx = row["Total Transaksi (Rp)"]
        kategori = row.get("Kategori", "Saham BEI")
        if pd.isna(kategori): kategori = "Saham BEI"
        
        if ticker not in portfolio:
            portfolio[ticker] = {"unit": 0.0, "total_modal": 0.0, "kategori": kategori}
            
        if row["Tipe"] == "BELI":
            portfolio[ticker]["unit"] += unit
            portfolio[ticker]["total_modal"] += total_trx
        elif row["Tipe"] == "JUAL":
            current_unit = portfolio[ticker]["unit"]
            if current_unit > 0:
                avg_cost = portfolio[ticker]["total_modal"] / current_unit
                modal_dilepas = unit * avg_cost
                profit_jual = total_trx - modal_dilepas
                realized_pl += profit_jual
                
                portfolio[ticker]["unit"] -= unit
                portfolio[ticker]["total_modal"] -= modal_dilepas
                
                if portfolio[ticker]["unit"] <= 0:
                    portfolio[ticker] = {"unit": 0.0, "total_modal": 0.0, "kategori": kategori}
                    
    active_portfolio = {k: v for k, v in portfolio.items() if v["unit"] > 0}
    return active_portfolio, realized_pl

active_portfolio, total_realized_pl = calculate_portfolio_and_realized(df_transaksi)

if submit_button:
    try:
        clean_jml = jumlah_unit_str.replace(".", "").replace(",", ".").strip()
        jumlah_unit = float(clean_jml) if clean_jml else 0.0
    except ValueError:
        st.sidebar.error("Format jumlah unit tidak valid!")
        st.stop()

    try:
        clean_harga = harga_str.replace(".", "").replace(",", ".").strip()
        harga_input = float(clean_harga) if clean_harga else 0.0
    except ValueError:
        st.sidebar.error("Format harga tidak valid!")
        st.stop()

    try:
        clean_fee = persen_fee_str.replace(".", "").replace(",", ".").strip()
        persen_fee = float(clean_fee) if clean_fee else 0.0
    except ValueError:
        persen_fee = 0.15

    if kategori_asset == "Saham BEI":
        total_lembar = jumlah_unit * 100
        subtotal = total_lembar * harga_input
    else:
        if mata_uang_input == "USDT":
            subtotal = jumlah_unit * harga_input * current_usd
        else:
            subtotal = jumlah_unit * harga_input

    fee_transaksi = subtotal * (persen_fee / 100)
    
    if tipe == "BELI":
        total_kebutuhan = subtotal + fee_transaksi
        if total_kebutuhan > buying_power:
            formatted_butuh = f"Rp {total_kebutuhan:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
            st.sidebar.error(f"Gagal! Saldo RDN tidak cukup. Butuh {formatted_butuh}")
            st.stop()
        else:
            buying_power -= total_kebutuhan
            save_cash(buying_power)
            total_transaksi = total_kebutuhan
            add_mutasi_record(str(tanggal), "BELI ASET", f"Pembelian {kategori_asset} {kode_input} ({jumlah_unit} unit)", total_kebutuhan)
    else:  
        owned_units = active_portfolio.get(kode_input, {}).get("unit", 0.0)
        if jumlah_unit > owned_units and not df_transaksi.empty:
            st.sidebar.warning(f"Catatan: Penjualan melebihi sisa unit tercatat, transaksi tetap diproses.")
        total_penerimaan = subtotal - fee_transaksi
        buying_power += total_penerimaan
        save_cash(buying_power)
        total_transaksi = total_penerimaan
        add_mutasi_record(str(tanggal), "JUAL ASET", f"Penjualan {kategori_asset} {kode_input} ({jumlah_unit} unit)", total_penerimaan)

    new_id = int(df_transaksi["ID"].max()) + 1 if not df_transaksi.empty and "ID" in df_transaksi.columns else 1
    new_data = {
        "ID": new_id,
        "Tanggal": str(tanggal),
        "Kategori": kategori_asset,
        "Kode Saham": kode_input,
        "Tipe": tipe,
        "Jumlah Unit": jumlah_unit,
        "Harga per Lembar": harga_input,
        "Fee (Rp)": round(fee_transaksi, 2),
        "Total Transaksi (Rp)": round(total_transaksi, 2)
    }
    df_transaksi = pd.concat([df_transaksi, pd.DataFrame([new_data])], ignore_index=True)
    save_data(df_transaksi)
    st.sidebar.success(f"Berhasil {tipe} {kategori_asset} {kode_input}!")
    st.rerun()

# --- MARKET SENTIMENT & MACRO BAR DENGAN NAMA NASAR & MINI CHART ---
col_title_macro, col_name_nasar = st.columns([3, 1])
with col_title_macro:
    st.markdown("### 🌐 Market Macro Bar & Mini Trend Charts")
with col_name_nasar:
    st.markdown("<h3 style='text-align: right; color: #3b82f6; margin: 0;'>👤 NASAR</h3>", unsafe_allow_html=True)

if not df_macros.empty:
    df_tradisional = df_macros[df_macros["Tipe"] != "Crypto"]
    df_crypto = df_macros[df_macros["Tipe"] == "Crypto"]

    if not df_tradisional.empty:
        cols_t = st.columns(len(df_tradisional))
        for idx, row in df_tradisional.reset_index().iterrows():
            simbol = row["Simbol"]
            label = row["Label"]
            tipe = row["Tipe"]
            
            with cols_t[idx]:
                try:
                    m_data = yf.Ticker(simbol).history(period="5d")
                    if len(m_data) >= 2:
                        val = float(m_data['Close'].iloc[-1])
                        prev = float(m_data['Close'].iloc[-2])
                        chg = ((val - prev) / prev) * 100 if prev > 0 else 0
                        
                        if tipe == "Forex":
                            val_str = f"Rp {val:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
                            st.metric(f"💱 {label}", val_str, f"{chg:+.2f}%")
                        elif tipe == "Commodity":
                            st.metric(f"🪙 {label}", f"${val:,.2f}", f"{chg:+.2f}%")
                        elif tipe == "Stock":
                            val_str = f"Rp {val:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
                            st.metric(f"🏦 {label}", val_str, f"{chg:+.2f}%")
                        else:
                            st.metric(f"📊 {label}", f"{val:,.2f}", f"{chg:+.2f}%")
                        
                        fig_spark = go.Figure(data=go.Scatter(
                            x=m_data.index, y=m_data['Close'],
                            mode='lines',
                            line=dict(color='#26a69a' if chg >= 0 else '#ef5350', width=2)
                        ))
                        fig_spark.update_layout(
                            template="plotly_dark",
                            paper_bgcolor="#0e1117",
                            plot_bgcolor="#0e1117",
                            margin=dict(l=0, r=0, t=0, b=0),
                            height=45,
                            xaxis=dict(visible=False),
                            yaxis=dict(visible=False, autorange=True),
                            showlegend=False
                        )
                        st.plotly_chart(fig_spark, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.metric(f"📌 {label}", "Offline")
                except Exception:
                    st.metric(f"📌 {label}", "Offline")

    if not df_crypto.empty:
        cols_c = st.columns(len(df_crypto))
        for idx, row in df_crypto.reset_index().iterrows():
            simbol = row["Simbol"]
            label = row["Label"]
            
            with cols_c[idx]:
                try:
                    m_data = yf.Ticker(simbol).history(period="5d")
                    if len(m_data) >= 2:
                        val = float(m_data['Close'].iloc[-1])
                        prev = float(m_data['Close'].iloc[-2])
                        chg = ((val - prev) / prev) * 100 if prev > 0 else 0
                        st.metric(f"🪙 {label}", f"${val:,.2f}", f"{chg:+.2f}%")
                        
                        fig_spark = go.Figure(data=go.Scatter(
                            x=m_data.index, y=m_data['Close'],
                            mode='lines',
                            line=dict(color='#26a69a' if chg >= 0 else '#ef5350', width=2)
                        ))
                        fig_spark.update_layout(
                            template="plotly_dark",
                            paper_bgcolor="#0e1117",
                            plot_bgcolor="#0e1117",
                            margin=dict(l=0, r=0, t=0, b=0),
                            height=45,
                            xaxis=dict(visible=False),
                            yaxis=dict(visible=False, autorange=True),
                            showlegend=False
                        )
                        st.plotly_chart(fig_spark, use_container_width=True, config={'displayModeBar': False})
                    else:
                        st.metric(f"🪙 {label}", "Offline")
                except Exception:
                    st.metric(f"🪙 {label}", "Offline")

st.markdown("---")

# --- FUNGSI SEKTOR SAHAM BEI & KRIPTO ---
def get_sector(ticker, kategori):
    if kategori == "Kripto (USDT)":
        return "Crypto Asset (USDT)"
    financials = ["BBCA", "BBRI", "BMRI", "BBNI", "ARTO", "BRIS", "BBTN", "NISP", "BDMN"]
    energy = ["ADRO", "PTBA", "ITMG", "HRUM", "ANTM", "UNTR"]
    consumer = ["ICBP", "INDF", "UNVR", "MYOR", "GGRM", "HMSP"]
    infrastructure = ["TLKM", "ISAT", "EXCL", "JSMR", "WIKA", "ADHI"]
    
    if ticker in financials: return "Financials (Perbankan)"
    elif ticker in energy: return "Energy & Mining (Energi/Tambang)"
    elif ticker in consumer: return "Consumer Goods (Barang Konsumsi)"
    elif ticker in infrastructure: return "Infrastructure & Telco"
    else: return "Others / Lainnya"

# --- PROSES DATA RINGKASAN PORTOFOLIO MULTI-ASET ---
summary_list = []
for ticker, info in active_portfolio.items():
    unit = info["unit"]
    total_modal = info["total_modal"]
    kategori = info.get("kategori", "Saham BEI")
    if pd.isna(kategori): kategori = "Saham BEI"
    
    if kategori == "Saham BEI":
        total_lembar = unit * 100
        avg_price = total_modal / total_lembar if total_lembar > 0 else 0
        yf_ticker = f"{ticker}.JK"
    else:
        avg_price = (total_modal / current_usd) / unit if unit > 0 else 0
        yf_ticker = f"{ticker}-USD"
        
    try:
        stock = yf.Ticker(yf_ticker)
        hist = stock.history(period="1d")
        if not hist.empty:
            current_price_raw = float(hist['Close'].iloc[-1])
        else:
            current_price_raw = avg_price
    except Exception:
        current_price_raw = avg_price

    if kategori == "Saham BEI":
        current_price = current_price_raw
        nilai_sekarang = (unit * 100) * current_price
    else:
        current_price = current_price_raw  
        nilai_sekarang = unit * current_price * current_usd  
        
    profit_loss = nilai_sekarang - total_modal
    percentage = (profit_loss / total_modal * 100) if total_modal > 0 else 0
    
    summary_list.append({
        "Kode Aset": ticker,
        "Kategori": kategori,
        "Sektor": get_sector(ticker, kategori),
        "Jumlah (Lot/Unit)": unit,
        "Avg Price": round(avg_price, 2),
        "Harga Realtime": round(current_price, 2),
        "Total Modal (Rp)": round(total_modal, 2),
        "Nilai Sekarang (Rp)": round(nilai_sekarang, 2),
        "Unrealized P/L (Rp)": round(profit_loss, 2),
        "Unrealized P/L (%)": round(percentage, 2)
    })
    
df_summary = pd.DataFrame(summary_list)

total_investasi = df_summary["Total Modal (Rp)"].sum() if not df_summary.empty else 0
total_nilai_portofolio = df_summary["Nilai Sekarang (Rp)"].sum() if not df_summary.empty else 0
total_unrealized = total_nilai_portofolio - total_investasi
total_dividen_diterima = df_dividen["Jumlah Dividen (Rp)"].sum() if not df_dividen.empty else 0

total_kekayaan = total_nilai_portofolio + buying_power + bank_cash

# --- TAMPILAN UTAMA BERBASIS TAB (10 TAB LENGKAP BERSAMA BERITA) ---
tab_dash, tab_port, tab_cal, tab_alert, tab_div, tab_watch, tab_news, tab_hist, tab_report, tab_sim = st.tabs([
    "📊 Dashboard", 
    "📋 Portofolio & Risiko", 
    "📅 Kalender Korporasi",
    "🔔 Price Alert",
    "💵 Dividen",
    "⭐ Watchlist", 
    "📰 Berita Pasar",
    "📜 Riwayat & Mutasi Kas",
    "📑 Laporan Bulanan",
    "🔮 Simulasi & Proyeksi"
])

# --- TAB 1: DASHBOARD ---
with tab_dash:
    dashboard.render(total_kekayaan, total_nilai_portofolio, buying_power, bank_cash, total_investasi, total_unrealized, total_realized_pl, total_dividen_diterima, df_transaksi)

# --- TAB 2: PORTOFOLIO & RISIKO ---
with tab_port:
    portofolio.render(df_summary, buying_power, bank_cash, total_kekayaan, total_nilai_portofolio)

# --- TAB 3: CORPORATE ACTIONS CALENDAR ---
with tab_cal:
    kalender.render(active_portfolio, df_watchlist)

# --- TAB 4: PRICE ALERT ---
with tab_alert:
    alert.render(df_alerts, save_alerts)

# --- TAB 5: DIVIDEN ---
with tab_div:
    dividen.render(df_dividen, buying_power, save_dividends, save_cash, add_mutasi_record, active_portfolio)

# --- TAB 6: WATCHLIST ---
with tab_watch:
    watchlist.render(df_watchlist, save_watchlist)

# --- TAB 7: BERITA PASAR REAL-TIME ---
with tab_news:
    berita.render()

# --- TAB 8: RIWAYAT & MUTASI KAS ---
with tab_hist:
    riwayat.render(df_transaksi, buying_power, save_cash, save_data, load_mutasi)

# --- TAB 9: LAPORAN KINERJA BULANAN ---
with tab_report:
    laporan.render(df_transaksi, total_dividen_diterima, total_realized_pl)

# --- TAB 10: SIMULASI & PROYEKSI KEKAYAAN ---
with tab_sim:
    simulasi.render(total_kekayaan)

# --- IKON SEGITIGA TERSEMBUNYI DI POJOK KANAN BAWAH (ZONA RESET) ---
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown("<div style='text-align: right;'>", unsafe_allow_html=True)
with st.popover("⚠️"):
    st.markdown("### ⚠️ Reset Total Terminal")
    st.warning("Tindakan ini akan menghapus seluruh data transaksi, kas, dividen, dan watchlist secara permanen.")
    confirm_input = st.text_input("Ketik kata **KONFIRMASI** untuk melanjutkan:", value="")
    
    is_code_correct = (confirm_input.strip() == "KONFIRMASI")
    if st.button("Hapus Permanen Semua Data", disabled=not is_code_correct):
        if is_code_correct:
            for f in [DATA_FILE, CASH_FILE, BANK_CASH_FILE, MUTASI_FILE, WATCHLIST_FILE, DIVIDEND_FILE, ALERT_FILE]:
                if os.path.exists(f): os.remove(f)
            st.success("Semua data terminal berhasil di-reset!")
            st.rerun()
st.markdown("</div>", unsafe_allow_html=True)