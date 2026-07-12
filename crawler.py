import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from urllib.parse import urljoin
from io import StringIO
from datetime import datetime

# Cấu hình
base_url = "https://diemthi.tuyensinh247.com"
main_url = f"{base_url}/diem-chuan.html"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_all_school_links(url):
    """Thu thập toàn bộ link chi tiết của các trường"""
    print(f"Đang kết nối đến trang chủ: {url}")
    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        school_links = []
        # Tìm tất cả thẻ a trong danh sách trường
        for a_tag in soup.select('div.list-schol-box ul li a'):
            href = a_tag.get('href')
            if href:
                full_link = urljoin(base_url, href)
                school_links.append(full_link)

        return list(set(school_links))  # loại bỏ trùng lặp
    except Exception as e:
        print(f"❌ Lỗi khi lấy danh sách trường: {e}")
        return []

def scrape_all_data(links):
    """Duyệt từng trường, lấy bảng điểm chuẩn"""
    all_dataframes = []
    total_schools = len(links)

    for i, link in enumerate(links):
        print(f"Đang xử lý ({i+1}/{total_schools}): {link}")

        try:
            response = requests.get(link, headers=headers)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            # Tìm bảng điểm chuẩn - thường là bảng có class 'table' hoặc id 'diemchuan'
            table = soup.find('table', {'id': 'diemchuan'})
            if table is None:
                # thử tìm bảng đầu tiên có chứa từ khóa
                table = soup.find('table')
            
            if table:
                df = pd.read_html(StringIO(str(table)))[0]
                df['Link_Nguồn'] = link
                # Tách mã trường từ URL
                ma_truong = link.split('/')[-1].split('-')[-1].replace('.html', '')
                df['Mã Trường'] = ma_truong.upper()
                df['Ngày cào'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                all_dataframes.append(df)
            else:
                print(f"⚠️ Không tìm thấy bảng dữ liệu ở: {link}")

        except Exception as e:
            print(f"❌ Lỗi khi đọc bảng ở {link}: {e}")

        # Nghỉ ngẫu nhiên để tránh bị chặn
        time.sleep(random.uniform(1.0, 2.5))

    if all_dataframes:
        final_df = pd.concat(all_dataframes, ignore_index=True)
        return final_df
    return None

if __name__ == "__main__":
    print("="*50)
    print("KHỞI CHẠY CÀO DỮ LIỆU ĐIỂM CHUẨN")
    print("="*50)

    links = get_all_school_links(main_url)

    if links:
        print(f"✅ Đã tìm thấy {len(links)} trường.")
        data = scrape_all_data(links)
        if data is not None:
            file_name = 'Tong_Hop_Diem_Chuan_Toan_Bo.xlsx'
            data.to_excel(file_name, index=False)
            print(f"\n✅ HOÀN THÀNH! Đã lưu vào {file_name}")
        else:
            print("❌ Không có dữ liệu để lưu.")
    else:
        print("❌ Không lấy được danh sách trường.")
