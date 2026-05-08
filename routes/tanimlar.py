"""Tanımlar route — Hammadde, tedarikçi/üretici ve silo tanımları."""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, HammaddeTipi, HammaddeKart, Silo, Tedarikci, TedarikciHammadde
from services.stok import get_or_create_uretici, parse_float, parse_int

tanimlar_bp = Blueprint('tanimlar', __name__)


@tanimlar_bp.route('/')
def index():
    hammadde_tipleri_kayitlari = HammaddeTipi.query.filter_by(aktif=True).order_by(HammaddeTipi.ad).all()
    hammadde_kartlari = HammaddeKart.query.order_by(
        HammaddeKart.hammadde_tipi, HammaddeKart.hammadde_kodu
    ).filter_by(aktif=True).all()
    tedarikciler = Tedarikci.query.filter_by(aktif=True).order_by(Tedarikci.ad).all()
    silolar = Silo.query.filter_by(aktif=True).order_by(Silo.id).all()

    # Hammadde tipleri listesi
    hammadde_tipleri = [h.ad for h in hammadde_tipleri_kayitlari]

    return render_template(
        'tanimlar.html',
        hammadde_tipleri_kayitlari=hammadde_tipleri_kayitlari,
        hammadde_kartlari=hammadde_kartlari,
        tedarikciler=tedarikciler,
        silolar=silolar,
        hammadde_tipleri=hammadde_tipleri
    )


@tanimlar_bp.route('/hammadde-tipi-kaydet', methods=['POST'])
def hammadde_tipi_kaydet():
    tipi_id = request.form.get('tipi_id')
    ad = (request.form.get('ad') or '').strip()
    aciklama = request.form.get('aciklama', '').strip()

    if not ad:
        flash('Hammadde tipi adı zorunludur.', 'error')
        return redirect(url_for('tanimlar.index'))

    if tipi_id:
        tipi = HammaddeTipi.query.get_or_404(int(tipi_id))
        tipi.ad = ad
        tipi.aciklama = aciklama
        tipi.updated_at = datetime.utcnow()
        flash(f'{ad} hammadde tipi güncellendi.', 'success')
    else:
        # Yeni tipi ekle
        existing = HammaddeTipi.query.filter_by(ad=ad).first()
        if existing and existing.aktif:
            flash(f'{ad} hammadde tipi zaten mevcut.', 'error')
            return redirect(url_for('tanimlar.index'))
        
        tipi = HammaddeTipi(ad=ad, aciklama=aciklama)
        db.session.add(tipi)
        flash(f'{ad} hammadde tipi eklendi.', 'success')

    db.session.commit()
    return redirect(url_for('tanimlar.index'))


@tanimlar_bp.route('/hammadde-tipi-sil/<int:tipi_id>', methods=['POST'])
def hammadde_tipi_sil(tipi_id):
    tipi = HammaddeTipi.query.get_or_404(tipi_id)
    ad = tipi.ad
    
    # Bu tipi kullanan kartlar varsa kontrol et
    kartlar = HammaddeKart.query.filter_by(hammadde_tipi=ad, aktif=True).count()
    silolar = Silo.query.filter_by(hammadde_tipi=ad, aktif=True).count()
    
    if kartlar > 0 or silolar > 0:
        flash(f'"{ad}" tipi {kartlar} hammadde kartında ve {silolar} siloda kullanılıyor. Önce bunları güncelle veya sil.', 'error')
        return redirect(url_for('tanimlar.index'))
    
    tipi.aktif = False
    tipi.updated_at = datetime.utcnow()
    db.session.commit()
    flash(f'{ad} hammadde tipi pasife alındı.', 'success')
    return redirect(url_for('tanimlar.index'))


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
        return redirect(url_for('tanimlar.index'))

    kart = HammaddeKart.query.get(int(kart_id)) if kart_id else HammaddeKart.query.filter_by(
        hammadde_tipi=hammadde_tipi,
        hammadde_kodu=hammadde_kodu,
        uretici_id=uretici.id if uretici else None
    ).first()
    if not kart:
        kart = HammaddeKart(hammadde_tipi=hammadde_tipi, hammadde_kodu=hammadde_kodu, uretici=uretici)
        db.session.add(kart)

    kart.paketleme_tipi = paketleme_tipi
    kart.birim_agirlik_kg = birim_agirlik_kg
    kart.bigbag_tipi = bigbag_tipi
    kart.notlar = request.form.get('notlar', '')
    kart.updated_at = datetime.utcnow()
    db.session.commit()

    flash(f'{hammadde_tipi} / {hammadde_kodu} hammadde kartı kaydedildi.', 'success')
    return redirect(url_for('tanimlar.index'))


@tanimlar_bp.route('/hammadde-sil/<int:kart_id>', methods=['POST'])
def hammadde_sil(kart_id):
    kart = HammaddeKart.query.get_or_404(kart_id)
    kart.aktif = False
    kart.updated_at = datetime.utcnow()
    db.session.commit()
    flash(f'{kart.hammadde_tipi} / {kart.hammadde_kodu} pasife alındı.', 'success')
    return redirect(url_for('tanimlar.index'))


