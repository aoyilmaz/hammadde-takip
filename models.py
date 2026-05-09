"""
Veritabanı modelleri — Hammadde Takip Sistemi.
Tüm tablolar ve ilişkiler burada tanımlanır.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class HammaddeTipi(db.Model):
    """Hammadde tipleri - merkez yönetimi."""
    __tablename__ = 'hammadde_tipleri'

    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100), unique=True, nullable=False)
    aciklama = db.Column(db.Text)
    aktif = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<HammaddeTipi {self.ad}>'


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
    aktif = db.Column(db.Boolean, default=True)
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
    """PVC ambalaj stok takibi — kg ana stok, adet sayım kolaylığı içindir."""
    __tablename__ = 'pvc_stok'

    id = db.Column(db.Integer, primary_key=True)
    bigbag_tipi = db.Column(db.Integer, nullable=False)  # 750, 1000, 1100 (kg)
    urun_kodu = db.Column(db.String(100), default='Standart') # Ürün kodu ayrımı
    adet = db.Column(db.Integer, default=0)
    mevcut_kg = db.Column(db.Float, nullable=True)
    acik_kg = db.Column(db.Float, default=0.0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def toplam_kg(self):
        """Gerçek PVC stoku kg bazlıdır; eski kayıtlarda adetten hesaplanır."""
        if self.mevcut_kg is not None:
            return self.mevcut_kg
        return self.bigbag_tipi * self.adet

    @property
    def tam_bigbag_kg(self):
        return self.bigbag_tipi * self.adet

    def __repr__(self):
        return f'<PvcStok {self.urun_kodu} {self.toplam_kg}kg>'

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


class Tedarikci(db.Model):
    """Tedarikçi firma bilgileri."""
    __tablename__ = 'tedarikciler'

    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(200), nullable=False)
    iletisim_kisi = db.Column(db.String(100))
    telefon = db.Column(db.String(50))
    eposta = db.Column(db.String(100))
    notlar = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    aktif = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Tedarikci {self.ad}>'


class Uretici(db.Model):
    """Malzemenin gerçek üreticisi. Tedarikçi, bize satan firmadır."""
    __tablename__ = 'ureticiler'

    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(200), unique=True, nullable=False)
    notlar = db.Column(db.Text)
    aktif = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Uretici {self.ad}>'


class HammaddeKart(db.Model):
    """Hammadde/katkı ana kartı: tip, kod ve üretici bilgisini birleştirir."""
    __tablename__ = 'hammadde_kartlari'

    id = db.Column(db.Integer, primary_key=True)
    hammadde_tipi = db.Column(db.String(50), nullable=False)
    hammadde_kodu = db.Column(db.String(100), default='Standart')
    uretici_id = db.Column(db.Integer, db.ForeignKey('ureticiler.id'), nullable=True)
    paketleme_tipi = db.Column(db.String(30), default='dokme')
    birim_agirlik_kg = db.Column(db.Float, default=0.0)
    bigbag_tipi = db.Column(db.Integer, nullable=True)
    birim = db.Column(db.String(20), default='kg')
    notlar = db.Column(db.Text)
    tedarik_suresi_gun = db.Column(db.Integer, default=0)
    aktif = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    uretici = db.relationship('Uretici', backref='hammadde_kartlari')

    @property
    def stok_kg(self):
        return sum(lot.mevcut_kg for lot in self.lotlar)

    @property
    def etiket(self):
        parcalar = [self.hammadde_tipi]
        if self.hammadde_kodu:
            parcalar.append(self.hammadde_kodu)
        if self.uretici:
            parcalar.append(self.uretici.ad)
        return ' / '.join(parcalar)

    def __repr__(self):
        return f'<HammaddeKart {self.etiket}>'


class AmbalajTipi(db.Model):
    """Sayım/giriş kolaylığı için genel ambalaj tanımı."""
    __tablename__ = 'ambalaj_tipleri'

    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100), nullable=False)
    ambalaj_turu = db.Column(db.String(30), nullable=False)  # dokme, tanker, ibc, varil, torba, bigbag, palet
    birim_agirlik_kg = db.Column(db.Float, default=0.0)
    torba_agirlik_kg = db.Column(db.Float, default=0.0)
    torba_adet = db.Column(db.Integer, default=0)
    aktif = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def palet_agirlik_kg(self):
        if self.ambalaj_turu == 'palet' and self.torba_agirlik_kg and self.torba_adet:
            return self.torba_agirlik_kg * self.torba_adet
        return self.birim_agirlik_kg

    def __repr__(self):
        return f'<AmbalajTipi {self.ad}>'


class TedarikciHammadde(db.Model):
    """Tedarikçilerin hangi hammaddeleri sattığını tutan eşleştirme."""
    __tablename__ = 'tedarikci_hammadde'
    
    id = db.Column(db.Integer, primary_key=True)
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikciler.id', ondelete='CASCADE'), nullable=False)
    hammadde_tipi = db.Column(db.String(50), nullable=False)
    urun_kodu = db.Column(db.String(100), nullable=True)  # Tedarikçinin bu hammadde için kullandığı ürün kodu
    uretici_id = db.Column(db.Integer, db.ForeignKey('ureticiler.id'), nullable=True)
    paketleme_tipi = db.Column(db.String(30), default='dokme')
    birim_agirlik_kg = db.Column(db.Float, default=0.0)
    bigbag_tipi = db.Column(db.Integer, nullable=True)
    notlar = db.Column(db.Text)
    
    tedarikci = db.relationship('Tedarikci', backref=db.backref('hammadde_tipleri', cascade='all, delete-orphan'))
    uretici = db.relationship('Uretici', backref='tedarikci_eslesmeleri')



class HammaddeGiris(db.Model):
    """Hammadde giriş kayıtları (tanker, bigbag, IBC/varil)."""
    __tablename__ = 'hammadde_giris'

    id = db.Column(db.Integer, primary_key=True)
    hammadde_tipi = db.Column(db.String(50), nullable=False)  # PVC, DOA, DOTP, vb.
    silo_id = db.Column(db.Integer, db.ForeignKey('silolar.id'), nullable=True)
    miktar_kg = db.Column(db.Float, nullable=False)
    bigbag_tipi = db.Column(db.Integer, nullable=True)  # 750, 1000, 1100 (sadece PVC için)
    bigbag_adet = db.Column(db.Integer, nullable=True)  # Sadece PVC için
    tedarikci = db.Column(db.String(200)) # Geriye dönük uyumluluk için eski metin alanı
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikciler.id'), nullable=True)
    uretici_id = db.Column(db.Integer, db.ForeignKey('ureticiler.id'), nullable=True)
    irsaliye_no = db.Column(db.String(100))
    urun_kodu = db.Column(db.String(100)) # Snapshot of product code from supplier
    lot_no = db.Column(db.String(100))
    paketleme_tipi = db.Column(db.String(30))
    paket_adet = db.Column(db.Integer, default=0)
    birim_agirlik_kg = db.Column(db.Float, default=0.0)
    acik_kg = db.Column(db.Float, default=0.0)
    palet_adet = db.Column(db.Integer, default=0)
    palet_agirlik_kg = db.Column(db.Float, default=0.0)
    tarih = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    notlar = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # İlişkiler
    silo = db.relationship('Silo', backref='girisler')
    tedarikci_rel = db.relationship('Tedarikci', backref='giris_kayitlari')
    uretici = db.relationship('Uretici', backref='giris_kayitlari')

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
    ekstra_bilesenler = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def toplam_hammadde_kg(self):
        """Bir partinin toplam hammadde miktarını hesaplar (geri dönüşüm hariç)."""
        toplam = (self.pvc_kg + self.dotp_kg + self.doa_kg +
                self.esbo_kg + self.antifog_kg + self.stabilizer_kg + self.slip_kg)
        if self.ekstra_bilesenler:
            for k, v in self.ekstra_bilesenler.items():
                try:
                    toplam += float(v)
                except (ValueError, TypeError):
                    pass
        return toplam

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
            'ekstra_bilesenler': self.ekstra_bilesenler or {}
        }

    def __repr__(self):
        return f'<Formul {self.ad}>'


class FormulMaliyet(db.Model):
    """Kaydedilen formül maliyet hesaplamaları."""
    __tablename__ = 'formul_maliyetleri'

    id = db.Column(db.Integer, primary_key=True)
    formul_id = db.Column(db.Integer, db.ForeignKey('formuller.id', ondelete='SET NULL'), nullable=True)
    formul_ad = db.Column(db.String(200))
    tarih = db.Column(db.DateTime, default=datetime.utcnow)
    eur_usd_rate = db.Column(db.Float, default=1.0)
    toplam_maliyet_usd = db.Column(db.Float)
    ton_maliyet_usd = db.Column(db.Float)
    detaylar = db.Column(db.JSON) # Bileşen fiyatları ve para birimleri
    notlar = db.Column(db.Text)

    formul = db.relationship('Formul', backref='maliyet_kayitlari')

    def __repr__(self):
        return f'<FormulMaliyet {self.formul_ad} - {self.tarih}>'



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


class GeriDonusBigbagStok(db.Model):
    """Geri dönüşümden elde edilen bigbag stoku."""
    __tablename__ = 'geri_donus_bigbag_stok'

    id = db.Column(db.Integer, primary_key=True)
    agirlik_kg = db.Column(db.Float, nullable=False) # Her bir bigbag ağırlığı
    adet = db.Column(db.Integer, default=0)
    olusturma_tarihi = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notlar = db.Column(db.Text)

    @property
    def toplam_kg(self):
        return self.agirlik_kg * self.adet

    def __repr__(self):
        return f'<GeriDonusBigbag {self.agirlik_kg}kg x{self.adet}>'


class StokLot(db.Model):
    """Lot bazlı gerçek stok. Asıl miktar her zaman kg olarak tutulur."""
    __tablename__ = 'stok_lotlari'

    id = db.Column(db.Integer, primary_key=True)
    hammadde_kart_id = db.Column(db.Integer, db.ForeignKey('hammadde_kartlari.id'), nullable=False)
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikciler.id'), nullable=True)
    uretici_id = db.Column(db.Integer, db.ForeignKey('ureticiler.id'), nullable=True)
    silo_id = db.Column(db.Integer, db.ForeignKey('silolar.id'), nullable=True)
    hammadde_giris_id = db.Column(db.Integer, db.ForeignKey('hammadde_giris.id'), nullable=True)
    lot_no = db.Column(db.String(100))
    ambalaj_tipi = db.Column(db.String(30), default='dokme')
    paket_adet = db.Column(db.Integer, default=0)
    birim_agirlik_kg = db.Column(db.Float, default=0.0)
    acik_kg = db.Column(db.Float, default=0.0)
    palet_adet = db.Column(db.Integer, default=0)
    palet_agirlik_kg = db.Column(db.Float, default=0.0)
    giris_kg = db.Column(db.Float, nullable=False, default=0.0)
    mevcut_kg = db.Column(db.Float, nullable=False, default=0.0)
    irsaliye_no = db.Column(db.String(100))
    tarih = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    aktif = db.Column(db.Boolean, default=True)
    notlar = db.Column(db.Text)

    hammadde_kart = db.relationship('HammaddeKart', backref='lotlar')
    tedarikci = db.relationship('Tedarikci', backref='stok_lotlari')
    uretici = db.relationship('Uretici', backref='stok_lotlari')
    silo = db.relationship('Silo', backref='stok_lotlari')
    hammadde_giris = db.relationship('HammaddeGiris', backref='stok_lotlari')

    @property
    def hammadde_tipi(self):
        return self.hammadde_kart.hammadde_tipi if self.hammadde_kart else ''

    @property
    def hammadde_kodu(self):
        return self.hammadde_kart.hammadde_kodu if self.hammadde_kart else ''

    def __repr__(self):
        return f'<StokLot {self.hammadde_tipi} {self.lot_no or "-"} {self.mevcut_kg}kg>'


class StokHareket(db.Model):
    """Tüm stok değişikliklerinin izlenebilir hareket kaydı."""
    __tablename__ = 'stok_hareketleri'

    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('stok_lotlari.id'), nullable=True)
    hammadde_tipi = db.Column(db.String(50), nullable=False)
    hammadde_kodu = db.Column(db.String(100))
    hareket_tipi = db.Column(db.String(30), nullable=False)  # giris, uretim, sayim, silme, duzeltme
    miktar_kg = db.Column(db.Float, nullable=False)
    onceki_kg = db.Column(db.Float)
    sonraki_kg = db.Column(db.Float)
    referans_tipi = db.Column(db.String(50))
    referans_id = db.Column(db.Integer)
    aciklama = db.Column(db.Text)
    tarih = db.Column(db.DateTime, default=datetime.utcnow)

    lot = db.relationship('StokLot', backref='hareketler')

    def __repr__(self):
        return f'<StokHareket {self.hareket_tipi} {self.hammadde_tipi} {self.miktar_kg}kg>'


class SayimFisi(db.Model):
    """Toplu sayım kayıt belgesi."""
    __tablename__ = 'sayim_fisleri'

    id = db.Column(db.Integer, primary_key=True)
    tarih = db.Column(db.DateTime, default=datetime.utcnow)
    yapan_kisi = db.Column(db.String(100))
    notlar = db.Column(db.Text)
    
    detaylar = db.relationship('SayimDetay', backref='sayim_fisi', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<SayimFisi {self.tarih.strftime("%Y-%m-%d %H:%M")}>'


class SayimDetay(db.Model):
    """Sayım detay satırları."""
    __tablename__ = 'sayim_detaylari'

    id = db.Column(db.Integer, primary_key=True)
    sayim_fisi_id = db.Column(db.Integer, db.ForeignKey('sayim_fisleri.id'), nullable=False)
    
    # Neyi sayıyoruz? (Silo, PVC, Geri Dönüşüm)
    kalem_tipi = db.Column(db.String(50), nullable=False) # 'silo', 'pvc_bigbag', 'geri_donus_bigbag'
    kalem_id = db.Column(db.Integer, nullable=False) # Silo.id veya PvcStok.id
    kalem_adi = db.Column(db.String(200)) # Örn: "DOTP Silo 1" veya "750kg PVC Bigbag"
    
    # Değerler
    onceki_miktar = db.Column(db.Float, nullable=False)
    sayilan_miktar = db.Column(db.Float, nullable=False)
    fark = db.Column(db.Float, nullable=False) # sayilan - onceki
