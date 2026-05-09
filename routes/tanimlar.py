from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, HammaddeTipi, HammaddeKart, Silo, Tedarikci, TedarikciHammadde, HammaddeGiris, Uretici
from services.stok import get_or_create_uretici, parse_float, parse_int

tanimlar_bp = Blueprint('tanimlar', __name__)


@tanimlar_bp.route('/')
def index():
    return redirect(url_for('tanimlar.hammadde'))


# === HAMMADDE TİPLERİ ===
@tanimlar_bp.route('/tipler')
def tipler():
    kayitlar = HammaddeTipi.query.filter_by(aktif=True).order_by(HammaddeTipi.ad).all()
    return render_template('tanimlar_tipler.html', kayitlar=kayitlar)


@tanimlar_bp.route('/hammadde-tipi-kaydet', methods=['POST'])
def hammadde_tipi_kaydet():
    tipi_id = request.form.get('tipi_id')
    ad = (request.form.get('ad') or '').strip()
    aciklama = request.form.get('aciklama', '').strip()

    if not ad:
        flash('Hammadde tipi adı zorunludur.', 'error')
        return redirect(url_for('tanimlar.tipler'))

    if tipi_id:
        tipi = HammaddeTipi.query.get_or_404(int(tipi_id))
        tipi.ad = ad
        tipi.aciklama = aciklama
        flash(f'{ad} hammadde tipi güncellendi.', 'success')
    else:
        existing = HammaddeTipi.query.filter_by(ad=ad).first()
        if existing and existing.aktif:
            flash(f'{ad} hammadde tipi zaten mevcut.', 'error')
            return redirect(url_for('tanimlar.tipler'))
        
        tipi = HammaddeTipi(ad=ad, aciklama=aciklama)
        db.session.add(tipi)
        flash(f'{ad} hammadde tipi eklendi.', 'success')

    db.session.commit()
    return redirect(url_for('tanimlar.tipler'))


@tanimlar_bp.route('/hammadde-tipi-sil/<int:tipi_id>', methods=['POST'])
def hammadde_tipi_sil(tipi_id):
    tipi = HammaddeTipi.query.get_or_404(tipi_id)
    ad = tipi.ad
    tipi.aktif = False
    db.session.commit()
    flash(f'{ad} hammadde tipi silindi.', 'success')
    return redirect(url_for('tanimlar.tipler'))


# === HAMMADDE KARTLARI ===
@tanimlar_bp.route('/hammadde')
def hammadde():
    tip_filtre = request.args.get('tip')
    query = HammaddeKart.query.filter_by(aktif=True)
    if tip_filtre:
        query = query.filter_by(hammadde_tipi=tip_filtre)
    
    kayitlar = query.order_by(HammaddeKart.hammadde_tipi, HammaddeKart.hammadde_kodu).all()
    tipler = HammaddeTipi.query.filter_by(aktif=True).order_by(HammaddeTipi.ad).all()
    
    return render_template('tanimlar_hammadde.html', kayitlar=kayitlar, tipler=tipler, tip_filtre=tip_filtre)


@tanimlar_bp.route('/hammadde-kaydet', methods=['POST'])
def hammadde_kaydet():
    kart_id = request.form.get('kart_id')
    hammadde_tipi = (request.form.get('hammadde_tipi') or '').strip()
    hammadde_kodu = (request.form.get('hammadde_kodu') or 'Standart').strip() or 'Standart'
    uretici = get_or_create_uretici(request.form.get('uretici_ad'))
    paketleme_tipi = request.form.get('paketleme_tipi') or 'dokme'
    birim_agirlik_kg = parse_float(request.form.get('birim_agirlik_kg'), 0)
    bigbag_tipi = parse_int(request.form.get('bigbag_tipi'), 0) or None

    if not hammadde_tipi:
        flash('Hammadde tipi zorunludur.', 'error')
        return redirect(url_for('tanimlar.hammadde'))

    if kart_id:
        kart = HammaddeKart.query.get_or_404(int(kart_id))
    else:
        kart = HammaddeKart(hammadde_tipi=hammadde_tipi, hammadde_kodu=hammadde_kodu, uretici=uretici)
        db.session.add(kart)

    kart.hammadde_tipi = hammadde_tipi
    kart.hammadde_kodu = hammadde_kodu
    kart.uretici = uretici
    kart.paketleme_tipi = paketleme_tipi
    kart.birim_agirlik_kg = birim_agirlik_kg
    kart.bigbag_tipi = bigbag_tipi
    kart.notlar = request.form.get('notlar', '')
    kart.tedarik_suresi_gun = parse_int(request.form.get('tedarik_suresi_gun'), 0)
    
    db.session.commit()
    flash(f'{hammadde_tipi} / {hammadde_kodu} hammadde kartı kaydedildi.', 'success')
    return redirect(url_for('tanimlar.hammadde'))