@tanimlar_bp.route('/tedarikci-kaydet', methods=['POST'])
def tedarikci_kaydet():
    tedarikci_id = request.form.get('tedarikci_id')
    hammadde_tipi = (request.form.get('hammadde_tipi') or '').strip()
    
    # Eğer hammadde_tipi varsa, bu bir "Eşleşme" formudur
    if hammadde_tipi:
        if not tedarikci_id:
            flash('Lütfen önce bir tedarikçi seçin.', 'error')
            return redirect(url_for('tanimlar.index'))
            
        eslesme_id = request.form.get('eslesme_id')
        uretici = get_or_create_uretici(request.form.get('uretici_ad'))
        urun_kodu = (request.form.get('urun_kodu') or '').strip()
        
        if eslesme_id:
            eslesme = TedarikciHammadde.query.get_or_404(int(eslesme_id))
            flash_msg = 'Hammadde eşleşmesi güncellendi.'
        else:
            eslesme = TedarikciHammadde(tedarikci_id=int(tedarikci_id))
            flash_msg = 'Yeni hammadde eşleşmesi eklendi.'
            
        eslesme.hammadde_tipi = hammadde_tipi
        eslesme.urun_kodu = urun_kodu
        eslesme.uretici = uretici
        eslesme.paketleme_tipi = request.form.get('paketleme_tipi') or 'dokme'
        eslesme.birim_agirlik_kg = parse_float(request.form.get('birim_agirlik_kg'), 0)
        eslesme.bigbag_tipi = parse_int(request.form.get('bigbag_tipi'), 0) or None
        eslesme.notlar = request.form.get('eslesme_notlar', '')
        
        db.session.add(eslesme)
        db.session.commit()
        flash(flash_msg, 'success')
    
    # hammadde_tipi yoksa, bu bir "Tedarikçi Bilgileri" formudur
    else:
        if tedarikci_id:
            tedarikci = Tedarikci.query.get_or_404(int(tedarikci_id))
            flash_msg = f'{tedarikci.ad} bilgileri güncellendi.'
        else:
            tedarikci = Tedarikci()
            db.session.add(tedarikci)
            flash_msg = 'Tedarikçi başarıyla kaydedildi.'

        tedarikci.ad = request.form.get('ad', 'İsimsiz Tedarikçi')
        tedarikci.iletisim_kisi = request.form.get('iletisim_kisi', '')
        tedarikci.telefon = request.form.get('telefon', '')
        tedarikci.eposta = request.form.get('eposta', '')
        tedarikci.notlar = request.form.get('notlar', '')
        
        db.session.commit()
        flash(flash_msg, 'success')

    return redirect(url_for('tanimlar.index'))


@tanimlar_bp.route('/eslesme-sil/<int:eslesme_id>', methods=['POST'])
def eslesme_sil(eslesme_id):
    eslesme = TedarikciHammadde.query.get_or_404(eslesme_id)
    db.session.delete(eslesme)
    db.session.commit()
    flash('Tedarikçi-hammadde eşleşmesi silindi.', 'success')
    return redirect(url_for('tanimlar.index'))


@tanimlar_bp.route('/tedarikci-sil/<int:tedarikci_id>', methods=['POST'])
def tedarikci_sil(tedarikci_id):
    tedarikci = Tedarikci.query.get_or_404(tedarikci_id)
    tedarikci.aktif = False
    db.session.commit()
    flash(f'{tedarikci.ad} pasife alındı.', 'success')
    return redirect(url_for('tanimlar.index'))


@tanimlar_bp.route('/silo-kaydet', methods=['POST'])
def silo_kaydet():
    silo_id = request.form.get('silo_id')
    ad = request.form.get('silo_ad')
    hammadde_tipi = request.form.get('silo_hammadde_tipi')
    silo_tipi = request.form.get('silo_tipi') or 'silo'
    kapasite = parse_float(request.form.get('kapasite_kg'), 0)

    if not ad or not hammadde_tipi or kapasite <= 0:
        flash('Silo/tank adı, hammadde tipi ve kapasite zorunludur.', 'error')
        return redirect(url_for('tanimlar.index'))

    silo = Silo.query.get(int(silo_id)) if silo_id else Silo(mevcut_kg=0)
    silo.ad = ad
    silo.hammadde_tipi = hammadde_tipi
    silo.silo_tipi = silo_tipi
    silo.kapasite_kg = kapasite
    silo.aktif = True
    silo.updated_at = datetime.utcnow()
    db.session.add(silo)
    db.session.commit()

    flash(f'{ad} tanımı kaydedildi.', 'success')
    return redirect(url_for('tanimlar.index'))


@tanimlar_bp.route('/silo-sil/<int:silo_id>', methods=['POST'])
def silo_sil(silo_id):
    silo = Silo.query.get_or_404(silo_id)
    if silo.mevcut_kg > 0:
        flash('Stok bulunan silo/tank pasife alınamaz. Önce stok düzeltmesi yapın.', 'error')
        return redirect(url_for('tanimlar.index'))
    silo.aktif = False
    silo.updated_at = datetime.utcnow()
    db.session.commit()
    flash(f'{silo.ad} pasife alındı.', 'success')
    return redirect(url_for('tanimlar.index'))
