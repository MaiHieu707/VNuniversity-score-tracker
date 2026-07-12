import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from urllib.parse import urljoin
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

def parse_table_to_df(soup):
    """
    Tìm bảng điểm chuẩn và trả về DataFrame với các cột chuẩn:
    STT, Mã ngành, Tên ngành, Tổ hợp môn, Điểm chuẩn, Ghi chú
    """
    # Tìm table chứa điểm chuẩn (ưu tiên table có id/class liên quan)
    table = soup.find('table', {'id': 'diemchuan'})
    if not table:
        tables = soup.find_all('table')
        # Chọn bảng đầu tiên có chứa từ khóa "Mã ngành" hoặc "Tổ hợp môn"
        for tbl in tables:
            if 'Mã ngành' in tbl.get_text() or 'Tổ hợp môn' in tbl.get_text():
                table = tbl
                break
        else:
            table = tables[0] if tables else None

    if not table:
        return None

    rows = table.find_all('tr')
    header_row_idx = None
    # Tìm dòng tiêu đề thực sự (có thẻ <th> chứa "Mã ngành")
    for i, row in enumerate(rows):
        ths = row.find_all('th')
        if ths:
            th_texts = [th.get_text(strip=True) for th in ths]
            if any('Mã ngành' in t for t in th_texts):
                header_row_idx = i
                break

    if header_row_idx is None:
        # Nếu không tìm thấy, dùng dòng đầu tiên có thẻ <th>
        for i, row in enumerate(rows):
            if row.find_all('th'):
                header_row_idx = i
                break

    if header_row_idx is None:
        # Không có dòng tiêu đề → bỏ qua
        return None

    # Lấy nội dung tiêu đề
    header_row = rows[header_row_idx]
    columns = [th.get_text(strip=True) for th in header_row.find_all('th')]
    # Chuẩn hóa tên cột: loại bỏ dấu cách thừa, thay thế nếu cần
    columns = [col.replace('\n', ' ').strip() for col in columns]

    # Lấy dữ liệu từ các dòng sau tiêu đề
    data_rows = rows[header_row_idx + 1:]
    data = []
    for row in data_rows:
        cells = row.find_all(['td', 'th'])
        if not cells:
            continue
        row_data = [cell.get_text(strip=True) for cell in cells]
        # Bỏ qua dòng chỉ chứa quảng cáo (dòng "Tra cứu tại...")
        if len(row_data) > 0 and 'Tra cứu tại' in row_data[0]:
            continue
        data.append(row_data)

    # Đảm bảo các hàng có cùng số cột như tiêu đề (nếu thiếu thì thêm rỗng)
    max_cols = len(columns)
    clean_data = []
    for row in data:
        if len(row) < max_cols:
            row += [''] * (max_cols - len(row))
        elif len(row) > max_cols:
            row = row[:max_cols]
        clean_data.append(row)

    df = pd.DataFrame(clean_data, columns=columns)

    # Đổi tên cột cho đồng bộ (nếu cần)
    rename_map = {}
    for col in df.columns:
        low = col.lower()
        if 'mã ngành' in low:
            rename_map[col] = 'Mã ngành'
        elif 'tên ngành' in low or low == 'ngành':
            rename_map[col] = 'Tên ngành'
        elif 'tổ hợp' in low or 'khối' in low:
            rename_map[col] = 'Tổ hợp môn'
        elif 'điểm' in low:
            rename_map[col] = 'Điểm chuẩn'
        elif 'ghi chú' in low:
            rename_map[col] = 'Ghi chú'
        elif 'stt' in low:
            rename_map[col] = 'STT'
    if rename_map:
        df.rename(columns=rename_map, inplace=True)

    # Loại bỏ cột STT nếu có
    if 'STT' in df.columns:
        df.drop(columns=['STT'], inplace=True)

    return df

def scrape_all_data(links):
    all_dataframes = []
    total = len(links)

    for i, link in enumerate(links):
        print(f"Đang xử lý ({i+1}/{total}): {link}")
        try:
            response = requests.get(link, headers=headers)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            df = parse_table_to_df(soup)
            if df is None or df.empty:
                print(f"⚠️ Không lấy được bảng: {link}")
                continue

            # Thêm thông tin nguồn và mã trường
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
