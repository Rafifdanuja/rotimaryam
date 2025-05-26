import streamlit as st
from datetime import date
from menu_data import menu_data
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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

