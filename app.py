import streamlit as st
from datetime import date
from menu_data import menu_data
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# --- Setup Google Sheets
def connect_gsheet():
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds_dict["private_key"] = creds_dict["private_key"].replace('\\n', '\n')

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open("penjualan_roti_maryam").sheet1

def simpan_ke_gsheet(data):
    sheet = connect_gsheet()
    row = [data["Tanggal"], data["Menu"], data["Jumlah"], data["Harga"], data["Total"], data["Topping"]]
    sheet.append_row(row)

# --- Data Analysis Functions
def get_data_by_date(sheet, target_date):
    df = pd.DataFrame(sheet.get_all_records())
    df['Tanggal'] = pd.to_datetime(df['Tanggal'])
    return df[df['Tanggal'] == pd.to_datetime(target_date)]

def get_data_last_week(sheet, end_date):
    df = pd.DataFrame(sheet.get_all_records())
    df['Tanggal'] = pd.to_datetime(df['Tanggal'])
    start_date = pd.to_datetime(end_date) - pd.Timedelta(days=6)
    return df[(df['Tanggal'] >= start_date) & (df['Tanggal'] <= pd.to_datetime(end_date))]

def abc_analysis(df):
    grouped = df.groupby('Menu')['Total'].sum().reset_index()
    grouped = grouped.sort_values(by='Total', ascending=False)
    grouped['Persentase'] = 100 * grouped['Total'] / grouped['Total'].sum()
    grouped['Kumulatif'] = grouped['Persentase'].cumsum()

    def kategori(p):
        return 'A' if p <= 70 else 'B' if p <= 90 else 'C'

    grouped['Kategori'] = grouped['Kumulatif'].apply(kategori)
    return grouped

# --- UI Starts Here
st.set_page_config(page_title="Pencatatan Penjualan Roti Maryam", layout="centered")
st.markdown("# 📋 Pencatatan Penjualan Roti Maryam")
st.markdown("Sistem pencatatan transaksi harian berbasis Google Sheets dengan analisis ABC otomatis.")

# --- Form Input
with st.form("form_transaksi"):
    st.subheader("🛒 Input Transaksi")

    col1, col2 = st.columns(2)
    with col1:
        tanggal = st.date_input("📅 Tanggal", value=date.today(), help="Pilih tanggal transaksi.")
    with col2:
        jumlah = st.number_input("🔢 Jumlah Roti Terjual", min_value=1, step=1, help="Masukkan jumlah yang terjual.")

    menu_selected = st.selectbox("🍽️ Pilih Menu Roti", list(menu_data.keys()), help="Pilih varian menu roti yang terjual.")

    harga = menu_data[menu_selected]["harga"]
    topping = ", ".join(menu_data[menu_selected]["topping"])
    total = harga * jumlah

    st.markdown(f"💰 **Harga per pcs:** Rp{harga:,}")
    st.markdown(f"🍫 **Topping:** {topping}")
    st.markdown(f"📦 **Total Pendapatan:** Rp{total:,}")

    submitted = st.form_submit_button("💾 Simpan Transaksi ke Google Sheets")
    if submitted:
        data = {
            "Tanggal": tanggal.strftime("%Y-%m-%d"),
            "Menu": menu_selected,
            "Jumlah": jumlah,
            "Harga": harga,
            "Total": total,
            "Topping": topping
        }
        simpan_ke_gsheet(data)
        st.success("✅ Transaksi berhasil disimpan ke Google Sheets!")

# --- ABC Analysis Hari Ini
with st.expander("🔍 Lihat ABC Analysis Hari Ini", expanded=False):
    st.subheader("📊 ABC Hari Ini")
    sheet = connect_gsheet()
    df_today = get_data_by_date(sheet, tanggal)

    if not df_today.empty:
        df_abc = abc_analysis(df_today)
        st.dataframe(df_abc, use_container_width=True)
    else:
        st.warning("⚠️ Belum ada transaksi pada tanggal ini.")

# --- ABC Analysis Mingguan
st.markdown("---")
st.subheader("📈 ABC Analysis 7 Hari Terakhir")

with st.expander("📅 Lihat ABC Analysis Mingguan"):
    sheet = connect_gsheet()
    df_week = get_data_last_week(sheet, tanggal)

    if not df_week.empty:
        df_abc_week = abc_analysis(df_week)
        st.dataframe(df_abc_week, use_container_width=True)
    else:
        st.warning("⚠️ Tidak ditemukan transaksi selama 7 hari terakhir.")
