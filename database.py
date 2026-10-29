import os
import pandas as pd

DATA_FILE = "transaksi_saham.csv"
CASH_FILE = "buying_power.csv"
BANK_CASH_FILE = "rekening_bank.csv"
MUTASI_FILE = "mutasi_kas.csv"
WATCHLIST_FILE = "watchlist.csv"
DIVIDEND_FILE = "dividen.csv"
ALERT_FILE = "price_alerts.csv"
MACRO_CONFIG_FILE = "macro_watchlist.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if "Kategori" not in df.columns:
            df["Kategori"] = "Saham BEI"
        else:
            df["Kategori"] = df["Kategori"].fillna("Saham BEI")
        return df
    else:
        return pd.DataFrame(columns=["ID", "Tanggal", "Kategori", "Kode Saham", "Tipe", "Jumlah Unit", "Harga per Lembar", "Fee (Rp)", "Total Transaksi (Rp)"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def load_cash():
    if os.path.exists(CASH_FILE):
        df_cash = pd.read_csv(CASH_FILE)
        return float(df_cash["Saldo"].iloc[0])
    else:
        return 10000000.0

def save_cash(amount):
    df_cash = pd.DataFrame([{"Saldo": amount}])
    df_cash.to_csv(CASH_FILE, index=False)

def load_bank_cash():
    if os.path.exists(BANK_CASH_FILE):
        df_bank = pd.read_csv(BANK_CASH_FILE)
        return float(df_bank["Saldo"].iloc[0])
    else:
        return 50000000.0

def save_bank_cash(amount):
    df_bank = pd.DataFrame([{"Saldo": amount}])
    df_bank.to_csv(BANK_CASH_FILE, index=False)

def load_mutasi():
    if os.path.exists(MUTASI_FILE):
        return pd.read_csv(MUTASI_FILE)
    else:
        return pd.DataFrame(columns=["ID", "Tanggal", "Jenis", "Keterangan", "Jumlah (Rp)"])

def save_mutasi(df):
    df.to_csv(MUTASI_FILE, index=False)

def add_mutasi_record(tanggal_str, jenis, ket, jumlah):
    df_m = load_mutasi()
    new_id = int(df_m["ID"].max()) + 1 if not df_m.empty and "ID" in df_m.columns else 1
    new_row = {
        "ID": new_id,
        "Tanggal": str(tanggal_str),
        "Jenis": jenis,
        "Keterangan": ket,
        "Jumlah (Rp)": round(jumlah, 2)
    }
    df_m = pd.concat([df_m, pd.DataFrame([new_row])], ignore_index=True)
    save_mutasi(df_m)

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        return pd.read_csv(WATCHLIST_FILE)
    else:
        return pd.DataFrame(columns=["Kode Saham"])

def save_watchlist(df):
    df.to_csv(WATCHLIST_FILE, index=False)

def load_dividends():
    if os.path.exists(DIVIDEND_FILE):
        df_div = pd.read_csv(DIVIDEND_FILE)
        if "Tahun" not in df_div.columns and "Tanggal" in df_div.columns:
            df_div["Tahun"] = pd.to_datetime(df_div["Tanggal"]).dt.year
        return df_div
    else:
        return pd.DataFrame(columns=["ID", "Tanggal", "Tahun", "Kode Saham", "Jumlah Dividen (Rp)"])

def save_dividends(df):
    df.to_csv(DIVIDEND_FILE, index=False)

def load_alerts():
    if os.path.exists(ALERT_FILE):
        return pd.read_csv(ALERT_FILE)
    else:
        return pd.DataFrame(columns=["ID", "Kode Saham", "Target Harga", "Aksi Target"])

def save_alerts(df):
    df.to_csv(ALERT_FILE, index=False)

def load_macro_config():
    if os.path.exists(MACRO_CONFIG_FILE):
        return pd.read_csv(MACRO_CONFIG_FILE)
    else:
        default_macros = pd.DataFrame({
            "Simbol": ["^JKSE", "IDR=X", "GC=F", "^GSPC", "BBRI.JK", "BMRI.JK", "BTC-USD", "ETH-USD", "SOL-USD"],
            "Label": ["IHSG", "USD/IDR", "Emas", "S&P 500", "BBRI", "BMRI", "Bitcoin", "Ethereum", "Solana"],
            "Tipe": ["Index", "Forex", "Commodity", "Index", "Stock", "Stock", "Crypto", "Crypto", "Crypto"]
        })
        default_macros.to_csv(MACRO_CONFIG_FILE, index=False)
        return default_macros

def save_macro_config(df):
    df.to_csv(MACRO_CONFIG_FILE, index=False)