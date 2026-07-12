import streamlit as st
import pandas as pd
import os
import re

# 1. Cấu hình hiển thị Full màn hình rộng
st.set_page_config(layout="wide", page_title="Hệ Thống Lọc Điểm Chuẩn Đại Học", page_icon="🎓")

# 2. Tự động áp dụng giao diện Dark Mode & Purple Accent
custom_style = """
<style>
    .stApp {
        background-color: #1e1e2f; 
        color: #ffffff;
    }
    [data-testid="stSidebar"] {
        background-color: #27293d;
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        border-radius: 12px !important;
        background-color: #1e1e2f !important;
        color: white !important;
        border: 1px solid #4a4a6a !important;
    }
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #27293d;
        margin-bottom: 25px;
    }
    h1 {
        color: #8c54ff;
        font-weight: 700 !important;
    }
</style>
"""
st.markdown(custom_style, unsafe_allow_html=True)

# 3. Hàm tải và chuẩn hóa cấu trúc dữ liệu
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
            
    # --- TỰ ĐỘNG PHÂN LOẠI ĐẠI HỌC / CAO ĐẲNG ---
    def phan_loai_bac(row):
        link = str(row.get('Link_Nguồn', '')).lower()
        if 'cao-dang' in link:
            return 'Cao đẳng'
        return 'Đại học'
        
    df['Bậc Đào Tạo'] = df.apply(phan_loai_bac, axis=1)
    # ---------------------------------------------
            
    df[col_diem] = pd.to_numeric(df[col_diem], errors='coerce')
    return df, col_diem, col_khoi, col_truong, col_ma_nganh

# 4. Kiểm tra sự tồn tại của file dữ liệu
data_file = "Tong_Hop_Diem_Chuan_Toan_Bo.xlsx"

if not os.path.exists(data_file):
    st.title("🎓 HỆ THỐNG LỌC ĐIỂM CHUẨN ĐẠI HỌC")
    st.error(f"❌ Không tìm thấy file cơ sở dữ liệu: `{data_file}`")
    st.stop()

df, col_diem, col_khoi, col_truong, col_ma_nganh = load_and_prepare_data(data_file)

# 5. Thiết kế giao diện thanh điều khiển (Sidebar)
with st.sidebar:
    st.markdown("<h2 style='color:#8c54ff; text-align:center;'>⚙️ BỘ LỌC ĐIỂM</h2>", unsafe_allow_html=True)
    st.write("---")
    
    search_query = st.text_input("🔍 Tìm kiếm Trường (Tên/Mã):", placeholder="Ví dụ: BKA, Kinh tế...")
    search_ma_nganh = st.text_input("🆔 Tìm theo Mã Ngành (nếu có):", placeholder="Ví dụ: 7480201...")
    
    # --- BỘ LỌC BẬC ĐÀO TẠO MỚI ---
    bac_dao_tao = st.selectbox("🎓 Chọn Bậc đào tạo:", ["Tất cả", "Đại học", "Cao đẳng"])
    # ------------------------------
    
    # Bộ lọc Khối bằng Regex
    raw_khoi_list = df[col_khoi].dropna().astype(str).tolist()
    all_blocks = []
    for item in raw_khoi_list:
        matches = re.findall(r'\b[A-Z]\d{2}\b', item.upper())
        all_blocks.extend(matches)
    clean_khoi = sorted(list(set(all_blocks)))
    
    selected_khoi = st.selectbox("📚 Chọn Khối xét tuyển:", ["Tất cả"] + clean_khoi)
    
    diem_thi = st.slider("🎯 Điểm số của bạn (Bộ lọc sẽ hiển thị trường có điểm chuẩn <= điểm này):", 
                         min_value=0.0, max_value=40.0, value=25.0, step=0.25)

# 6. Tiến trình xử lý lọc dữ liệu
filtered_df = df.copy()

if search_query:
    filtered_df = filtered_df[filtered_df[col_truong].astype(str).str.contains(search_query, case=False, na=False)]

if search_ma_nganh and col_ma_nganh:
    filtered_df = filtered_df[filtered_df[col_ma_nganh].astype(str).str.contains(search_ma_nganh, na=False)]

if bac_dao_tao != "Tất cả":
    filtered_df = filtered_df[filtered_df['Bậc Đào Tạo'] == bac_dao_tao]

if selected_khoi != "Tất cả":
    filtered_df = filtered_df[filtered_df[col_khoi].astype(str).str.contains(selected_khoi, case=False, na=False)]

filtered_df = filtered_df[(filtered_df[col_diem] <= diem_thi) & (filtered_df[col_diem] > 0)]
filtered_df = filtered_df.sort_values(by=col_diem, ascending=False)

# 7. HIỂN THỊ DỮ LIỆU (MỖI TRƯỜNG 1 BẢNG)
st.title("🎓 HỆ THỐNG LỌC ĐIỂM CHUẨN")
st.markdown(f"Khối xét tuyển: **{selected_khoi}** | Điểm tối đa: **{diem_thi}** | Bậc: **{bac_dao_tao}**")
st.markdown(f"### 📊 Tìm thấy **{len(filtered_df)}** phương án phù hợp")
st.markdown("---")

if len(filtered_df) > 0:
    # Gom nhóm dữ liệu theo từng trường
    grouped = filtered_df.groupby(col_truong, sort=False)
    
    # Xác định các cột "rác" cần ẩn đi cho bảng đẹp (như Unnamed, Link, Cột dùng để lọc...)
    cols_to_hide = [c for c in filtered_df.columns if 'unnamed' in c.lower() or c in ['Link_Nguồn', 'Bậc Đào Tạo']]
    
    for school, group_data in grouped:
        # In Tên trường làm tiêu đề cho mỗi bảng
        st.markdown(f"<h4 style='color:#69b1ff; padding-top:15px;'>🏫 Trường: {school}</h4>", unsafe_allow_html=True)
        
        # Bỏ đi cột Tên trường và các cột rác khỏi bảng (vì tên trường đã ở tiêu đề rồi)
        display_df = group_data.drop(columns=[col_truong] + cols_to_hide, errors='ignore')
        
        # Hiển thị bảng
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
else:
    st.warning("⚠️ Không có ngành học/trường nào thỏa mãn tiêu chí của bạn. Thử tăng khoảng điểm hoặc chọn lại khối thi!")
