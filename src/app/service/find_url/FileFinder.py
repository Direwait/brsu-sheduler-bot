import re
import requests
from requests import RequestException


def find_excel_files_from_page(page_url:str) -> list:
    base_domain = "https://www.brsu.by"
    excel_urls = []
    """https://www.brsu.by/filologicheskij-fakultet"""
    try:
        print(f"Парсим страницу: {page_url}")
        response = requests.get(page_url, timeout=10)

        if response.status_code == 200:
            # Ищем все ссылки на Excel файлы
            excel_pattern = r'href="([^"]*\.xls[x]?[^"]*)"'
            excel_links = re.findall(excel_pattern, response.text, re.IGNORECASE)

            print(f"Найдено ссылок с Excel: {len(excel_links)}")

            for link in excel_links:
                full_url = base_domain + link
                try:
                    file_response = requests.head(full_url, timeout=5)
                    if file_response.status_code == 200:
                        excel_urls.append(full_url)
                    else:
                        print(f"✗ Файл недоступен: {full_url}")
                except RequestException:
                    print(f"✗ Ошибка проверки: {full_url}")
        else:
            print(f"Ошибка доступа к странице: {response.status_code}")

    except RequestException as e:
        print(f"✗ Ошибка при парсинге страницы: {e}")

    return excel_urls

def newest_files(page_url) -> tuple:
    try:
        excel_files = find_excel_files_from_page(page_url)

        if excel_files:
            print(f"\n🎯 Найдено Excel файлов: {len(excel_files)}")

            newest_file = excel_files[0]
            print(f"\n📎 Самый новый файл: {newest_file}")

            # Предпоследний новый - второй в списке
            second_newest_file = None
            if len(excel_files) >= 2:
                second_newest_file = excel_files[1]
                print(f"📎 Предпоследний новый файл: {second_newest_file}")
            else:
                print("📎 Предпоследний файл: не найден")

            return newest_file, second_newest_file
        else:
            print("❌ Excel файлы не найдены на странице")
            return None, None

    except Exception as e:
        print(f"Общая ошибка: {e}")
        return None, None