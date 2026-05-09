"""
Silo Takip — PVC Streç Üretim Hattı Hammadde Takip Sistemi.
Ana Flask uygulama dosyası. Veritabanı başlatma ve seed verilerini içerir.
"""

import os
import sqlite3
from datetime import datetime
from flask import Flask
from config import Config
from models import db, Ayar, Silo, PvcStok, AmbalajTipi, HammaddeTipi


def create_app():
    """Flask uygulama fabrikası."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # instance klasörünü oluştur (SQLite DB için)
    os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)

    # Veritabanını başlat
    db.init_app(app)

    # Jinja2 şablon filtreleri
    @app.template_filter("tarih")
    def tarih_filtresi(value):
        """Tarihi GG.AA.YYYY formatında gösterir."""
        if isinstance(value, str):
            return value
        if value:
            return value.strftime("%d.%m.%Y")
        return ""

    @app.template_filter("tarih_saat")
    def tarih_saat_filtresi(value):
        """Tarihi GG.AA.YYYY HH:MM formatında gösterir."""
        if value:
            return value.strftime("%d.%m.%Y %H:%M")
        return ""

    @app.template_filter("sayi")
    def sayi_filtresi(value):
        """Sayıyı Türkçe formata çevirir (binlik ayracı nokta, ondalık virgül)."""
        if value is None:
            return "0"
        if isinstance(value, float):
            if value == int(value):
                return f"{int(value):,}".replace(",", ".")
            return f"{value:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{value:,}".replace(",", ".")

    # Blueprint'leri kaydet
    from routes.dashboard import dashboard_bp
    from routes.hammadde import hammadde_bp
    from routes.formul import formul_bp
    from routes.uretim import uretim_bp
    from routes.geri_donus import geri_donus_bp
    from routes.rapor import rapor_bp
    from routes.ayarlar import ayarlar_bp

    from routes.sayim import sayim_bp
    from routes.tanimlar import tanimlar_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(hammadde_bp, url_prefix="/hammadde")
    app.register_blueprint(formul_bp, url_prefix="/formul")
    app.register_blueprint(uretim_bp, url_prefix="/uretim")
    app.register_blueprint(geri_donus_bp, url_prefix="/geri-donus")
    app.register_blueprint(rapor_bp, url_prefix="/rapor")
    app.register_blueprint(ayarlar_bp, url_prefix="/ayarlar")

    app.register_blueprint(sayim_bp, url_prefix="/sayim")
    app.register_blueprint(tanimlar_bp, url_prefix="/tanimlar")

    # Veritabanını oluştur ve başlangıç verilerini ekle
    with app.app_context():
        db.create_all()
        ensure_schema(app)
        seed_data()
        seed_reference_data()

    return app


def seed_data():
    """Başlangıç verilerini ekler (ilk çalıştırmada)."""
    # Eğer veri varsa tekrar ekleme
    if Silo.query.first():
        return

    # Silolar ve tanklar
    silolar = [
        Silo(
            ad="DOA Silo",
            hammadde_tipi="DOA",
            kapasite_kg=20000,
            mevcut_kg=0,
            silo_tipi="silo",
        ),
        Silo(
            ad="DOTP Silo 1",
            hammadde_tipi="DOTP",
            kapasite_kg=20000,
            mevcut_kg=0,
            silo_tipi="silo",
        ),
        Silo(
            ad="DOTP Silo 2",
            hammadde_tipi="DOTP",
            kapasite_kg=30000,
            mevcut_kg=0,
            silo_tipi="silo",
        ),
        Silo(
            ad="ESBO Silo 1",
            hammadde_tipi="ESBO",
            kapasite_kg=15000,
            mevcut_kg=0,
            silo_tipi="silo",
        ),
        Silo(
            ad="ESBO Silo 2",
            hammadde_tipi="ESBO",
            kapasite_kg=30000,
            mevcut_kg=0,
            silo_tipi="silo",
        ),
        Silo(
            ad="Antifog Tankı",
            hammadde_tipi="Antifog",
            kapasite_kg=1000,
            mevcut_kg=0,
            silo_tipi="tank",
        ),
        Silo(
            ad="Stabilizer Tankı",
            hammadde_tipi="Stabilizer",
            kapasite_kg=1000,
            mevcut_kg=0,
            silo_tipi="tank",
        ),
        Silo(
            ad="Slip Tankı",
            hammadde_tipi="Slip",
            kapasite_kg=1000,
            mevcut_kg=0,
            silo_tipi="tank",
        ),
        Silo(
            ad="Kırma Tankı",
            hammadde_tipi="Kırma",
            kapasite_kg=500,
            mevcut_kg=0,
            silo_tipi="geri_donus",
        ),
        Silo(
            ad="Pellet Tankı",
            hammadde_tipi="Pellet",
            kapasite_kg=500,
            mevcut_kg=0,
            silo_tipi="geri_donus",
        ),
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
        Ayar(
            anahtar="kirma_akis_hizi",
            deger="0.1",
            aciklama="Kırma tankı akış hızı (kg/sn)",
        ),
    ]
    db.session.add_all(ayarlar)

    db.session.commit()


def seed_reference_data():
    """Genel stok sistemi için referans kayıtlarını eksikse oluşturur."""
    from models import StokLot
    from services.stok import lot_giris_kaydet

    # Hammadde Tipleri
    if not HammaddeTipi.query.first():
        db.session.add_all(
            [
                HammaddeTipi(ad="PVC", aciklama="Polyvinyl Chloride - Ana hammadde"),
                HammaddeTipi(ad="DOA", aciklama="Dioctyl Adipate - Plastisizer"),
                HammaddeTipi(ad="DOTP", aciklama="Dioctyl Terephthalate - Plastisizer"),
                HammaddeTipi(
                    ad="ESBO", aciklama="Epoxidized Soybean Oil - Plastisizer"
                ),
                HammaddeTipi(ad="Antifog", aciklama="Antifog ajanı"),
                HammaddeTipi(ad="Stabilizer", aciklama="Isı stabilizatörü"),
                HammaddeTipi(ad="Slip", aciklama="Kayganlaştırıcı"),
                HammaddeTipi(
                    ad="Kırma", aciklama="Geri dönüşümden elde edilen malzeme"
                ),
                HammaddeTipi(ad="Pellet", aciklama="Pelet form"),
            ]
        )

    if not Ayar.query.filter_by(anahtar="haftalik_hedef_parti").first():
        db.session.add(
            Ayar(
                anahtar="haftalik_hedef_parti",
                deger="100",
                aciklama="Haftalık hedeflenen üretim parti sayısı",
            )
        )

    if not AmbalajTipi.query.first():
        db.session.add_all(
            [
                AmbalajTipi(ad="Dökme / Tanker", ambalaj_turu="dokme"),
                AmbalajTipi(ad="IBC", ambalaj_turu="ibc", birim_agirlik_kg=1000),
                AmbalajTipi(ad="Varil", ambalaj_turu="varil", birim_agirlik_kg=200),
                AmbalajTipi(
                    ad="Bigbag 750 kg", ambalaj_turu="bigbag", birim_agirlik_kg=750
                ),
                AmbalajTipi(
                    ad="Bigbag 1000 kg", ambalaj_turu="bigbag", birim_agirlik_kg=1000
                ),
                AmbalajTipi(
                    ad="Bigbag 1100 kg", ambalaj_turu="bigbag", birim_agirlik_kg=1100
                ),
                AmbalajTipi(
                    ad="Torbalı Palet",
                    ambalaj_turu="palet",
                    torba_agirlik_kg=25,
                    torba_adet=55,
                ),
            ]
        )

    for pvc in PvcStok.query.all():
        if pvc.mevcut_kg is None:
            pvc.mevcut_kg = pvc.bigbag_tipi * pvc.adet + (pvc.acik_kg or 0)

    if not StokLot.query.first():
        for pvc in PvcStok.query.all():
            if pvc.toplam_kg > 0:
                lot_giris_kaydet(
                    hammadde_tipi="PVC",
                    miktar_kg=pvc.toplam_kg,
                    hammadde_kodu=pvc.urun_kodu or "Standart",
                    lot_no="DEVIR",
                    ambalaj_tipi="bigbag",
                    paket_adet=pvc.adet,
                    birim_agirlik_kg=pvc.bigbag_tipi,
                    acik_kg=pvc.acik_kg or 0,
                    notlar="Mevcut PVC stok devir kaydı",
                )

        for silo in Silo.query.all():
            if silo.mevcut_kg > 0:
                lot_giris_kaydet(
                    hammadde_tipi=silo.hammadde_tipi,
                    miktar_kg=silo.mevcut_kg,
                    hammadde_kodu="Standart",
                    silo_id=silo.id,
                    lot_no="DEVIR",
                    ambalaj_tipi="dokme",
                    notlar="Mevcut silo/tank stok devir kaydı",
                )

    db.session.commit()


def ensure_schema(app):
    """SQLite için eski veritabanlarına eksik kolonları idempotent ekler."""
    db_path = os.path.join(app.root_path, "instance", "silo_takip.db")
    if not os.path.exists(db_path):
        return

    kolonlar = {
        "pvc_stok": [
            ("urun_kodu", "VARCHAR(100) DEFAULT 'Standart'"),
            ("mevcut_kg", "FLOAT"),
            ("acik_kg", "FLOAT DEFAULT 0"),
        ],
        "hammadde_giris": [
            ("tedarikci_id", "INTEGER REFERENCES tedarikciler(id)"),
            ("urun_kodu", "VARCHAR(100)"),
            ("uretici_id", "INTEGER REFERENCES ureticiler(id)"),
            ("lot_no", "VARCHAR(100)"),
            ("paketleme_tipi", "VARCHAR(30)"),
            ("paket_adet", "INTEGER DEFAULT 0"),
            ("birim_agirlik_kg", "FLOAT DEFAULT 0"),
            ("acik_kg", "FLOAT DEFAULT 0"),
            ("palet_adet", "INTEGER DEFAULT 0"),
            ("palet_agirlik_kg", "FLOAT DEFAULT 0"),
        ],
        "tedarikci_hammadde": [
            ("urun_kodu", "VARCHAR(100)"),
            ("uretici_id", "INTEGER REFERENCES ureticiler(id)"),
            ("paketleme_tipi", "VARCHAR(30) DEFAULT 'dokme'"),
            ("birim_agirlik_kg", "FLOAT DEFAULT 0"),
            ("bigbag_tipi", "INTEGER"),
            ("notlar", "TEXT"),
        ],
        "formuller": [
            ("ekstra_bilesenler", "JSON"),
        ],
        "silolar": [
            ("aktif", "BOOLEAN DEFAULT 1"),
        ],
        "hammadde_kartlari": [
            ("paketleme_tipi", "VARCHAR(30) DEFAULT 'dokme'"),
            ("birim_agirlik_kg", "FLOAT DEFAULT 0"),
            ("bigbag_tipi", "INTEGER"),
            ("tedarik_suresi_gun", "INTEGER DEFAULT 0"),
        ],
    }

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        for tablo, eklenecekler in kolonlar.items():
            cursor.execute(f"PRAGMA table_info({tablo})")
            mevcut = {row[1] for row in cursor.fetchall()}
            for ad, tanim in eklenecekler:
                if ad not in mevcut:
                    cursor.execute(f"ALTER TABLE {tablo} ADD COLUMN {ad} {tanim}")

        cursor.execute(
            "UPDATE pvc_stok SET mevcut_kg = (bigbag_tipi * adet) + COALESCE(acik_kg, 0) "
            "WHERE mevcut_kg IS NULL"
        )
        conn.commit()
    finally:
        conn.close()


# Uygulama başlatma
app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5002)
