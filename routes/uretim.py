"""
Üretim route — Parti kayıt, stok düşüm ve toplu üretim.
"""
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db, Silo, PvcStok, Formul, Parti, Ayar

uretim_bp = Blueprint('uretim', __name__)


def stok_kontrol(formul, parti_sayisi=1):
    """Formül için yeterli stok var mı kontrol eder. Eksikleri döndürür."""
    eksikler = []
    pvc_toplam = sum(s.toplam_kg for s in PvcStok.query.all())
    gerekli_pvc = formul.pvc_kg * parti_sayisi
    if gerekli_pvc > pvc_toplam:
        eksikler.append(f'PVC: Gerekli {gerekli_pvc} kg, Mevcut {pvc_toplam} kg')

    # Her hammadde tipi için toplam mevcut stok kontrol et
    hammadde_silo_map = {
        'dotp_kg': 'DOTP', 'doa_kg': 'DOA', 'esbo_kg': 'ESBO',
        'antifog_kg': 'Antifog', 'stabilizer_kg': 'Stabilizer', 'slip_kg': 'Slip'
    }
    for attr, tip in hammadde_silo_map.items():
        gerekli = getattr(formul, attr) * parti_sayisi
        if gerekli <= 0:
            continue
        mevcut = db.session.query(db.func.sum(Silo.mevcut_kg)).filter_by(hammadde_tipi=tip).scalar() or 0
        if gerekli > mevcut:
            eksikler.append(f'{tip}: Gerekli {gerekli} kg, Mevcut {mevcut} kg')
            
    # Ekstra bileşenlerin stok kontrolü
    if formul.ekstra_bilesenler:
        for tip, miktar in formul.ekstra_bilesenler.items():
            gerekli = float(miktar) * parti_sayisi
            if gerekli <= 0:
                continue
            mevcut = db.session.query(db.func.sum(Silo.mevcut_kg)).filter_by(hammadde_tipi=tip).scalar() or 0
            if gerekli > mevcut:
                eksikler.append(f'{tip}: Gerekli {gerekli} kg, Mevcut {mevcut} kg')

    # Geri dönüşüm kontrolleri
    if formul.pellet_kg > 0:
        pellet_tank = Silo.query.filter_by(hammadde_tipi='Pellet').first()
        gerekli_pellet = formul.pellet_kg * parti_sayisi
        if pellet_tank and gerekli_pellet > pellet_tank.mevcut_kg:
            eksikler.append(f'Pellet: Gerekli {gerekli_pellet} kg, Mevcut {pellet_tank.mevcut_kg} kg')

    if formul.kirma_sure_sn > 0:
        kirma_tank = Silo.query.filter_by(hammadde_tipi='Kırma').first()
        kirma_hiz = float(Ayar.query.filter_by(anahtar='kirma_akis_hizi').first().deger or 0.1)
        gerekli_kirma = formul.kirma_sure_sn * kirma_hiz * parti_sayisi
        if kirma_tank and gerekli_kirma > kirma_tank.mevcut_kg:
            eksikler.append(f'Kırma: Gerekli {gerekli_kirma:.1f} kg ({formul.kirma_sure_sn}sn), Mevcut {kirma_tank.mevcut_kg} kg')

    return eksikler


