"""
Hammadde giriş route — Tanker, bigbag, IBC/varil ile hammadde girişi.
"""
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Silo, PvcStok, HammaddeGiris, Tedarikci, StokLot, HammaddeKart, HammaddeTipi
from services.stok import (
    ambalajdan_kg,
    get_or_create_uretici,
    lot_giris_kaydet,
    hareket_yaz,
    parse_float,
    parse_int,
)

hammadde_bp = Blueprint('hammadde', __name__)


@hammadde_bp.route('/')
def index():
    """Hammadde giriş sayfası — form ve geçmiş kayıtlar."""
    silolar = Silo.query.filter(Silo.silo_tipi != 'geri_donus', Silo.aktif == True).all()
    pvc_stoklar = PvcStok.query.all()
    girisler = HammaddeGiris.query.order_by(HammaddeGiris.created_at.desc()).limit(20).all()

    # Hammadde tipleri
    hammadde_tipleri = [t.ad for t in HammaddeTipi.query.filter_by(aktif=True).order_by(HammaddeTipi.ad).all()]
    
    # Hammadde Kartları (Frontend otomatik doldurma için)
    hammadde_kart_map = [{
        'tip': k.hammadde_tipi,
        'kod': k.hammadde_kodu or '',
        'uretici': k.uretici.ad if k.uretici else '',
        'paketleme': k.paketleme_tipi or '',
        'birim_kg': k.birim_agirlik_kg or 0,
        'bigbag_tipi': k.bigbag_tipi or 0
    } for k in HammaddeKart.query.filter_by(aktif=True).all()]

    # Tedarikçiler (Basit liste)
    tedarikciler = Tedarikci.query.filter_by(aktif=True).order_by(Tedarikci.ad).all()

    # Bigbag tipleri
    bigbag_tipleri = [750, 1000, 1100]
    # Kayıtlı kartlardan ek varsa ekle
    bb_kart = db.session.query(HammaddeKart.bigbag_tipi).filter(HammaddeKart.bigbag_tipi != None).distinct().all()
    for b in bb_kart:
        if b[0] and b[0] not in bigbag_tipleri:
            bigbag_tipleri.append(int(b[0]))
    bigbag_tipleri.sort()

    return render_template('hammadde_giris.html',
                           silolar=silolar,
                           pvc_stoklar=pvc_stoklar,
                           girisler=girisler,
                           tedarikciler=tedarikciler,
                           hammadde_kart_map=hammadde_kart_map,
                           hammadde_tipleri=hammadde_tipleri,
                           bigbag_tipleri=bigbag_tipleri)


