import streamlit as st
from datetime import date
from menu_data import menu_data
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Setup Google Sheets
def connect_gsheet():
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("gspread_key.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("penjualan_roti_maryam").sheet1
    return sheet

# Simpan transaksi
def simpan_ke_gsheet(data):
    sheet = connect_gsheet()
    row = [data["Tanggal"], data["Menu"], data["Jumlah"], data["Harga"], data["Total"], data["Topping"]]
    sheet.append_row(row)
    
# ABC Analysis
def get_data_by_date(sheet, target_date):
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    df['Tanggal'] = pd.to_datetime(df['Tanggal'])
    df_filtered = df[df['Tanggal'] == pd.to_datetime(target_date)]
    return df_filtered

def abc_analysis(df):
    df_grouped = df.groupby('Menu')['Total'].sum().reset_index()
    df_grouped = df_grouped.sort_values(by='Total', ascending=False)
    df_grouped['Persentase'] = 100 * df_grouped['Total'] / df_grouped['Total'].sum()
    df_grouped['Kumulatif'] = df_grouped['Persentase'].cumsum()

    def kategori(persen):
        if persen <= 70:
            return 'A'
        elif persen <= 90:
            return 'B'
        else:
            return 'C'

    df_grouped['Kategori'] = df_grouped['Kumulatif'].apply(kategori)
    return df_grouped
    
# UI
st.title("📋 Pencatatan Penjualan Roti Maryam")

tanggal = st.date_input("Tanggal", value=date.today())
menu_selected = st.selectbox("Pilih Menu", list(menu_data.keys()))
jumlah = st.number_input("Jumlah Terjual", min_value=1, step=1)

if menu_selected:
    harga = menu_data[menu_selected]["harga"]
    topping = ", ".join(menu_data[menu_selected]["topping"])
    total = harga * jumlah

    st.write(f"💰 Harga per pcs: Rp{harga}")
    st.write(f"🍫 Topping: {topping}")
    st.write(f"📦 Total Pendapatan: Rp{total}")

    if st.button("✅ Simpan Transaksi"):
        data = {
            "Tanggal": tanggal.strftime("%Y-%m-%d"),
            "Menu": menu_selected,
            "Jumlah": jumlah,
            "Harga": harga,
            "Total": total,
            "Topping": topping
        }
        simpan_ke_gsheet(data)
        st.success("Transaksi berhasil disimpan ke Google Sheets!")
        
st.subheader("📊 Lihat ABC Analysis Hari Ini")

if st.button("🔍 Tampilkan ABC Analysis Hari Ini"):
    sheet = connect_gsheet()
    df_today = get_data_by_date(sheet, tanggal)

    if not df_today.empty:
        df_abc = abc_analysis(df_today)
        st.write("Hasil ABC Analysis:")
        st.dataframe(df_abc)
    else:
        st.warning("Belum ada transaksi di tanggal ini.")
