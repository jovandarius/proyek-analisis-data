import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

st.set_page_config(
    page_title="E-Commerce Performance Dashboard",
    page_icon='🛒',
    layout="wide"
)
sns.set_theme(style='whitegrid')

@st.cache_data
def load_main_data():
    df = pd.read_csv("main_data.csv")
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    return df

main_df = load_main_data()

# Sidebar
st.sidebar.title("E-Commerce Dashboard")
st.sidebar.markdown("**Nama:** Jovan Darius Gonza")
st.sidebar.markdown("**ID Dicoding:** DS001B6Y1890")
st.sidebar.markdown("---")

min_date = main_df['order_purchase_timestamp'].min().date()
max_date = main_df['order_purchase_timestamp'].max().date()

start_date, end_date = st.sidebar.date_input(
    label="Pilih Rentang Transaksi",
    min_value=min_date,
    max_value=max_date,
    value=[min_date, max_date]
)

filtered_df = main_df[
    (main_df['order_purchase_timestamp'].dt.date >= start_date) &
    (main_df['order_purchase_timestamp'].dt.date <= end_date)
]

st.title("E-Commerce Public Data Performance Dashboard")
st.markdown("Analisis Kinerja Logistik Pengiriman dan Tren Pendapatan Produk (Jan 2027 - Ags 2018)")

st.subheader("Overview Kinerja")
col1, col2, col3, col4 = st.columns(4)

total_orders = filtered_df['order_id'].nunique()
total_revenue = filtered_df['price'].sum()
avg_review = filtered_df['review_score'].mean()
delay_rate = (filtered_df['is_delayed'].sum() / len(filtered_df) * 100 if len(filtered_df) > 0 else 0)

with col1:
    st.metric(label="Total Pesanan", value=f"{total_orders:,}")
with col2:
    st.metric(label="Total Pendapatan", value=f"R$ {total_revenue:,.2f}")
with col3:
    st.metric(label="Rerata Ulasan", value=f"{avg_review:.2f} / 5.00")
with col4:
    st.metric(label="Tingkat Keterlambatan", value=f"{delay_rate:.2f}%")

st.markdown("---")

# Bagian 1: Analisis Keterlambatan Pengiriman & Ulasan Pelanggan
st.header("1. Dampak Keterlambatan Pengiriman terhadap Kepuasan Pelanggan")

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Rerata Skor Ulasan (Tepat Waktu vs Terlambat)")
    review_summary = filtered_df.groupby('is_delayed')['review_score'].mean().reset_index()
    review_summary['status_label'] = review_summary['is_delayed'].map({False: 'Tepat Waktu / Cepat', True: 'Terlambat'})

    fig, ax = plt.subplots(figsize=(6, 4))
    sns.barplot(
        x='status_label',
        y='review_score',
        data=review_summary,
        palette=['#2ca02c', '#d62728'],
        ax=ax
    )
    ax.set_xlabel("Status Pengiriman")
    ax.set_ylabel("Rerata Skor Ulasan (1-5)")
    ax.set_ylim(0, 5)
    for p in ax.patches:
        ax.annotate(f"{p.get_height():.2f}", 
                    (p.get_x() + p.get_width() / 2., p.get_height() / 2),
                    ha='center', va='center', fontsize=11, color='white', fontweight='bold')
    st.pyplot(fig)

with col_right:
    st.subheader("Tingkat Keterlambatan per Negara Bagian (%)")
    top_10_states = filtered_df['customer_state'].value_counts().head(10).index
    state_delay = filtered_df[filtered_df['customer_state'].isin(top_10_states)].groupby('customer_state').agg(
        delay_rate=('is_delayed', 'mean')
    ).reset_index()
    state_delay['delay_rate_pct'] = state_delay['delay_rate'] * 100
    state_delay = state_delay.sort_values(by='delay_rate_pct', ascending=False)

    fig, ax = plt.subplots(figsize=(6, 4))
    sns.barplot(
        x='delay_rate_pct',
        y='customer_state',
        data=state_delay,
        palette='Blues_r',
        ax=ax
    )
    ax.set_xlabel("Persentase Keterlambatan (%)")
    ax.set_ylabel("Negara Bagian (State)")
    for p in ax.patches:
        ax.annotate(f"{p.get_width():.1f}%", 
                    (p.get_width() + 0.3, p.get_y() + p.get_height() / 2.),
                    ha='center', va='center', fontsize=9, color='black')
    st.pyplot(fig)

st.markdown("---")

# Bagian 2: Analisis Pendapatan & Tren Kategori Produk
st.header("2. Kinerja Pendapatan Kategori Produk")

col_cat1, col_cat2 = st.columns([1, 2])

with col_cat1:
    st.subheader("Top 10 Kategori Produk (Revenue)")
    top_categories = filtered_df.groupby('product_category_name_english')['price'].sum().reset_index()
    top_categories = top_categories.sort_values(by='price', ascending=False).head(10)
    
    fig, ax = plt.subplots(figsize=(5, 6))
    sns.barplot(
        x='price',
        y='product_category_name_english',
        data=top_categories,
        palette='Greens_r',
        ax=ax
    )
    ax.set_xlabel("Total Pendapatan (BRL)")
    ax.set_ylabel("Kategori Produk")
    st.pyplot(fig)

with col_cat2:
    st.subheader("Tren Pendapatan Bulanan (Top 3 Kategori)")
    top_3_cats = top_categories.head(3)['product_category_name_english'].tolist()
    
    filtered_df['year_month'] = filtered_df['order_purchase_timestamp'].dt.to_period('M')
    monthly_top3 = filtered_df[filtered_df['product_category_name_english'].isin(top_3_cats)].groupby(
        ['year_month', 'product_category_name_english']
    )['price'].sum().unstack().fillna(0)
    monthly_top3.index = monthly_top3.index.astype(str)

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    for idx, col in enumerate(monthly_top3.columns):
        ax.plot(
            monthly_top3.index, 
            monthly_top3[col], 
            marker='o', 
            linewidth=2, 
            color=colors[idx % len(colors)],
            label=col.replace('_', ' ').title()
        )
    ax.set_xlabel("Bulan Transaksi")
    ax.set_ylabel("Pendapatan (BRL)")
    plt.xticks(rotation=45)
    ax.legend(title="Kategori Produk")
    st.pyplot(fig)

st.markdown("---")

# Bagian 3: Kesimpulan & Rekomendasi
st.header("💡 Kesimpulan & Rekomendasi Bisnis")

st.success("""
**Kesimpulan Utama:**
1. **Pengaruh Keterlambatan:** Keterlambatan pengiriman menurunkan skor ulasan secara drastis dari **4.29** menjadi **2.57**. Negara bagian **Bahia (BA)** dan **Rio de Janeiro (RJ)** mengalami keterlambatan tertinggi (>13%).
2. **Kategori Penjualan Teratas:** **Health & Beauty**, **Watches & Gifts**, dan **Bed, Bath & Table** mendominasi total pendapatan. Kategori *Health & Beauty* menunjukkan tren pertumbuhan bulanan paling konsisten sepanjang 2018.
""")

st.info("""
**Rekomendasi Action Item:**
- **Evaluasi Kurir Regional:** Lakukan renegosiasi SLA dan penataan ulang rute kurir pengiriman di wilayah Bahia (BA) dan Rio de Janeiro (RJ).
- **Manajemen Stok & Promosi:** Prioritaskan stok produk *Health & Beauty* untuk menjaga pertumbuhan, serta manfaatkan lonjakan musiman bulan Mei (*Watches & Gifts*) dan November (*Bed, Bath & Table*).
""")