@hammadde_bp.route('/ekle', methods=['POST'])
def ekle():
    """Yeni hammadde girişi kaydet."""
    hammadde_tipi = request.form.get('hammadde_tipi')
    tarih_str = request.form.get('tarih', '')
    tedarikci_id_str = request.form.get('tedarikci_id', '')
    tedarikci_id = int(tedarikci_id_str) if tedarikci_id_str and tedarikci_id_str != 'None' else None
    uretici_ad = request.form.get('uretici_ad', '').strip()
    
    # Tedarikçi seçilmemişse üreticiyi tedarikçi olarak kullan
    if not tedarikci_id and uretici_ad:
        ted = Tedarikci.query.filter_by(ad=uretici_ad).first()
        if not ted:
            ted = Tedarikci(ad=uretici_ad, notlar="Otomatik oluşturuldu (Üretici)")
            db.session.add(ted)
            db.session.flush()
        tedarikci_id = ted.id

    uretici = get_or_create_uretici(uretici_ad)
    urun_kodu = request.form.get('urun_kodu', '')
    lot_no = request.form.get('lot_no', '')
    paketleme_tipi = request.form.get('paketleme_tipi', 'dokme')
    paket_adet = parse_int(request.form.get('paket_adet'), 0)
    birim_agirlik_kg = parse_float(request.form.get('birim_agirlik_kg'), 0)
    acik_kg = parse_float(request.form.get('acik_kg'), 0)
    palet_adet = parse_int(request.form.get('palet_adet'), 0)
    palet_agirlik_kg = parse_float(request.form.get('palet_agirlik_kg'), 0)
    irsaliye_no = request.form.get('irsaliye_no', '')
    notlar = request.form.get('notlar', '')

    # Tarih parse et
    try:
        tarih = datetime.strptime(tarih_str, '%Y-%m-%d').date() if tarih_str else date.today()
    except ValueError:
        tarih = date.today()

    if hammadde_tipi == 'PVC':
        # PVC bigbag girişi
        bigbag_tipi = parse_int(request.form.get('bigbag_tipi'), 750)
        bigbag_adet = parse_int(request.form.get('bigbag_adet'), 0)
        pvc_acik_kg = parse_float(request.form.get('pvc_acik_kg'), 0)
        
        # Manuel miktar kontrolü
        miktar_kg = parse_float(request.form.get('miktar_kg'), 0)
        if miktar_kg <= 0:
            miktar_kg = bigbag_tipi * bigbag_adet + pvc_acik_kg

        if miktar_kg <= 0:
            flash('PVC giriş miktarı 0\'dan büyük olmalıdır.', 'error')
            return redirect(url_for('hammadde.index'))

        # PVC stok güncelle (tip ve koda göre)
        pvc_kod = urun_kodu or 'Standart'
        pvc = PvcStok.query.filter_by(bigbag_tipi=bigbag_tipi, urun_kodu=pvc_kod).first()
        if pvc:
            pvc.adet += bigbag_adet
            pvc.mevcut_kg = (pvc.toplam_kg or 0) + miktar_kg
            pvc.acik_kg = (pvc.acik_kg or 0) + pvc_acik_kg
        else:
            pvc = PvcStok(
                bigbag_tipi=bigbag_tipi,
                urun_kodu=pvc_kod,
                adet=bigbag_adet,
                mevcut_kg=miktar_kg,
                acik_kg=pvc_acik_kg
            )
            db.session.add(pvc)
        pvc.updated_at = datetime.utcnow()

        # Giriş kaydı oluştur
        giris = HammaddeGiris(
            hammadde_tipi='PVC',
            miktar_kg=miktar_kg,
            bigbag_tipi=bigbag_tipi,
            bigbag_adet=bigbag_adet,
            tedarikci_id=tedarikci_id,
            uretici_id=uretici.id if uretici else None,
            urun_kodu=urun_kodu,
            lot_no=lot_no,
            paketleme_tipi='bigbag',
            paket_adet=bigbag_adet,
            birim_agirlik_kg=bigbag_tipi,
            acik_kg=pvc_acik_kg,
            irsaliye_no=irsaliye_no,
            tarih=tarih,
            notlar=notlar
        )
        db.session.add(giris)
        db.session.flush()
        lot_giris_kaydet(
            hammadde_tipi='PVC',
            miktar_kg=miktar_kg,
            hammadde_kodu=pvc_kod,
            uretici=uretici,
            tedarikci_id=tedarikci_id,
            hammadde_giris_id=giris.id,
            lot_no=lot_no,
            ambalaj_tipi='bigbag',
            paket_adet=bigbag_adet,
            birim_agirlik_kg=bigbag_tipi,
            acik_kg=pvc_acik_kg,
            irsaliye_no=irsaliye_no,
            tarih=tarih,
            notlar=notlar
        )
        db.session.commit()

        flash(f'{bigbag_adet} adet {bigbag_tipi} kg PVC bigbag girişi yapıldı ({miktar_kg} kg).', 'success')

    else:
        # Silo/tank girişi (DOA, DOTP, ESBO, Antifog, Stabilizer, Slip)
        silo_id = request.form.get('silo_id')
        miktar_kg = parse_float(request.form.get('miktar_kg'), 0)
        
        # Ambalajdan hesaplanan miktar (bilgi amaçlı veya varsayılan olarak kullanılabilir)
        hesaplanan_kg = ambalajdan_kg(
            paketleme_tipi,
            paket_adet=paket_adet,
            birim_agirlik_kg=birim_agirlik_kg,
            acik_kg=acik_kg,
            palet_adet=palet_adet,
            palet_agirlik_kg=palet_agirlik_kg,
            miktar_kg=miktar_kg
        )
        
        # Eğer manuel miktar girilmemişse veya 0 ise hesaplanan miktarı kullan
        if miktar_kg <= 0 and hesaplanan_kg > 0:
            miktar_kg = hesaplanan_kg

        if not silo_id or miktar_kg <= 0:
            flash('Silo seçimi ve miktar zorunludur.', 'error')
            return redirect(url_for('hammadde.index'))

        silo = Silo.query.get(int(silo_id))
        if not silo:
            flash('Geçersiz silo seçimi.', 'error')
            return redirect(url_for('hammadde.index'))

        # Kapasite kontrolü
        if silo.mevcut_kg + miktar_kg > silo.kapasite_kg:
            flash(f'Dikkat: {silo.ad} kapasitesi aşılıyor! '
                  f'Mevcut: {silo.mevcut_kg} kg, Kapasite: {silo.kapasite_kg} kg', 'warning')

        # Silo güncelle
        silo.mevcut_kg += miktar_kg
        silo.updated_at = datetime.utcnow()

        # Giriş kaydı oluştur
        giris = HammaddeGiris(
            hammadde_tipi=hammadde_tipi,
            silo_id=silo.id,
            miktar_kg=miktar_kg,
            tedarikci_id=tedarikci_id,
            uretici_id=uretici.id if uretici else None,
            urun_kodu=urun_kodu,
            lot_no=lot_no,
            paketleme_tipi=paketleme_tipi,
            paket_adet=paket_adet,
            birim_agirlik_kg=birim_agirlik_kg,
            acik_kg=acik_kg,
            palet_adet=palet_adet,
            palet_agirlik_kg=palet_agirlik_kg,
            irsaliye_no=irsaliye_no,
            tarih=tarih,
            notlar=notlar
        )
        db.session.add(giris)
        db.session.flush()
        lot_giris_kaydet(
            hammadde_tipi=hammadde_tipi,
            miktar_kg=miktar_kg,
            hammadde_kodu=urun_kodu or 'Standart',
            uretici=uretici,
            tedarikci_id=tedarikci_id,
            silo_id=silo.id,
            hammadde_giris_id=giris.id,
            lot_no=lot_no,
            ambalaj_tipi=paketleme_tipi,
            paket_adet=paket_adet,
            birim_agirlik_kg=birim_agirlik_kg,
            acik_kg=acik_kg,
            palet_adet=palet_adet,
            palet_agirlik_kg=palet_agirlik_kg,
            irsaliye_no=irsaliye_no,
            tarih=tarih,
            notlar=notlar
        )
        db.session.commit()

        flash(f'{silo.ad} → {miktar_kg} kg {hammadde_tipi} girişi yapıldı.', 'success')

    return redirect(url_for('hammadde.index'))


