# Hammadde Takip

Plastik film üretiminde kullanılan hammaddelerin stok girişi, silo/depolama seviye takibi, mikser formülüne göre parti bazlı tüketim hesabı ve günlük raporlama ihtiyaçlarını karşılayan bir **Python Flask** web uygulaması.

## 🏭 Özellikler

- **Dashboard:** Silo/tank doluluk seviyeleri, bigbag stoku, günlük üretim özeti
- **Hammadde Giriş:** Tanker, Bigbag, IBC/Varil girişleri
- **Formül Yönetimi:** Çoklu formül oluşturma, düzenleme, kopyalama
- **Üretim (Parti Kayıt):** Formüle göre otomatik stok düşümü, toplu parti üretimi, stok kontrolü
- **Geri Dönüşüm:** Kırma tankı (B-kalite) ve pellet tankı (şerit kepek) takibi
- **Raporlama:** Günlük/tarihsel tüketim raporu, CSV dışa aktarma
- **Ayarlar:** Silo kapasiteleri, kırma akış hızı, stok düzeltme, veritabanı yedekleme/geri yükleme

**Geri Dönüşüm Tankları:** Kırma Tankı + Pellet Tankı

## 🚀 Kurulum

### Gereksinimler
- Python 3.10+

### Adımlar

```bash
# Repo'yu klonla
git clone https://github.com/aoyilmaz/hammadde-takip.git
cd hammadde-takip

# Sanal ortam oluştur
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Bağımlılıkları yükle
pip install -r requirements.txt

# Uygulamayı başlat
python app.py
```

Tarayıcıda **http://127.0.0.1:5000** adresini açın.

## 🛠️ Teknolojiler

| Katman | Teknoloji |
|--------|-----------|
| Backend | Python 3 + Flask |
| Veritabanı | SQLite |
| ORM | Flask-SQLAlchemy |
| Frontend | HTML + CSS + Vanilla JS |
| Font | Google Fonts (Inter) |

## 📁 Proje Yapısı

```
hammadde-takip/
├── app.py                  # Flask ana uygulama
├── config.py               # Konfigürasyon
├── models.py               # Veritabanı modelleri
├── requirements.txt        # Python bağımlılıkları
├── routes/                 # Route modülleri
│   ├── dashboard.py
│   ├── hammadde.py
│   ├── formul.py
│   ├── uretim.py
│   ├── geri_donus.py
│   ├── rapor.py
│   └── ayarlar.py
├── templates/              # Jinja2 HTML şablonları
│   ├── base.html
│   ├── dashboard.html
│   ├── hammadde_giris.html
│   ├── formul.html
│   ├── uretim.html
│   ├── geri_donus.html
│   ├── rapor.html
│   └── ayarlar.html
└── static/
    ├── css/style.css       # Koyu tema stil dosyası
    └── js/app.js           # Frontend JavaScript
```

## 📄 Lisans

MIT