@tanimlar_bp.route('/hammadde-sil/<int:kart_id>', methods=['POST'])
def hammadde_sil(kart_id):
    kart = HammaddeKart.query.get_or_404(kart_id)
    kart.aktif = False
    db.session.commit()
    flash(f'Hammadde kartı pasife alındı.', 'success')
    return redirect(url_for('tanimlar.hammadde'))


# === TEDARİKÇİLER ===
@tanimlar_bp.route('/tedarikci')
def tedarikci():
    kayitlar = Tedarikci.query.filter_by(aktif=True).order_by(Tedarikci.ad).all()
    # Her tedarikçi için son 5 alımı getir
    for t in kayitlar:
        t.son_alimlar = HammaddeGiris.query.filter_by(tedarikci_id=t.id).order_by(HammaddeGiris.tarih.desc()).limit(5).all()
    
    return render_template('tanimlar_tedarikci.html', kayitlar=kayitlar)


@tanimlar_bp.route('/tedarikci-kaydet', methods=['POST'])
def tedarikci_kaydet():
    ted_id = request.form.get('tedarikci_id')
    ad = (request.form.get('ad') or '').strip()
    notlar = request.form.get('notlar', '').strip()

    if not ad:
        flash('Firma adı zorunludur.', 'error')
        return redirect(url_for('tanimlar.tedarikci'))

    if ted_id:
        ted = Tedarikci.query.get_or_404(int(ted_id))
        ted.ad = ad
        ted.notlar = notlar
        flash(f'{ad} bilgileri güncellendi.', 'success')
    else:
        ted = Tedarikci(ad=ad, notlar=notlar)
        db.session.add(ted)
        flash(f'{ad} tedarikçi olarak eklendi.', 'success')

    db.session.commit()
    return redirect(url_for('tanimlar.tedarikci'))


@tanimlar_bp.route('/tedarikci-sil/<int:ted_id>', methods=['POST'])
def tedarikci_sil(ted_id):
    ted = Tedarikci.query.get_or_404(ted_id)
    ted.aktif = False
    db.session.commit()
    flash(f'Tedarikçi pasife alındı.', 'success')
    return redirect(url_for('tanimlar.tedarikci'))


# === SİLO / TANKLAR ===
@tanimlar_bp.route('/silolar')
def silolar():
    kayitlar = Silo.query.filter_by(aktif=True).order_by(Silo.id).all()
    tipler = HammaddeTipi.query.filter_by(aktif=True).order_by(HammaddeTipi.ad).all()
    return render_template('tanimlar_silolar.html', kayitlar=kayitlar, tipler=tipler)


@tanimlar_bp.route('/silo-kaydet', methods=['POST'])
def silo_kaydet():
    silo_id = request.form.get('silo_id')
    ad = request.form.get('silo_ad')
    hammadde_tipi = request.form.get('silo_hammadde_tipi')
    silo_tipi = request.form.get('silo_tipi') or 'silo'
    kapasite = parse_float(request.form.get('kapasite_kg'), 0)

    if not ad or not hammadde_tipi or kapasite <= 0:
        flash('Silo/tank adı, hammadde tipi ve kapasite zorunludur.', 'error')
        return redirect(url_for('tanimlar.silolar'))

    if silo_id:
        silo = Silo.query.get_or_404(int(silo_id))
    else:
        silo = Silo(mevcut_kg=0)
        db.session.add(silo)

    silo.ad = ad
    silo.hammadde_tipi = hammadde_tipi
    silo.silo_tipi = silo_tipi
    silo.kapasite_kg = kapasite
    silo.updated_at = datetime.utcnow()
    
    db.session.commit()
    flash(f'{ad} tanımı kaydedildi.', 'success')
    return redirect(url_for('tanimlar.silolar'))


@tanimlar_bp.route('/silo-sil/<int:silo_id>', methods=['POST'])
def silo_sil(silo_id):
    silo = Silo.query.get_or_404(silo_id)
    if silo.mevcut_kg > 0:
        flash('Stok bulunan silo/tank silinemez.', 'error')
        return redirect(url_for('tanimlar.silolar'))
    
    silo.aktif = False
    db.session.commit()
    flash(f'Silo/tank pasife alındı.', 'success')
    return redirect(url_for('tanimlar.silolar'))