@hammadde_bp.route('/sil/<int:giris_id>', methods=['POST'])
def sil(giris_id):
    """Hammadde giriş kaydını sil ve stoku geri al."""
    giris = HammaddeGiris.query.get_or_404(giris_id)
    lotlar = StokLot.query.filter_by(hammadde_giris_id=giris.id).all()
    if any(round(lot.mevcut_kg, 3) != round(lot.giris_kg, 3) for lot in lotlar):
        flash('Bu girişe bağlı lottan tüketim yapılmış. Önce üretim/sayım hareketlerini kontrol edin.', 'error')
        return redirect(url_for('hammadde.index'))

    # Stoku geri al
    if giris.hammadde_tipi == 'PVC':
        pvc_kod = giris.urun_kodu or 'Standart'
        pvc = PvcStok.query.filter_by(bigbag_tipi=giris.bigbag_tipi, urun_kodu=pvc_kod).first()
        if pvc:
            pvc.adet = max(0, pvc.adet - (giris.bigbag_adet or 0))
            pvc.mevcut_kg = max(0, (pvc.toplam_kg or 0) - giris.miktar_kg)
            pvc.acik_kg = max(0, (pvc.acik_kg or 0) - (giris.acik_kg or 0))
            pvc.updated_at = datetime.utcnow()
    elif giris.silo_id:
        silo = Silo.query.get(giris.silo_id)
        if silo:
            silo.mevcut_kg = max(0, silo.mevcut_kg - giris.miktar_kg)
            silo.updated_at = datetime.utcnow()

    for lot in lotlar:
        hareket_yaz(lot, 'silme', -lot.mevcut_kg, lot.mevcut_kg, 0, 'hammadde_giris', giris.id)
        lot.mevcut_kg = 0
        lot.aktif = False
        lot.updated_at = datetime.utcnow()

    db.session.delete(giris)
    db.session.commit()
    flash('Hammadde giriş kaydı silindi ve stok güncellendi.', 'success')
    return redirect(url_for('hammadde.index'))
