"""Genel kg bazlı stok, lot ve hareket yardımcıları."""
from datetime import datetime, date
from models import db, Uretici, HammaddeKart, StokLot, StokHareket


def parse_float(value, default=0.0):
    try:
        if value is None or value == '':
            return default
        return float(str(value).replace(',', '.'))
    except (TypeError, ValueError):
        return default


def parse_int(value, default=0):
    try:
        if value is None or value == '':
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def get_or_create_uretici(ad):
    ad = (ad or '').strip()
    if not ad:
        return None
    uretici = Uretici.query.filter(db.func.lower(Uretici.ad) == ad.lower()).first()
    if uretici:
        return uretici
    uretici = Uretici(ad=ad)
    db.session.add(uretici)
    db.session.flush()
    return uretici


def get_or_create_hammadde_kart(hammadde_tipi, hammadde_kodu=None, uretici=None):
    kod = (hammadde_kodu or 'Standart').strip() or 'Standart'
    query = HammaddeKart.query.filter_by(
        hammadde_tipi=hammadde_tipi,
        hammadde_kodu=kod,
        uretici_id=uretici.id if uretici else None
    )
    kart = query.first()
    if kart:
        return kart
    kart = HammaddeKart(hammadde_tipi=hammadde_tipi, hammadde_kodu=kod, uretici=uretici)
    db.session.add(kart)
    db.session.flush()
    return kart


def ambalajdan_kg(paketleme_tipi, paket_adet=0, birim_agirlik_kg=0, acik_kg=0,
                  palet_adet=0, palet_agirlik_kg=0, miktar_kg=0):
    """Ambalaj bilgilerini sistemin ana birimi olan kg'a çevirir."""
    paketleme_tipi = paketleme_tipi or 'dokme'
    if paketleme_tipi == 'palet':
        return palet_adet * palet_agirlik_kg + acik_kg
    if paketleme_tipi in ('bigbag', 'torba', 'ibc', 'varil'):
        return paket_adet * birim_agirlik_kg + acik_kg
    return miktar_kg


def hareket_yaz(lot, hareket_tipi, miktar_kg, onceki_kg=None, sonraki_kg=None,
                referans_tipi=None, referans_id=None, aciklama=None):
    hareket = StokHareket(
        lot=lot,
        hammadde_tipi=lot.hammadde_tipi if lot else '',
        hammadde_kodu=lot.hammadde_kodu if lot else '',
        hareket_tipi=hareket_tipi,
        miktar_kg=miktar_kg,
        onceki_kg=onceki_kg,
        sonraki_kg=sonraki_kg,
        referans_tipi=referans_tipi,
        referans_id=referans_id,
        aciklama=aciklama
    )
    db.session.add(hareket)
    return hareket


def lot_giris_kaydet(hammadde_tipi, miktar_kg, hammadde_kodu=None, uretici=None,
                     tedarikci_id=None, silo_id=None, hammadde_giris_id=None,
                     lot_no=None, ambalaj_tipi='dokme', paket_adet=0,
                     birim_agirlik_kg=0, acik_kg=0, palet_adet=0,
                     palet_agirlik_kg=0, irsaliye_no=None, tarih=None, notlar=None):
    kart = get_or_create_hammadde_kart(hammadde_tipi, hammadde_kodu, uretici)
    lot = StokLot(
        hammadde_kart=kart,
        tedarikci_id=tedarikci_id,
        uretici=uretici,
        silo_id=silo_id,
        hammadde_giris_id=hammadde_giris_id,
        lot_no=lot_no,
        ambalaj_tipi=ambalaj_tipi or 'dokme',
        paket_adet=paket_adet,
        birim_agirlik_kg=birim_agirlik_kg,
        acik_kg=acik_kg,
        palet_adet=palet_adet,
        palet_agirlik_kg=palet_agirlik_kg,
        giris_kg=miktar_kg,
        mevcut_kg=miktar_kg,
        irsaliye_no=irsaliye_no,
        tarih=tarih or date.today(),
        notlar=notlar
    )
    db.session.add(lot)
    db.session.flush()
    hareket_yaz(lot, 'giris', miktar_kg, 0, miktar_kg, 'hammadde_giris', hammadde_giris_id)
    return lot


def lotlardan_tuket(hammadde_tipi, miktar_kg, hammadde_kodu=None, referans_tipi='uretim',
                    referans_id=None):
    """FIFO lot tüketimi yapar. Çağıran önceden stok kontrolü yapmalıdır."""
    if miktar_kg <= 0:
        return []

    query = StokLot.query.join(HammaddeKart).filter(
        HammaddeKart.hammadde_tipi == hammadde_tipi,
        StokLot.mevcut_kg > 0
    )
    if hammadde_kodu:
        query = query.filter(HammaddeKart.hammadde_kodu == hammadde_kodu)

    kalan = miktar_kg
    hareketler = []
    for lot in query.order_by(StokLot.tarih, StokLot.id).all():
        if kalan <= 0:
            break
        onceki = lot.mevcut_kg
        dusulecek = min(kalan, lot.mevcut_kg)
        lot.mevcut_kg -= dusulecek
        lot.updated_at = datetime.utcnow()
        kalan -= dusulecek
        hareketler.append(hareket_yaz(
            lot, 'uretim', -dusulecek, onceki, lot.mevcut_kg, referans_tipi, referans_id
        ))
    return hareketler


def toplam_lot_stok(hammadde_tipi, hammadde_kodu=None):
    query = db.session.query(db.func.sum(StokLot.mevcut_kg)).join(HammaddeKart).filter(
        HammaddeKart.hammadde_tipi == hammadde_tipi
    )
    if hammadde_kodu:
        query = query.filter(HammaddeKart.hammadde_kodu == hammadde_kodu)
    return query.scalar() or 0
