import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from urllib.parse import urljoin
from io import StringIO
from datetime import datetime

base_url = "https://diemthi.tuyensinh247.com"
main_url = f"{base_url}/diem-chuan.html"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_all_school_links(url):
    print(f"Đang kết nối đến trang chủ: {url}")
    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        school_links = []
        for a_tag in soup.select('div.list-schol-box ul li a'):
            href = a_tag.get('href')
            if href:
                full_link = urljoin(base_url, href)
                school_links.append(full_link)
        return list(set(school_links))
    except Exception as e:
        print(f"❌ Lỗi khi lấy danh sách trường: {e}")
        return []

def find_admission_table(soup):
    """
    Tìm bảng điểm chuẩn chính xác trong HTML.
    Ưu tiên bảng có class/id liên quan, hoặc chứa các từ khóa đặc trưng trong thẻ <th>.
    """
    # Tìm theo id hoặc class thường dùng
    table = soup.find('table', {'id': 'diemchuan'})
    if table:
        return table

    # Tìm tất cả bảng, kiểm tra bảng nào có header chứa từ "mã ngành", "điểm", "khối"
    all_tables = soup.find_all('table')
    for tbl in all_tables:
        headers = [th.get_text(strip=True).lower() for th in tbl.find_all('th')]
        if any('mã ngành' in h or 'điểm' in h or 'khối' in h or 'tổ hợp' in h for h in headers):
            return tbl
    # Nếu không có, trả về bảng đầu tiên
    return all_tables[0] if all_tables else None

def scrape_all_data(links):
    all_dataframes = []
    total = len(links)

    for i, link in enumerate(links):
        print(f"Đang xử lý ({i+1}/{total}): {link}")
        try:
            response = requests.get(link, headers=headers)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            table = find_admission_table(soup)
            if table is None:
                print(f"⚠️ Không tìm thấy bảng: {link}")
                continue

            df = pd.read_html(StringIO(str(table)))[0]

            # --- Đảm bảo có cột Mã ngành ---
            # Các tên cột có thể gặp: 'Mã ngành', 'Mã xét tuyển', 'Ngành', 'Mã ngành xét tuyển', ...
            ma_nganh_cols = [c for c in df.columns if 'mã' in c.lower() and ('ngành' in c.lower() or 'xét' in c.lower())]
            if not ma_nganh_cols:
                # Thử tìm cột chứa 'ngành' nhưng không phải 'tên ngành'
                possible = [c for c in df.columns if 'ngành' in c.lower() and 'tên' not in c.lower()]
                if not possible:
                    # Nếu không có, tạo cột Mã ngành trống
                    df['Mã ngành'] = ''
                else:
                    # Đổi tên cột đó thành 'Mã ngành'
                    df.rename(columns={possible[0]: 'Mã ngành'}, inplace=True)
            else:
                # Đảm bảo tên cột là 'Mã ngành'
                df.rename(columns={ma_nganh_cols[0]: 'Mã ngành'}, inplace=True)

            # Thêm thông tin nguồn
            df['Link_Nguồn'] = link
            ma_truong = link.split('/')[-1].split('-')[-1].replace('.html', '')
            df['Mã Trường'] = ma_truong.upper()
            df['Ngày cào'] = datetime.now().strftime("%Y-%m-%d %H:%M")

            all_dataframes.append(df)

        except Exception as e:
            print(f"❌ Lỗi ở {link}: {e}")

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
        print(f"✅ Tìm thấy {len(links)} trường.")
        data = scrape_all_data(links)
        if data is not None:
            data.to_excel("Tong_Hop_Diem_Chuan_Toan_Bo.xlsx", index=False)
            print("✅ Đã lưu Tong_Hop_Diem_Chuan_Toan_Bo.xlsx")
        else:
            print("❌ Không có dữ liệu.")
    else:
        print("❌ Không lấy được danh sách trường.")
