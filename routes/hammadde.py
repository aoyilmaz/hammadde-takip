"""
Hammadde giriş route — Tanker, bigbag, IBC/varil ile hammadde girişi.
"""
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Silo, PvcStok, HammaddeGiris, Tedarikci

hammadde_bp = Blueprint('hammadde', __name__)


@hammadde_bp.route('/')
def index():
    """Hammadde giriş sayfası — form ve geçmiş kayıtlar."""
    silolar = Silo.query.filter(Silo.silo_tipi != 'geri_donus').all()
    pvc_stoklar = PvcStok.query.all()
    girisler = HammaddeGiris.query.order_by(HammaddeGiris.created_at.desc()).limit(20).all()

    # Hammadde tipleri (Dinamik)
    silolar_tipler = db.session.query(Silo.hammadde_tipi).filter(Silo.silo_tipi != 'geri_donus').distinct().all()
    hammadde_tipleri = sorted(list(set([s[0] for s in silolar_tipler] + ['PVC'])))

    # Tedarikçiler
    tedarikciler = Tedarikci.query.filter_by(aktif=True).all()
    tedarikci_map = []
    for t in tedarikciler:
        tipler = [{'tip': th.hammadde_tipi, 'kod': th.urun_kodu or ''} for th in t.hammadde_tipleri]
        tedarikci_map.append({'id': t.id, 'ad': t.ad, 'tipler': tipler})

    return render_template('hammadde_giris.html',
                           silolar=silolar,
                           pvc_stoklar=pvc_stoklar,
                           girisler=girisler,
                           tedarikci_map=tedarikci_map,
                           hammadde_tipleri=hammadde_tipleri)


@hammadde_bp.route('/ekle', methods=['POST'])
def ekle():
    """Yeni hammadde girişi kaydet."""
    hammadde_tipi = request.form.get('hammadde_tipi')
    tarih_str = request.form.get('tarih', '')
    tedarikci_id_str = request.form.get('tedarikci_id', '')
    tedarikci_id = int(tedarikci_id_str) if tedarikci_id_str else None
    urun_kodu = request.form.get('urun_kodu', '')
    irsaliye_no = request.form.get('irsaliye_no', '')
    notlar = request.form.get('notlar', '')

    # Tarih parse et
    try:
        tarih = datetime.strptime(tarih_str, '%Y-%m-%d').date() if tarih_str else date.today()
    except ValueError:
        tarih = date.today()

    if hammadde_tipi == 'PVC':
        # PVC bigbag girişi
        bigbag_tipi = int(request.form.get('bigbag_tipi', 750))
        bigbag_adet = int(request.form.get('bigbag_adet', 0))
        miktar_kg = bigbag_tipi * bigbag_adet

        if bigbag_adet <= 0:
            flash('Bigbag adedi 0\'dan büyük olmalıdır.', 'error')
            return redirect(url_for('hammadde.index'))

        # PVC stok güncelle (tip ve koda göre)
        pvc_kod = urun_kodu or 'Standart'
        pvc = PvcStok.query.filter_by(bigbag_tipi=bigbag_tipi, urun_kodu=pvc_kod).first()
        if pvc:
            pvc.adet += bigbag_adet
        else:
            pvc = PvcStok(bigbag_tipi=bigbag_tipi, urun_kodu=pvc_kod, adet=bigbag_adet)
            db.session.add(pvc)
        pvc.updated_at = datetime.utcnow()

        # Giriş kaydı oluştur
        giris = HammaddeGiris(
            hammadde_tipi='PVC',
            miktar_kg=miktar_kg,
            bigbag_tipi=bigbag_tipi,
            bigbag_adet=bigbag_adet,
            tedarikci_id=tedarikci_id,
            urun_kodu=urun_kodu,
            irsaliye_no=irsaliye_no,
            tarih=tarih,
            notlar=notlar
        )
        db.session.add(giris)
        db.session.commit()

        flash(f'{bigbag_adet} adet {bigbag_tipi} kg PVC bigbag girişi yapıldı ({miktar_kg} kg).', 'success')

    else:
        # Silo/tank girişi (DOA, DOTP, ESBO, Antifog, Stabilizer, Slip)
        silo_id = request.form.get('silo_id')
        miktar_kg = float(request.form.get('miktar_kg', 0))

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
            urun_kodu=urun_kodu,
            irsaliye_no=irsaliye_no,
            tarih=tarih,
            notlar=notlar
        )
        db.session.add(giris)
        db.session.commit()

        flash(f'{silo.ad} → {miktar_kg} kg {hammadde_tipi} girişi yapıldı.', 'success')

    return redirect(url_for('hammadde.index'))


@hammadde_bp.route('/sil/<int:giris_id>', methods=['POST'])
def sil(giris_id):
    """Hammadde giriş kaydını sil ve stoku geri al."""
    giris = HammaddeGiris.query.get_or_404(giris_id)

    # Stoku geri al
    if giris.hammadde_tipi == 'PVC':
        pvc_kod = giris.urun_kodu or 'Standart'
        pvc = PvcStok.query.filter_by(bigbag_tipi=giris.bigbag_tipi, urun_kodu=pvc_kod).first()
        if pvc and pvc.adet >= giris.bigbag_adet:
            pvc.adet -= giris.bigbag_adet
            pvc.updated_at = datetime.utcnow()
    elif giris.silo_id:
        silo = Silo.query.get(giris.silo_id)
        if silo:
            silo.mevcut_kg = max(0, silo.mevcut_kg - giris.miktar_kg)
            silo.updated_at = datetime.utcnow()

    db.session.delete(giris)
    db.session.commit()
    flash('Hammadde giriş kaydı silindi ve stok güncellendi.', 'success')
    return redirect(url_for('hammadde.index'))
