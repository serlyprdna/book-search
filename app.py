import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# Konfigurasi halaman
st.set_page_config(
    page_title="Books to Scrape - Search Engine",
    page_icon="📚",
    layout="wide"
)

# Judul aplikasi
st.title("📚 Books to Scrape - Search Engine")
st.markdown("---")

# Fungsi untuk memuat data
@st.cache_data
def load_data():
    try:
        with open('data/books.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    except FileNotFoundError:
        st.error("File data/books.json tidak ditemukan! Pastikan Anda sudah menjalankan spider Scrapy.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error saat memuat data: {str(e)}")
        return pd.DataFrame()

# Memuat data
df = load_data()

if not df.empty:
    # Sidebar untuk filter
    st.sidebar.header("🔍 Filter & Search")
    
    # Search box
    search_query = st.sidebar.text_input("Cari buku:", placeholder="Masukkan judul buku...")
    
    # Filter berdasarkan kategori
    categories = ['All'] + sorted(df['category'].unique().tolist())
    selected_category = st.sidebar.selectbox("Kategori:", categories)
    
    # Filter berdasarkan rating
    rating_filter = st.sidebar.slider("Rating minimum:", 1, 5, 1)
    
    # Filter berdasarkan harga
    if 'price' in df.columns:
        # Konversi harga ke format numerik
        df['price_numeric'] = df['price'].str.replace('£', '').astype(float)
        min_price = float(df['price_numeric'].min())
        max_price = float(df['price_numeric'].max())
        
        price_range = st.sidebar.slider(
            "Range harga (£):", 
            min_price, 
            max_price, 
            (min_price, max_price)
        )
    
    # Filter berdasarkan ketersediaan
    availability_filter = st.sidebar.checkbox("Hanya buku yang tersedia")
    
    # Aplikasikan filter
    filtered_df = df.copy()
    
    # Filter search
    if search_query:
        filtered_df = filtered_df[
            filtered_df['title'].str.contains(search_query, case=False, na=False) |
            filtered_df['description'].str.contains(search_query, case=False, na=False)
        ]
    
    # Filter kategori
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    
    # Filter rating
    filtered_df = filtered_df[filtered_df['rating'] >= rating_filter]
    
    # Filter harga
    if 'price_numeric' in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df['price_numeric'] >= price_range[0]) & 
            (filtered_df['price_numeric'] <= price_range[1])
        ]
    
    # Filter ketersediaan
    if availability_filter:
        filtered_df = filtered_df[filtered_df['availability'].astype(int) > 0]
    
    # Statistik
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Buku", len(df))
    
    with col2:
        st.metric("Hasil Filter", len(filtered_df))
    
    with col3:
        avg_rating = filtered_df['rating'].mean()
        st.metric("Rating Rata-rata", f"{avg_rating:.1f}" if not pd.isna(avg_rating) else "N/A")
    
    with col4:
        if 'price_numeric' in filtered_df.columns:
            avg_price = filtered_df['price_numeric'].mean()
            st.metric("Harga Rata-rata", f"£{avg_price:.2f}" if not pd.isna(avg_price) else "N/A")
    
    st.markdown("---")
    
    # Sorting options
    sort_options = {
        'Title (A-Z)': 'title',
        'Title (Z-A)': 'title',
        'Price (Low to High)': 'price_numeric',
        'Price (High to Low)': 'price_numeric',
        'Rating (High to Low)': 'rating',
        'Rating (Low to High)': 'rating'
    }
    
    sort_by = st.selectbox("Urutkan berdasarkan:", list(sort_options.keys()))
    
    # Aplikasikan sorting
    if sort_by:
        ascending = 'Low to High' in sort_by or 'A-Z' in sort_by
        sort_column = sort_options[sort_by]
        filtered_df = filtered_df.sort_values(sort_column, ascending=ascending)
    
    # Pagination
    items_per_page = st.selectbox("Tampilkan per halaman:", [10, 20, 50, 100], index=1)
    
    total_pages = len(filtered_df) // items_per_page + (1 if len(filtered_df) % items_per_page > 0 else 0)
    
    if total_pages > 1:
        page = st.number_input("Halaman:", min_value=1, max_value=total_pages, value=1)
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_df = filtered_df.iloc[start_idx:end_idx]
    else:
        page_df = filtered_df
    
    # Tampilkan hasil
    st.subheader(f"📖 Hasil Pencarian ({len(filtered_df)} buku)")
    
    if len(page_df) == 0:
        st.info("Tidak ada buku yang ditemukan dengan kriteria pencarian tersebut.")
    else:
        # Tampilkan buku dalam format card
        for idx, book in page_df.iterrows():
            with st.container():
                col1, col2 = st.columns([1, 4])
                
                with col1:
                    if book['image_url']:
                        st.image(book['image_url'], width=120)
                    else:
                        st.write("📚")
                
                with col2:
                    st.markdown(f"### {book['title']}")
                    
                    # Rating stars
                    stars = "⭐" * int(book['rating']) + "☆" * (5 - int(book['rating']))
                    st.markdown(f"**Rating:** {stars} ({book['rating']}/5)")
                    
                    # Info dasar
                    info_col1, info_col2, info_col3 = st.columns(3)
                    
                    with info_col1:
                        st.markdown(f"**Harga:** {book['price']}")
                    
                    with info_col2:
                        st.markdown(f"**Kategori:** {book['category']}")
                    
                    with info_col3:
                        availability = int(book['availability']) if book['availability'].isdigit() else 0
                        if availability > 0:
                            st.markdown(f"**Stok:** {availability} tersedia")
                        else:
                            st.markdown("**Stok:** Tidak tersedia")
                    
                    # Deskripsi
                    if book['description'] and book['description'] != "No description available":
                        with st.expander("Lihat deskripsi"):
                            st.write(book['description'])
                    
                    # Link ke buku
                    st.markdown(f"[Lihat di website]({book['url']})")
                
                st.markdown("---")
        
        # Pagination info
        if total_pages > 1:
            st.markdown(f"Halaman {page} dari {total_pages}")
    
    # Chart dan statistik tambahan
    st.markdown("---")
    st.subheader("📊 Statistik & Analisis")
    
    tab1, tab2, tab3 = st.tabs(["Distribusi Rating", "Kategori Populer", "Analisis Harga"])
    
    with tab1:
        rating_counts = filtered_df['rating'].value_counts().sort_index()
        st.bar_chart(rating_counts)
    
    with tab2:
        category_counts = filtered_df['category'].value_counts().head(10)
        st.bar_chart(category_counts)
    
    with tab3:
        if 'price_numeric' in filtered_df.columns:
            st.line_chart(filtered_df[['price_numeric']].sort_values('price_numeric'))
    
    # Export data
    st.markdown("---")
    st.subheader("💾 Export Data")
    
    if st.button("Download hasil filter sebagai CSV"):
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"filtered_books_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

else:
    st.error("Tidak dapat memuat data. Pastikan file data/books.json ada dan berisi data yang valid.")
    st.info("Untuk menjalankan scraping, gunakan command: `scrapy crawl books -o data/books.json`")

# Footer
st.markdown("---")
st.markdown("**Dibuat untuk UAS Information Retrieval - Universitas Abulyatama**")
st.markdown("*Dosen: Teuku Rizky Noviandy, S.Kom., M.Kom.*")