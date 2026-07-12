import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from urllib.parse import urljoin
from io import StringIO

# Cấu hình hệ thống
base_url = "https://diemthi.tuyensinh247.com"
main_url = f"{base_url}/diem-chuan.html"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_all_school_links(url):
    """BƯỚC 1: Thu thập toàn bộ link chi tiết của tất cả các trường"""
    print(f"Đang kết nối đến trang chủ: {url}")
    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        school_links = []
        danh_sach_the_a = soup.select('div.list-schol-box ul li a') 
        
        for a_tag in danh_sach_the_a:
            href = a_tag.get('href')
            if href:
                full_link = urljoin(base_url, href)
                school_links.append(full_link)
                
        return list(set(school_links))
    except Exception as e:
        print(f"❌ Lỗi khi lấy danh sách trường: {e}")
        return []

def scrape_all_data(links):
    """BƯỚC 2: Duyệt qua danh sách trường để lấy bảng dữ liệu điểm chuẩn"""
    all_dataframes = []
    total_schools = len(links)
    
    for i, link in enumerate(links): 
        print(f"Đang tiến hành cào ({i+1}/{total_schools}): {link}")
        
        try:
            response = requests.get(link, headers=headers)
            response.encoding = 'utf-8'
            
            # Sử dụng StringIO để xử lý lỗi nhận nhầm chuỗi HTML thành đường dẫn file của Pandas
            html_data = StringIO(response.text)
            tables = pd.read_html(html_data)
            
            if tables:
                df_truong = tables[0] 
                df_truong['Link_Nguồn'] = link 
                
                # Tự động bóc tách Mã Trường từ đường link URL
                ma_truong = link.split('/')[-1].split('-')[-1].replace('.html', '')
                df_truong['Mã Trường'] = ma_truong.upper()
                
                all_dataframes.append(df_truong)
            else:
                print(f"⚠️ Không tìm thấy bảng dữ liệu ở trang: {link}")
                
        except Exception as e:
            print(f"❌ Lỗi khi đọc bảng ở trang {link}: {e}")
            
        # Cơ chế chống chặn IP (Anti-block): Nghỉ ngơi ngẫu nhiên từ 1 đến 2.5 giây
        time.sleep(random.uniform(1.0, 2.5)) 

    if all_dataframes:
        final_df = pd.concat(all_dataframes, ignore_index=True)
        return final_df
    return None

if __name__ == "__main__":
    print("========================================")
    print("KHỞI CHẠY TIẾN TRÌNH CÀO DỮ LIỆU ĐIỂM CHUẨN")
    print("========================================")

    links = get_all_school_links(main_url)

    if links:
        print(f"-> Thành công! Đã tìm thấy {len(links)} trường học.")
        print("-> Bắt đầu tiến hành thu thập toàn bộ dữ liệu...")
        
        data_raw = scrape_all_data(links)
        
        if data_raw is not None:
            file_name = 'Tong_Hop_Diem_Chuan_Toan_Bo.xlsx'
            data_raw.to_excel(file_name, index=False)
            print(f"\n✅ HOÀN THÀNH TOÀN BỘ TIẾN TRÌNH!")
            print(f"👉 Đã lưu file cơ sở dữ liệu gốc: {file_name}")
    else:
        print("❌ Thất bại. Không kết nối lấy được danh sách link từ trang chủ.")
