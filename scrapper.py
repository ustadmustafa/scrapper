import requests
from bs4 import BeautifulSoup
import re
import time
import pandas as pd

def extract_movie_series_names(url):
    """
    Doostihaa.com sitesinden film ve dizi isimlerini çeker
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        print(f"Siteye bağlanılıyor: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        print(f"HTTP Durum Kodu: {response.status_code}")
        
        if response.status_code == 200:
            print("Site başarıyla yüklendi!")
        else:
            print(f"Site yüklenemedi. Durum kodu: {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # HTML içeriğini dosyaya kaydet (debug için)
        with open('debug_html.html', 'w', encoding='utf-8') as f:
            f.write(str(soup.prettify()))
        print("HTML içeriği debug_html.html dosyasına kaydedildi")
        
        # Tüm div elementlerini kontrol et
        all_divs = soup.find_all('div')
        print(f"Toplam {len(all_divs)} div elementi bulundu")
        
        # Tüm span elementlerini kontrol et
        all_spans = soup.find_all('span')
        print(f"Toplam {len(all_spans)} span elementi bulundu")
        
        # Önce tüm article elementlerini bul
        all_articles = soup.find_all('article')
        print(f"Toplam {len(all_articles)} article elementi bulundu")
        
        # postsd class'ına sahip article elementlerini bul
        articles = soup.find_all('article', class_='postsd')
        print(f"postsd class'ına sahip {len(articles)} article bulundu")
        
        # Eğer postsd class'ı bulunamazsa, tüm article'ları kontrol et
        if len(articles) == 0:
            print("postsd class'ı bulunamadı, tüm article'ları kontrol ediliyor...")
            articles = all_articles
            
        # Eğer hiç article yoksa, div'leri kontrol et
        if len(articles) == 0:
            print("Hiç article bulunamadı, div'leri kontrol ediliyor...")
            # textkian0 class'ına sahip div'leri bul
            text_divs = soup.find_all('div', class_='textkian0')
            print(f"textkian0 class'ına sahip {len(text_divs)} div bulundu")
            
            if len(text_divs) > 0:
                articles = text_divs
            else:
                # Herhangi bir div'i article olarak kabul et
                articles = all_divs[:10]  # İlk 10 div'i kontrol et
        
        movies_series = []
        
        for i, article in enumerate(articles):
            print(f"\n--- Article {i+1} ---")
            print(f"Article class: {article.get('class', 'No class')}")
            
            # textkian0 class'ına sahip div'i bul
            text_div = article.find('div', class_='textkian0')
            if not text_div:
                # Alternatif div arama
                text_div = article.find('div', class_=lambda x: x and 'text' in x.lower())
                if not text_div:
                    # Herhangi bir div bul
                    text_div = article.find('div')
            
            if text_div:
                print(f"Div bulundu: {text_div.get('class', 'No class')}")
                
                # Mavi renkli span'i bul
                span = text_div.find('span', style='color: #0000ff;')
                if not span:
                    # Alternatif span arama
                    span = text_div.find('span', style=lambda x: x and '#0000ff' in x)
                    if not span:
                        # Herhangi bir span bul
                        span = text_div.find('span')
                
                if span:
                    text = span.get_text(strip=True)
                    print(f"Span metni: {text}")
                    
                    # Dizi kontrolü - "Episode" kelimesi var mı?
                    if 'Episode' in text:
                        # Dizi ismini çıkar - "Episode" kelimesinden önceki kısım
                        episode_index = text.find('Episode')
                        if episode_index != -1:
                            series_name = text[:episode_index].strip()
                            # Farsça karakterleri temizle ve sadece İngilizce kısmı al
                            series_name = clean_series_name(series_name)
                            if series_name:
                                movies_series.append({
                                    'type': 'Series',
                                    'name': series_name,
                                    'original_text': text
                                })
                                print(f"✓ Dizi bulundu: {series_name}")
                    
                    # Film kontrolü - yıl kontrolü (2025, 2024, 2023, vb.)
                    elif re.search(r'\b(19|20)\d{2}\b', text):
                        # Yıldan önceki kısmı al
                        year_match = re.search(r'\b(19|20)\d{2}\b', text)
                        if year_match:
                            year_index = year_match.start()
                            movie_name = text[:year_index].strip()
                            # Farsça karakterleri temizle
                            movie_name = clean_movie_name(movie_name)
                            if movie_name:
                                movies_series.append({
                                    'type': 'Movie',
                                    'name': movie_name,
                                    'original_text': text
                                })
                                print(f"✓ Film bulundu: {movie_name}")
                else:
                    print("Span bulunamadı")
            else:
                print("Div bulunamadı")
        
        return movies_series
        
    except requests.RequestException as e:
        print(f"HTTP hatası: {e}")
        return []
    except Exception as e:
        print(f"Genel hata: {e}")
        return []

def clean_series_name(name):
    """
    Dizi ismini temizler - Farsça karakterleri kaldırır
    """
    # Farsça karakterleri kaldır ve sadece İngilizce kısmı al
    # "دانلود قسمت هشتم سریال سووشون ‏Savushun" -> "Savushun"
    parts = name.split()
    english_parts = []
    
    for part in parts:
        # Sadece İngilizce karakterler içeren kısımları al
        if re.match(r'^[a-zA-Z\s]+$', part):
            english_parts.append(part)
    
    return ' '.join(english_parts).strip()

def clean_movie_name(name):
    """
    Film ismini temizler - Farsça karakterleri kaldırır
    """
    # "دانلود و تماشای سریال دود با دوبله فارسی Smoke" -> "Smoke"
    parts = name.split()
    english_parts = []
    
    for part in parts:
        # Sadece İngilizce karakterler içeren kısımları al
        if re.match(r'^[a-zA-Z\s]+$', part):
            english_parts.append(part)
    
    return ' '.join(english_parts).strip()

def main():
    url = "https://www.doostihaa.com/page/1"
    
    print("Doostihaa.com sitesinden film ve dizi isimleri çekiliyor...")
    print(f"URL: {url}")
    print("-" * 50)
    
    movies_series = extract_movie_series_names(url)
    
    if movies_series:
        print(f"\nToplam {len(movies_series)} film/dizi bulundu:")
        print("-" * 50)
        
        for item in movies_series:
            print(f"Tür: {item['type']}")
            print(f"İsim: {item['name']}")
            print(f"Orijinal metin: {item['original_text']}")
            print("-" * 30)
        
        # DataFrame oluştur
        df = pd.DataFrame(movies_series)
        
        # Excel'e kaydet
        excel_filename = "doostihaa_movies_series.xlsx"
        df.to_excel(excel_filename, index=False)
        print(f"\nSonuçlar {excel_filename} dosyasına kaydedildi.")
        
    else:
        print("Hiç film/dizi bulunamadı.")

if __name__ == "__main__":
    main()
