"""
Veritabanı modelleri — Hammadde Takip Sistemi.
Tüm tablolar ve ilişkiler burada tanımlanır.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Ayar(db.Model):
    """Sistem ayarları (anahtar-değer çiftleri)."""
    __tablename__ = 'ayarlar'

    id = db.Column(db.Integer, primary_key=True)
    anahtar = db.Column(db.String(100), unique=True, nullable=False)
    deger = db.Column(db.String(500), nullable=False)
    aciklama = db.Column(db.String(200))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Ayar {self.anahtar}={self.deger}>'


class Silo(db.Model):
    """Silolar ve tanklar (DOA, DOTP, ESBO, Antifog, Stabilizer, Slip, Kırma, Pellet)."""
    __tablename__ = 'silolar'

    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100), nullable=False)
    hammadde_tipi = db.Column(db.String(50), nullable=False)  # DOA, DOTP, ESBO, vb.
    kapasite_kg = db.Column(db.Float, nullable=False)
    mevcut_kg = db.Column(db.Float, default=0.0)
    silo_tipi = db.Column(db.String(20), default='silo')  # silo, tank, geri_donus
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def doluluk_yuzdesi(self):
        """Doluluk yüzdesini hesaplar."""
        if self.kapasite_kg <= 0:
            return 0
        return round((self.mevcut_kg / self.kapasite_kg) * 100, 1)

    @property
    def renk_kodu(self):
        """Doluluk yüzdesine göre renk kodu döndürür."""
        yuzde = self.doluluk_yuzdesi
        if yuzde >= 75:
            return 'green'
        elif yuzde >= 50:
            return 'blue'
        elif yuzde >= 25:
            return 'orange'
        else:
            return 'red'

    def __repr__(self):
        return f'<Silo {self.ad}: {self.mevcut_kg}/{self.kapasite_kg} kg>'


class PvcStok(db.Model):
    """PVC bigbag stok takibi — her bigbag tipi için bir kayıt."""
    __tablename__ = 'pvc_stok'

    id = db.Column(db.Integer, primary_key=True)
    bigbag_tipi = db.Column(db.Integer, nullable=False)  # 750, 1000, 1100 (kg)
    adet = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def toplam_kg(self):
        """Bu tipteki bigbag'lerin toplam kg'ını hesaplar."""
        return self.bigbag_tipi * self.adet

    def __repr__(self):
        return f'<PvcStok {self.bigbag_tipi}kg x{self.adet}>'

    @staticmethod
    def toplam_pvc_kg():
        """Tüm PVC bigbag tiplerinin toplam kg'ını döndürür."""
        stoklar = PvcStok.query.all()
        return sum(s.toplam_kg for s in stoklar)

    @staticmethod
    def toplam_pvc_adet():
        """Tüm PVC bigbag'lerin toplam adetini döndürür."""
        stoklar = PvcStok.query.all()
        return sum(s.adet for s in stoklar)


class HammaddeGiris(db.Model):
    """Hammadde giriş kayıtları (tanker, bigbag, IBC/varil)."""
    __tablename__ = 'hammadde_giris'

    id = db.Column(db.Integer, primary_key=True)
    hammadde_tipi = db.Column(db.String(50), nullable=False)  # PVC, DOA, DOTP, vb.
    silo_id = db.Column(db.Integer, db.ForeignKey('silolar.id'), nullable=True)
    miktar_kg = db.Column(db.Float, nullable=False)
    bigbag_tipi = db.Column(db.Integer, nullable=True)  # 750, 1000, 1100 (sadece PVC için)
    bigbag_adet = db.Column(db.Integer, nullable=True)  # Sadece PVC için
    tedarikci = db.Column(db.String(200))
    irsaliye_no = db.Column(db.String(100))
    tarih = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    notlar = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # İlişkiler
    silo = db.relationship('Silo', backref='girisler')

    def __repr__(self):
        return f'<HammaddeGiris {self.hammadde_tipi} {self.miktar_kg}kg>'


class Formul(db.Model):
    """Mikser formülleri — farklı ürün tipleri için."""
    __tablename__ = 'formuller'

    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(200), nullable=False)
    pvc_kg = db.Column(db.Float, default=0.0)
    dotp_kg = db.Column(db.Float, default=0.0)
    doa_kg = db.Column(db.Float, default=0.0)
    esbo_kg = db.Column(db.Float, default=0.0)
    antifog_kg = db.Column(db.Float, default=0.0)
    stabilizer_kg = db.Column(db.Float, default=0.0)
    slip_kg = db.Column(db.Float, default=0.0)
    pellet_kg = db.Column(db.Float, default=0.0)
    kirma_sure_sn = db.Column(db.Float, default=0.0)
    varsayilan = db.Column(db.Boolean, default=False)
    aktif = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def toplam_hammadde_kg(self):
        """Bir partinin toplam hammadde miktarını hesaplar (geri dönüşüm hariç)."""
        return (self.pvc_kg + self.dotp_kg + self.doa_kg +
                self.esbo_kg + self.antifog_kg + self.stabilizer_kg + self.slip_kg)

    def formul_snapshot(self):
        """Parti kaydı için formül anlık görüntüsü (JSON)."""
        return {
            'ad': self.ad,
            'pvc_kg': self.pvc_kg,
            'dotp_kg': self.dotp_kg,
            'doa_kg': self.doa_kg,
            'esbo_kg': self.esbo_kg,
            'antifog_kg': self.antifog_kg,
            'stabilizer_kg': self.stabilizer_kg,
            'slip_kg': self.slip_kg,
            'pellet_kg': self.pellet_kg,
            'kirma_sure_sn': self.kirma_sure_sn,
        }

    def __repr__(self):
        return f'<Formul {self.ad}>'


class Parti(db.Model):
    """Üretim parti kayıtları — her mikser partisi için bir kayıt."""
    __tablename__ = 'partiler'

    id = db.Column(db.Integer, primary_key=True)
    parti_no = db.Column(db.String(50), unique=True, nullable=False)
    formul_id = db.Column(db.Integer, db.ForeignKey('formuller.id'), nullable=False)
    formul_adi = db.Column(db.String(200))  # Formül silinse bile adı kalsın
    formul_snapshot = db.Column(db.JSON)  # Parti anındaki formül değerleri
    tarih = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    saat = db.Column(db.String(5))  # "HH:MM"
    toplam_hammadde_kg = db.Column(db.Float, default=0.0)
    kirma_tuketim_kg = db.Column(db.Float, default=0.0)  # Hesaplanan kırma tüketimi
    notlar = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # İlişkiler
    formul = db.relationship('Formul', backref='partiler')

    def __repr__(self):
        return f'<Parti {self.parti_no}>'


class GeriDonusGiris(db.Model):
    """Geri dönüşüm giriş kayıtları (kırma ve pellet tankları)."""
    __tablename__ = 'geri_donus_giris'

    id = db.Column(db.Integer, primary_key=True)
    tank_tipi = db.Column(db.String(20), nullable=False)  # kirma, pellet
    miktar_kg = db.Column(db.Float, nullable=False)
    tarih = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    notlar = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<GeriDonusGiris {self.tank_tipi} {self.miktar_kg}kg>'
