"""
Silo Takip — PVC Streç Üretim Hattı Hammadde Takip Sistemi.
Ana Flask uygulama dosyası. Veritabanı başlatma ve seed verilerini içerir.
"""
import os
from datetime import datetime
from flask import Flask
from config import Config
from models import db, Ayar, Silo, PvcStok


def create_app():
    """Flask uygulama fabrikası."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # instance klasörünü oluştur (SQLite DB için)
    os.makedirs(os.path.join(app.root_path, 'instance'), exist_ok=True)

    # Veritabanını başlat
    db.init_app(app)

    # Jinja2 şablon filtreleri
    @app.template_filter('tarih')
    def tarih_filtresi(value):
        """Tarihi GG.AA.YYYY formatında gösterir."""
        if isinstance(value, str):
            return value
        if value:
            return value.strftime('%d.%m.%Y')
        return ''

    @app.template_filter('tarih_saat')
    def tarih_saat_filtresi(value):
        """Tarihi GG.AA.YYYY HH:MM formatında gösterir."""
        if value:
            return value.strftime('%d.%m.%Y %H:%M')
        return ''

    @app.template_filter('sayi')
    def sayi_filtresi(value):
        """Sayıyı Türkçe formata çevirir (binlik ayracı nokta, ondalık virgül)."""
        if value is None:
            return '0'
        if isinstance(value, float):
            if value == int(value):
                return f"{int(value):,}".replace(',', '.')
            return f"{value:,.1f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return f"{value:,}".replace(',', '.')

    # Blueprint'leri kaydet
    from routes.dashboard import dashboard_bp
    from routes.hammadde import hammadde_bp
    from routes.formul import formul_bp
    from routes.uretim import uretim_bp
    from routes.geri_donus import geri_donus_bp
    from routes.rapor import rapor_bp
    from routes.ayarlar import ayarlar_bp
    from routes.tedarikci import tedarikci_bp
    from routes.sayim import sayim_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(hammadde_bp, url_prefix='/hammadde')
    app.register_blueprint(formul_bp, url_prefix='/formul')
    app.register_blueprint(uretim_bp, url_prefix='/uretim')
    app.register_blueprint(geri_donus_bp, url_prefix='/geri-donus')
    app.register_blueprint(rapor_bp, url_prefix='/rapor')
    app.register_blueprint(ayarlar_bp, url_prefix='/ayarlar')
    app.register_blueprint(tedarikci_bp, url_prefix='/tedarikci')
    app.register_blueprint(sayim_bp, url_prefix='/sayim')

    # Veritabanını oluştur ve başlangıç verilerini ekle
    with app.app_context():
        db.create_all()
        seed_data()

    return app


def seed_data():
    """Başlangıç verilerini ekler (ilk çalıştırmada)."""
    # Eğer veri varsa tekrar ekleme
    if Silo.query.first():
        return

    # Silolar ve tanklar
    silolar = [
        Silo(ad='DOA Silo', hammadde_tipi='DOA', kapasite_kg=20000, mevcut_kg=0, silo_tipi='silo'),
        Silo(ad='DOTP Silo 1', hammadde_tipi='DOTP', kapasite_kg=20000, mevcut_kg=0, silo_tipi='silo'),
        Silo(ad='DOTP Silo 2', hammadde_tipi='DOTP', kapasite_kg=30000, mevcut_kg=0, silo_tipi='silo'),
        Silo(ad='ESBO Silo 1', hammadde_tipi='ESBO', kapasite_kg=15000, mevcut_kg=0, silo_tipi='silo'),
        Silo(ad='ESBO Silo 2', hammadde_tipi='ESBO', kapasite_kg=30000, mevcut_kg=0, silo_tipi='silo'),
        Silo(ad='Antifog Tankı', hammadde_tipi='Antifog', kapasite_kg=1000, mevcut_kg=0, silo_tipi='tank'),
        Silo(ad='Stabilizer Tankı', hammadde_tipi='Stabilizer', kapasite_kg=1000, mevcut_kg=0, silo_tipi='tank'),
        Silo(ad='Slip Tankı', hammadde_tipi='Slip', kapasite_kg=1000, mevcut_kg=0, silo_tipi='tank'),
        Silo(ad='Kırma Tankı', hammadde_tipi='Kırma', kapasite_kg=500, mevcut_kg=0, silo_tipi='geri_donus'),
        Silo(ad='Pellet Tankı', hammadde_tipi='Pellet', kapasite_kg=500, mevcut_kg=0, silo_tipi='geri_donus'),
    ]
    db.session.add_all(silolar)

    # PVC bigbag stok kayıtları (3 tip)
    pvc_stoklar = [
        PvcStok(bigbag_tipi=750, adet=0),
        PvcStok(bigbag_tipi=1000, adet=0),
        PvcStok(bigbag_tipi=1100, adet=0),
    ]
    db.session.add_all(pvc_stoklar)

    # Varsayılan ayarlar
    ayarlar = [
        Ayar(anahtar='kirma_akis_hizi', deger='0.1', aciklama='Kırma tankı akış hızı (kg/sn)'),
    ]
    db.session.add_all(ayarlar)

    db.session.commit()


# Uygulama başlatma
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
