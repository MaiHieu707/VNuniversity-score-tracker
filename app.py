import streamlit as st
import pandas as pd
import os
import re

# 1. Cấu hình
st.set_page_config(layout="wide", page_title="Hệ Thống Lọc Điểm Chuẩn", page_icon="🎓")

# 2. Giao diện
custom_style = """
<style>
    .stApp { background-color: #1e1e2f; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #27293d; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        border-radius: 12px !important;
        background-color: #1e1e2f !important;
        color: white !important;
        border: 1px solid #4a4a6a !important;
    }
    [data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; border: 1px solid #27293d; margin-bottom: 25px; }
    h1 { color: #8c54ff; font-weight: 700 !important; }
    button[data-testid="stFormSubmitButton"] {
        background-color: #8c54ff !important; color: white !important; border-radius: 10px !important;
        border: none !important; width: 100% !important; padding: 10px 0px !important; font-weight: bold !important;
    }
    div.stButton > button { background-color: #27293d; color: #69b1ff; border: 1px solid #4a4a6a; border-radius: 8px; }
</style>
"""
st.markdown(custom_style, unsafe_allow_html=True)

if 'search_params' not in st.session_state:
    st.session_state.search_params = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1

# 3. TỐI ƯU HÓA BỘ NHỚ (Đưa hàm xử lý nặng vào Cache để không chạy lại)
@st.cache_data
def load_and_prepare_data(file_path):
    df = pd.read_excel(file_path)
    
    col_diem = [c for c in df.columns if 'điểm' in c.lower() or 'score' in c.lower()][0]
    col_khoi = [c for c in df.columns if 'khối' in c.lower() or 'tổ hợp' in c.lower()][0]
    ma_nganh_cols = [c for c in df.columns if 'mã ngành' in c.lower() or 'mã xét tuyển' in c.lower()]
    col_ma_nganh = ma_nganh_cols[0] if ma_nganh_cols else None
    
    truong_cols = [c for c in df.columns if 'trường' in c.lower() or 'school' in c.lower() or 'mã trường' in c.lower()]
    if truong_cols:
        col_truong = truong_cols[0]
    else:
        if 'Link_Nguồn' in df.columns:
            df['Mã Trường'] = df['Link_Nguồn'].apply(lambda x: str(x).split('/')[-1].split('-')[-1].replace('.html', '').upper() if pd.notna(x) else 'UNKNOWN')
            col_truong = 'Mã Trường'
        else:
            df['Trường'] = 'Đại Học'
            col_truong = 'Trường'
            
    if 'Link_Nguồn' in df.columns:
        df['Bậc Đào Tạo'] = df['Link_Nguồn'].apply(lambda x: 'Cao đẳng' if 'cao-dang' in str(x).lower() else 'Đại học')
    else:
        df['Bậc Đào Tạo'] = 'Đại học'
            
    df[col_diem] = pd.to_numeric(df[col_diem], errors='coerce')

    # --- DỜI PHẦN QUÉT KHỐI VÀO TRONG CACHE ĐỂ KHÔNG BỊ TRÀN RAM CPU ---
    raw_khoi_list = df[col_khoi].dropna().astype(str).tolist()
    all_blocks = []
    for item in raw_khoi_list:
        all_blocks.extend(re.findall(r'\b[A-Z]\d{2}\b', item.upper()))
    clean_khoi = sorted(list(set(all_blocks)))
    # ------------------------------------------------------------------

    return df, col_diem, col_khoi, col_truong, col_ma_nganh, clean_khoi

data_file = "Tong_Hop_Diem_Chuan_Toan_Bo.xlsx"
if not os.path.exists(data_file):
    st.error(f"❌ Không tìm thấy file cơ sở dữ liệu: `{data_file}`")
    st.stop()

# Nhận thêm biến clean_khoi từ hàm Cache
df, col_diem, col_khoi, col_truong, col_ma_nganh, clean_khoi = load_and_prepare_data(data_file)

