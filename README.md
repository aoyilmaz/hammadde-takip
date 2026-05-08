# Hammadde Takip

Plastik film üretiminde kullanılan hammaddelerin stok girişi, silo/depolama seviye takibi, mikser formülüne göre parti bazlı tüketim hesabı ve günlük raporlama ihtiyaçlarını karşılayan bir **Python Flask** web uygulaması.

## 🏭 Özellikler

- **Dashboard:** Silo/tank doluluk seviyeleri, bigbag stoku, günlük üretim özeti ve tahmini stok bitiş süreleri.
- **Tanımlar:** Hammadde kartları, tedarikçi yönetimi ve silo tanımları. Bir tedarikçiye birden fazla hammadde tipi/kodu atanabilir.
- **Hammadde Giriş:** Tanker (dökme), Bigbag, IBC/Varil girişleri. Kantar fişine göre **Net Giriş Miktarı** manuel olarak düzenlenebilir.
- **Formül Yönetimi:** Çoklu formül oluşturma, düzenleme, kopyalama ve snapshot bazlı geçmiş takibi.
- **Üretim (Parti Kayıt):** Formüle göre otomatik stok düşümü, toplu parti üretimi ve FIFO lot takibi.
- **Geri Dönüşüm:** Kırma tankı (B-kalite) ve pellet tankı (şerit kepek) seviye takibi.
- **Raporlama:** Günlük/tarihsel tüketim raporu, CSV dışa aktarma.
- **Ayarlar:** Sistem parametreleri (akış hızı, haftalık hedef), veritabanı yedekleme ve geri yükleme.

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

Tarayıcıda **http://127.0.0.1:5001** adresini açın.

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
├── app.py                  # Flask ana uygulama (Port: 5001)
├── config.py               # Konfigürasyon
├── models.py               # Veritabanı modelleri
├── requirements.txt        # Python bağımlılıkları
├── routes/                 # Route modülleri (dashboard, hammadde, formul, vb.)
├── templates/              # Jinja2 HTML şablonları
└── static/                 # CSS ve JS dosyaları
```

## 📄 Lisans

MIT
