import streamlit as st
import pandas as pd
import os

# 1. Cấu hình hiển thị Full màn hình rộng (Wide layout)
st.set_page_config(layout="wide", page_title="Hệ Thống Lọc Điểm Chuẩn Đại Học", page_icon="🎓")

# 2. Tự động áp dụng giao diện Dark Mode & Purple Accent dựa trên UI mẫu
custom_style = """
<style>
    /* Nền toàn bộ trang web */
    .stApp {
        background-color: #1e1e2f; 
        color: #ffffff;
    }
    
    /* Giao diện thanh công cụ bên trái */
    [data-testid="stSidebar"] {
        background-color: #27293d;
    }

    /* Tùy chỉnh các khối nhập liệu text input, selectbox */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        border-radius: 12px !important;
        background-color: #1e1e2f !important;
        color: white !important;
        border: 1px solid #4a4a6a !important;
    }
    
    /* Tùy chỉnh thanh trượt Slider màu tím */
    div[data-baseline="slider"] {
        color: #8c54ff;
    }

    /* Định dạng bảng dữ liệu hiển thị */
    [data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid #27293d;
    }
    
    /* Tiêu đề chính */
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
    
    # Định dạng tự động tìm tên các cột bất kể trang web đặt tiêu đề tiếng Việt ra sao
    col_diem = [c for c in df.columns if 'điểm' in c.lower() or 'score' in c.lower()][0]
    col_khoi = [c for c in df.columns if 'khối' in c.lower() or 'tổ hợp' in c.lower()][0]
    col_truong = [c for c in df.columns if 'trường' in c.lower() or 'school' in c.lower()][0]
    
    # Ép dữ liệu cột điểm chuẩn về dạng số (float) để thực hiện tính toán so sánh số học
    df[col_diem] = pd.to_numeric(df[col_diem], errors='coerce')
    return df, col_diem, col_khoi, col_truong

# 4. Kiểm tra sự tồn tại của file dữ liệu cơ sở trước khi chạy App
data_file = "Tong_Hop_Diem_Chuan_Toan_Bo.xlsx"

if not os.path.exists(data_file):
    st.title("🎓 HỆ THỐNG LỌC ĐIỂM CHUẨN ĐẠI HỌC")
    st.error(f"❌ Không tìm thấy file cơ sở dữ liệu: `{data_file}`")
    st.info("💡 Hướng dẫn: Bạn cần chạy file `crawler.py` trước để sinh ra file dữ liệu Excel này, sau đó ứng dụng Web mới có thể hoạt động.")
    st.stop()

# Đọc dữ liệu đầu vào
df, col_diem, col_khoi, col_truong = load_and_prepare_data(data_file)

# 5. Thiết kế giao diện thanh điều khiển (Sidebar bên trái)
with st.sidebar:
    st.markdown("<h2 style='color:#8c54ff; text-align:center;'>⚙️ BỘ LỌC ĐIỂM</h2>", unsafe_allow_html=True)
    st.write("---")
    
    # Bộ lọc 1: Tìm kiếm theo tên trường học
    search_query = st.text_input("🔍 Tên trường cần tìm kiếm:", placeholder="Nhập từ khóa...")
    
    # Bộ lọc 2: Tự động bóc tách danh sách các khối thi duy nhất từ hệ thống dữ liệu
    raw_khoi_list = df[col_khoi].dropna().astype(str).tolist()
    clean_khoi = sorted(list(set([k.strip() for items in raw_khoi_list for k in items.split(',')])))
    selected_khoi = st.selectbox("📚 Chọn Khối xét tuyển:", ["Tất cả"] + clean_khoi)
    
    # Bộ lọc 3: Thanh kéo chọn điểm thi thực tế của thí sinh
    diem_thi = st.slider("🎯 Điểm số của bạn (Bộ lọc sẽ hiển thị trường có điểm chuẩn <= điểm này):", 
                         min_value=0.0, max_value=30.0, value=25.0, step=0.25)
    
    st.write("---")
    st.caption("Dự án hỗ trợ chọn nguyện vọng Đại Học 🚀")

# 6. Tiến trình xử lý lọc dữ liệu thông minh (Real-time Filtering)
filtered_df = df.copy()

if search_query:
    filtered_df = filtered_df[filtered_df[col_truong].str.contains(search_query, case=False, na=False)]

if selected_khoi != "Tất cả":
    filtered_df = filtered_df[filtered_df[col_khoi].str.contains(selected_khoi, case=False, na=False)]

# Lọc điểm chuẩn nhỏ hơn hoặc bằng điểm thi thực tế và loại các dòng lỗi điểm âm/bằng không
filtered_df = filtered_df[(filtered_df[col_diem] <= diem_thi) & (filtered_df[col_diem] > 0)]

# Sắp xếp danh sách trả về từ cao xuống thấp để phân cấp nguyện vọng tối ưu
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