# 5. Form Sidebar
with st.sidebar.form(key='filter_form'):
    st.markdown("<h2 style='color:#8c54ff; text-align:center;'>⚙️ BỘ LỌC ĐIỂM</h2>", unsafe_allow_html=True)
    st.write("---")
    
    search_query = st.text_input("🔍 Tìm kiếm Trường (Tên/Mã):", placeholder="Ví dụ: BKA, Kinh tế...")
    search_ma_nganh = st.text_input("🆔 Tìm theo Mã Ngành:", placeholder="Ví dụ: 7480201...")
    bac_dao_tao = st.selectbox("🎓 Chọn Bậc đào tạo:", ["Tất cả", "Đại học", "Cao đẳng"])
    selected_khoi = st.selectbox("📚 Chọn Khối xét tuyển:", ["Tất cả"] + clean_khoi)
    diem_thi = st.slider("🎯 Điểm số của bạn:", min_value=0.0, max_value=40.0, value=25.0, step=0.25)
    
    submit_button = st.form_submit_button(label="🔍 Áp dụng bộ lọc & Tìm kiếm")
    
    if submit_button:
        st.session_state.search_params = {
            'query': search_query,
            'ma_nganh': search_ma_nganh,
            'bac': bac_dao_tao,
            'khoi': selected_khoi,
            'diem': diem_thi
        }
        st.session_state.current_page = 1

# 6. Khu vực hiển thị
st.title("🎓 HỆ THỐNG LỌC ĐIỂM CHUẨN ĐẠI HỌC")

if st.session_state.search_params is not None:
    params = st.session_state.search_params
    
    # Dùng nguyên DataFrame (không copy để tiết kiệm RAM)
    filtered_df = df
    
    if params['query']:
        filtered_df = filtered_df[filtered_df[col_truong].astype(str).str.contains(params['query'], case=False, na=False)]
    if params['ma_nganh'] and col_ma_nganh:
        filtered_df = filtered_df[filtered_df[col_ma_nganh].astype(str).str.contains(params['ma_nganh'], na=False)]
    if params['bac'] != "Tất cả":
        filtered_df = filtered_df[filtered_df['Bậc Đào Tạo'] == params['bac']]
    if params['khoi'] != "Tất cả":
        filtered_df = filtered_df[filtered_df[col_khoi].astype(str).str.contains(params['khoi'], case=False, na=False)]
        
    filtered_df = filtered_df[(filtered_df[col_diem] <= params['diem']) & (filtered_df[col_diem] > 0)]
    filtered_df = filtered_df.sort_values(by=col_diem, ascending=False)
    
    st.markdown(f"Khối xét: **{params['khoi']}** | Điểm tối đa: **{params['diem']}** | Bậc: **{params['bac']}**")
    st.markdown(f"### 📊 Tìm thấy **{len(filtered_df)}** ngành phù hợp")
    st.markdown("---")
    
    if len(filtered_df) > 0:
        grouped = filtered_df.groupby(col_truong, sort=False)
        school_list = list(grouped.groups.keys())
        
        schools_per_page = 10
        total_schools = len(school_list)
        total_pages = (total_schools - 1) // schools_per_page + 1
        
        if st.session_state.current_page > total_pages:
            st.session_state.current_page = total_pages
            
        start_idx = (st.session_state.current_page - 1) * schools_per_page
        end_idx = start_idx + schools_per_page
        current_schools_page = school_list[start_idx:end_idx]
        
        st.markdown(f"**Hiển thị trang {st.session_state.current_page} / {total_pages}**")
        
        cols_to_hide = [c for c in filtered_df.columns if 'unnamed' in c.lower() or c in ['Link_Nguồn', 'Bậc Đào Tạo']]
        
        for school in current_schools_page:
            st.markdown(f"<h4 style='color:#69b1ff; padding-top:15px;'>🏫 Trường: {school}</h4>", unsafe_allow_html=True)
            display_df = grouped.get_group(school).drop(columns=[col_truong] + cols_to_hide, errors='ignore')
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
        st.write("---")
        col_prev, col_text, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.session_state.current_page > 1:
                if st.button("⬅️ Trang trước"):
                    st.session_state.current_page -= 1
                    st.rerun()
        with col_text:
            st.markdown(f"<p style='text-align: center; font-size: 16px; font-weight: bold;'>Trang {st.session_state.current_page} / {total_pages}</p>", unsafe_allow_html=True)
        with col_next:
            if st.session_state.current_page < total_pages:
                if st.button("Trang sau ➡️"):
                    st.session_state.current_page += 1
                    st.rerun()
    else:
        st.warning("⚠️ Không có ngành học/trường nào thỏa mãn tiêu chí của bạn.")
else:
    st.info("💡 **Chào mừng bạn!** Hãy điều chỉnh BỘ LỌC ĐIỂM bên trái và bấm **[Áp dụng bộ lọc & Tìm kiếm]** để bắt đầu.")