def stok_dus(formul):
    """Bir parti için stoktan düşüm yapar."""
    # PVC düşümü — en büyük bigbag'den başlayarak FIFO
    kalan_pvc = formul.pvc_kg
    for pvc in PvcStok.query.order_by(PvcStok.bigbag_tipi.desc()).all():
        if kalan_pvc <= 0:
            break
        if pvc.adet <= 0:
            continue
        # Bu tipten kaç bigbag gerekiyor?
        while pvc.adet > 0 and kalan_pvc > 0:
            kalan_pvc -= pvc.bigbag_tipi
            if kalan_pvc >= 0:
                pvc.adet -= 1
            else:
                # Kısmi kullanım — bigbag sayısı düşmez, kalan negatif = artık PVC
                break
        pvc.updated_at = datetime.utcnow()

    # Silo/tank düşümleri
    hammadde_map = {
        'dotp_kg': 'DOTP', 'doa_kg': 'DOA', 'esbo_kg': 'ESBO',
        'antifog_kg': 'Antifog', 'stabilizer_kg': 'Stabilizer', 'slip_kg': 'Slip'
    }
    for attr, tip in hammadde_map.items():
        miktar = getattr(formul, attr)
        if miktar <= 0:
            continue
        silolar_tip = Silo.query.filter_by(hammadde_tipi=tip).order_by(Silo.id).all()
        kalan = miktar
        for silo in silolar_tip:
            if kalan <= 0:
                break
            dusulecek = min(kalan, silo.mevcut_kg)
            silo.mevcut_kg -= dusulecek
            silo.updated_at = datetime.utcnow()
            kalan -= dusulecek

    # Ekstra bileşenlerden düşüm
    if formul.ekstra_bilesenler:
        for tip, miktar in formul.ekstra_bilesenler.items():
            miktar = float(miktar)
            if miktar <= 0:
                continue
            silolar_tip = Silo.query.filter_by(hammadde_tipi=tip).order_by(Silo.id).all()
            kalan = miktar
            for silo in silolar_tip:
                if kalan <= 0:
                    break
                dusulecek = min(kalan, silo.mevcut_kg)
                silo.mevcut_kg -= dusulecek
                silo.updated_at = datetime.utcnow()
                kalan -= dusulecek

    # Pellet tankından düşüm
    if formul.pellet_kg > 0:
        pellet_tank = Silo.query.filter_by(hammadde_tipi='Pellet').first()
        if pellet_tank:
            pellet_tank.mevcut_kg = max(0, pellet_tank.mevcut_kg - formul.pellet_kg)
            pellet_tank.updated_at = datetime.utcnow()

    # Kırma tankından düşüm (süre × akış hızı = kg)
    kirma_tuketim_kg = 0
    if formul.kirma_sure_sn > 0:
        kirma_hiz = float(Ayar.query.filter_by(anahtar='kirma_akis_hizi').first().deger or 0.1)
        kirma_tuketim_kg = formul.kirma_sure_sn * kirma_hiz
        kirma_tank = Silo.query.filter_by(hammadde_tipi='Kırma').first()
        if kirma_tank:
            kirma_tank.mevcut_kg = max(0, kirma_tank.mevcut_kg - kirma_tuketim_kg)
            kirma_tank.updated_at = datetime.utcnow()

    return kirma_tuketim_kg


@uretim_bp.route('/')
def index():
    """Üretim sayfası — formül seçimi ve parti geçmişi."""
    formuller = Formul.query.filter_by(aktif=True).order_by(Formul.varsayilan.desc(), Formul.ad).all()
    partiler = Parti.query.order_by(Parti.created_at.desc()).limit(30).all()
    return render_template('uretim.html', formuller=formuller, partiler=partiler)


@uretim_bp.route('/parti-uret', methods=['POST'])
def parti_uret():
    """Parti üretimi — stok kontrol + düşüm + kayıt."""
    formul_id = request.form.get('formul_id')
    parti_sayisi = int(request.form.get('parti_sayisi', 1) or 1)

    if not formul_id:
        flash('Lütfen bir formül seçin.', 'error')
        return redirect(url_for('uretim.index'))

    formul = Formul.query.get_or_404(int(formul_id))

    # Stok kontrolü
    eksikler = stok_kontrol(formul, parti_sayisi)
    if eksikler:
        for eksik in eksikler:
            flash(f'Yetersiz stok: {eksik}', 'error')
        return redirect(url_for('uretim.index'))

    # Parti üretimi
    bugun = date.today()
    bugun_parti_count = Parti.query.filter_by(tarih=bugun).count()
    notlar = request.form.get('notlar', '')

    for i in range(parti_sayisi):
        parti_sira = bugun_parti_count + i + 1
        parti_no = f"P-{bugun.strftime('%Y%m%d')}-{parti_sira:03d}"
        kirma_tuketim = stok_dus(formul)

        parti = Parti(
            parti_no=parti_no,
            formul_id=formul.id,
            formul_adi=formul.ad,
            formul_snapshot=formul.formul_snapshot(),
            tarih=bugun,
            saat=datetime.now().strftime('%H:%M'),
            toplam_hammadde_kg=formul.toplam_hammadde_kg,
            kirma_tuketim_kg=kirma_tuketim,
            notlar=notlar
        )
        db.session.add(parti)

    db.session.commit()
    flash(f'{parti_sayisi} parti başarıyla üretildi (Formül: {formul.ad}).', 'success')
    return redirect(url_for('uretim.index'))


@uretim_bp.route('/formul-detay/<int:formul_id>')
def formul_detay(formul_id):
    """AJAX — Formül detaylarını JSON olarak döndürür."""
    formul = Formul.query.get_or_404(formul_id)
    return jsonify({
        'ad': formul.ad,
        'pvc_kg': formul.pvc_kg,
        'dotp_kg': formul.dotp_kg,
        'doa_kg': formul.doa_kg,
        'esbo_kg': formul.esbo_kg,
        'antifog_kg': formul.antifog_kg,
        'stabilizer_kg': formul.stabilizer_kg,
        'slip_kg': formul.slip_kg,
        'pellet_kg': formul.pellet_kg,
        'kirma_sure_sn': formul.kirma_sure_sn,
        'toplam_kg': formul.toplam_hammadde_kg
    })
