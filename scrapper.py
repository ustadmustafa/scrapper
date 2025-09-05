import requests
from bs4 import BeautifulSoup
import re
import time
import pandas as pd
import json

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

def get_omdb_data(title, api_key="3f924d91"):
    """
    OMDB API'sinden film/dizi bilgilerini çeker
    """
    # Boşlukları alt çizgi ile değiştir
    search_title = title.replace(' ', '_')
    
    url = f"https://www.omdbapi.com/?t={search_title}&apikey={api_key}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('Response') == 'True':
            return data
        else:
            print(f"OMDB'de bulunamadı: {title}")
            return None
            
    except requests.RequestException as e:
        print(f"OMDB API hatası ({title}): {e}")
        return None
    except Exception as e:
        print(f"Genel hata ({title}): {e}")
        return None

def parse_genres(genre_string):
    """
    Genre string'ini Genre1, Genre2, Genre3 şeklinde ayırır
    """
    if not genre_string or genre_string == "N/A":
        return {"Genre1": "", "Genre2": "", "Genre3": ""}
    
    genres = [g.strip() for g in genre_string.split(',')]
    
    result = {"Genre1": "", "Genre2": "", "Genre3": ""}
    
    for i, genre in enumerate(genres[:3]):  # Maksimum 3 genre
        result[f"Genre{i+1}"] = genre
    
    return result

def enhance_movies_with_omdb_data(movies_series):
    """
    Film/dizi listesini OMDB verileri ile zenginleştirir
    """
    enhanced_data = []
    
    for i, item in enumerate(movies_series):
        print(f"\nOMDB'de aranıyor ({i+1}/{len(movies_series)}): {item['name']}")
        
        # OMDB'den veri çek
        omdb_data = get_omdb_data(item['name'])
        
        if omdb_data:
            # Genre'leri ayır
            genres = parse_genres(omdb_data.get('Genre', ''))
            
            # Zenginleştirilmiş veri oluştur
            enhanced_item = {
                'Type': item['type'],
                'Title': omdb_data.get('Title', item['name']),
                'Year': omdb_data.get('Year', ''),
                'Rated': omdb_data.get('Rated', ''),
                'Released': omdb_data.get('Released', ''),
                'Runtime': omdb_data.get('Runtime', ''),
                'Genre1': genres['Genre1'],
                'Genre2': genres['Genre2'],
                'Genre3': genres['Genre3'],
                'Director': omdb_data.get('Director', ''),
                'Writer': omdb_data.get('Writer', ''),
                'Actors': omdb_data.get('Actors', ''),
                'Plot': omdb_data.get('Plot', ''),
                'Language': omdb_data.get('Language', ''),
                'Country': omdb_data.get('Country', ''),
                'Awards': omdb_data.get('Awards', ''),
                'IMDB_Rating': omdb_data.get('imdbRating', ''),
                'IMDB_Votes': omdb_data.get('imdbVotes', ''),
                'IMDB_ID': omdb_data.get('imdbID', ''),
                'Metascore': omdb_data.get('Metascore', ''),
                'Poster': omdb_data.get('Poster', ''),
                'Original_Text': item['original_text']
            }
            
            print(f"✓ Bulundu: {enhanced_item['Title']} ({enhanced_item['Year']})")
            print(f"  Genre: {enhanced_item['Genre1']}, {enhanced_item['Genre2']}, {enhanced_item['Genre3']}")
            print(f"  IMDB Rating: {enhanced_item['IMDB_Rating']}")
            
        else:
            # OMDB'de bulunamadı, orijinal veriyi kullan
            enhanced_item = {
                'Type': item['type'],
                'Title': item['name'],
                'Year': '',
                'Rated': '',
                'Released': '',
                'Runtime': '',
                'Genre1': '',
                'Genre2': '',
                'Genre3': '',
                'Director': '',
                'Writer': '',
                'Actors': '',
                'Plot': '',
                'Language': '',
                'Country': '',
                'Awards': '',
                'IMDB_Rating': '',
                'IMDB_Votes': '',
                'IMDB_ID': '',
                'Metascore': '',
                'Poster': '',
                'Original_Text': item['original_text']
            }
            print(f"✗ Bulunamadı: {item['name']}")
        
        enhanced_data.append(enhanced_item)
        
        # API rate limiting için kısa bekleme
        time.sleep(0.5)
    
    return enhanced_data

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
        
        print("\n" + "="*60)
        print("OMDB API'sinden detaylı bilgiler çekiliyor...")
        print("="*60)
        
        # OMDB verileri ile zenginleştir
        enhanced_data = enhance_movies_with_omdb_data(movies_series)
        
        # DataFrame oluştur
        df = pd.DataFrame(enhanced_data)
        
        # Excel'e kaydet
        excel_filename = "doostihaa_movies_series_enhanced.xlsx"
        df.to_excel(excel_filename, index=False)
        print(f"\n" + "="*60)
        print(f"Sonuçlar {excel_filename} dosyasına kaydedildi.")
        print("="*60)
        
        # Özet istatistikler
        found_count = len([item for item in enhanced_data if item['IMDB_Rating'] != ''])
        not_found_count = len(enhanced_data) - found_count
        
        print(f"\nÖzet:")
        print(f"Toplam film/dizi: {len(enhanced_data)}")
        print(f"OMDB'de bulunan: {found_count}")
        print(f"Bulunamayan: {not_found_count}")
        
    else:
        print("Hiç film/dizi bulunamadı.")

if __name__ == "__main__":
    main()
