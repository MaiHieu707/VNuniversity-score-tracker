import streamlit as st
import pandas as pd
import os

# 1. Cấu hình hiển thị Full màn hình rộng (Wide layout)
st.set_page_config(layout="wide", page_title="Hệ Thống Lọc Điểm Chuẩn Đại Học", page_icon="🎓")

# 2. Tự động áp dụng giao diện Dark Mode & Purple Accent dựa trên UI mẫu
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
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid #27293d;
    }
    h1 {
        color: #8c54ff;
        font-weight: 700 !important;
    }
</style>
"""
st.markdown(custom_style, unsafe_allow_html=True)

# 3. Hàm tải và chuẩn hóa cấu trúc dữ liệu linh hoạt
@st.cache_data
def load_and_prepare_data(file_path):
    df = pd.read_excel(file_path)
    
    # Định dạng tự động tìm tên các cột bất kể tiêu đề đặt ra sao
    col_diem = [c for c in df.columns if 'điểm' in c.lower() or 'score' in c.lower()][0]
    col_khoi = [c for c in df.columns if 'khối' in c.lower() or 'tổ hợp' in c.lower()][0]
    
    # Kiểm tra cột mã ngành
    ma_nganh_cols = [c for c in df.columns if 'mã ngành' in c.lower() or 'mã xét tuyển' in c.lower()]
    col_ma_nganh = ma_nganh_cols[0] if ma_nganh_cols else None
    
    # Kiểm tra hoặc tự tạo cột Mã Trường/Tên Trường để sửa lỗi IndexError
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
            
    # Ép dữ liệu cột điểm chuẩn về dạng số (float)
    df[col_diem] = pd.to_numeric(df[col_diem], errors='coerce')
    return df, col_diem, col_khoi, col_truong, col_ma_nganh

# 4. Kiểm tra sự tồn tại của file dữ liệu cơ sở trước khi chạy App
data_file = "Tong_Hop_Diem_Chuan_Toan_Bo.xlsx"

if not os.path.exists(data_file):
    st.title("🎓 HỆ THỐNG LỌC ĐIỂM CHUẨN ĐẠI HỌC")
    st.error(f"❌ Không tìm thấy file cơ sở dữ liệu: `{data_file}`")
    st.info("💡 Hướng dẫn: Bạn cần chạy file `crawler.py` trước dưới máy để sinh ra file dữ liệu Excel này, sau đó ứng dụng Web mới có thể hoạt động.")
    st.stop()

# Đọc dữ liệu đầu vào
df, col_diem, col_khoi, col_truong, col_ma_nganh = load_and_prepare_data(data_file)

# 5. Thiết kế giao diện thanh điều khiển (Sidebar bên trái)
with st.sidebar:
    st.markdown("<h2 style='color:#8c54ff; text-align:center;'>⚙️ BỘ LỌC ĐIỂM</h2>", unsafe_allow_html=True)
    st.write("---")
    
    # Bộ lọc 1: Tìm kiếm theo tên hoặc mã trường học
    search_query = st.text_input("🔍 Tìm kiếm Trường (Tên hoặc Mã trường):", placeholder="Ví dụ: BKA, Kinh tế...")
    
    # Bộ lọc 2: Tìm kiếm theo mã ngành cụ thể
    search_ma_nganh = st.text_input("🆔 Tìm theo Mã Ngành (nếu có):", placeholder="Ví dụ: 7480201...")
    
    # Bộ lọc 3: Tự động bóc tách danh sách các khối thi duy nhất
    raw_khoi_list = df[col_khoi].dropna().astype(str).tolist()
    clean_khoi = sorted(list(set([k.strip() for items in raw_khoi_list for k in items.split(',')])))
    selected_khoi = st.selectbox("📚 Chọn Khối xét tuyển:", ["Tất cả"] + clean_khoi)
    
    # Bộ lọc 4: Thanh kéo chọn điểm thi thực tế của thí sinh
    diem_thi = st.slider("🎯 Điểm số của bạn (Bộ lọc sẽ hiển thị trường có điểm chuẩn <= điểm này):", 
                         min_value=0.0, max_value=30.0, value=25.0, step=0.25)
    
    st.write("---")
    st.caption("Dự án hỗ trợ chọn nguyện vọng Đại Học 🚀")

# 6. Tiến trình xử lý lọc dữ liệu thông minh (Real-time Filtering)
filtered_df = df.copy()

if search_query:
    filtered_df = filtered_df[filtered_df[col_truong].astype(str).str.contains(search_query, case=False, na=False)]

if search_ma_nganh and col_ma_nganh:
    filtered_df = filtered_df[filtered_df[col_ma_nganh].astype(str).str.contains(search_ma_nganh, na=False)]

if selected_khoi != "Tất cả":
    filtered_df = filtered_df[filtered_df[col_khoi].astype(str).str.contains(selected_khoi, case=False, na=False)]

# Loại bỏ các hàng không có điểm hoặc điểm lỗi bằng 0
filtered_df = filtered_df[(filtered_df[col_diem] <= diem_thi) & (filtered_df[col_diem] > 0)]

# Sắp xếp danh sách trả về từ cao xuống thấp
filtered_df = filtered_df.sort_values(by=col_diem, ascending=False)

# 7. Hiển thị dữ liệu lên khu vực chính (Main board bên phải)
st.title("🎓 HỆ THỐNG LỌC ĐIỂM CHUẨN ĐẠI HỌC")
st.markdown(f"Đang hiển thị danh sách các ngành phù hợp cho Khối xét tuyển: **{selected_khoi}** với mức điểm số tối đa là **{diem_thi}**")

st.markdown(f"### 📊 Tìm thấy **{len(filtered_df)}** phương án phù hợp")

# Đổ bảng dữ liệu căng full toàn bộ kích thước màn hình máy tính
st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True
)
