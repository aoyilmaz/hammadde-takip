from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Silo, PvcStok, GeriDonusBigbagStok, SayimFisi, SayimDetay
from services.stok import parse_float, parse_int

sayim_bp = Blueprint('sayim', __name__)

@sayim_bp.route('/')
def index():
    """Sayım girişi sayfası ve geçmiş sayımlar."""
    silolar = Silo.query.order_by(Silo.id).all()
    pvc_stoklar = PvcStok.query.all()
    gd_bigbagler = GeriDonusBigbagStok.query.all()
    
    sayimlar = SayimFisi.query.order_by(SayimFisi.tarih.desc()).limit(20).all()
    
    return render_template('sayim.html', 
                           silolar=silolar, 
                           pvc_stoklar=pvc_stoklar, 
                           gd_bigbagler=gd_bigbagler,
                           sayimlar=sayimlar)

@sayim_bp.route('/kaydet', methods=['POST'])
def kaydet():
    """Sayım formunu kaydet ve stokları eşitle."""
    yapan_kisi = request.form.get('yapan_kisi', 'Sistem')
    notlar = request.form.get('notlar', '')
    
    yeni_sayim = SayimFisi(yapan_kisi=yapan_kisi, notlar=notlar)
    db.session.add(yeni_sayim)
    db.session.flush() # id'yi almak için
    
    degisim_var = False
    
    # 1. Siloları işle
    silolar = Silo.query.all()
    for silo in silolar:
        sayilan_str = request.form.get(f'silo_{silo.id}')
        if sayilan_str is not None and sayilan_str.strip() != '':
            sayilan = parse_float(sayilan_str)
            if round(sayilan, 1) != round(silo.mevcut_kg, 1):
                fark = sayilan - silo.mevcut_kg
                detay = SayimDetay(
                    sayim_fisi_id=yeni_sayim.id,
                    kalem_tipi='silo',
                    kalem_id=silo.id,
                    kalem_adi=silo.ad,
                    onceki_miktar=silo.mevcut_kg,
                    sayilan_miktar=sayilan,
                    fark=fark
                )
                db.session.add(detay)
                silo.mevcut_kg = sayilan
                silo.updated_at = datetime.utcnow()
                degisim_var = True

    # 2. PVC Bigbagleri işle
    pvc_stoklar = PvcStok.query.all()
    for pvc in pvc_stoklar:
        sayilan_str = request.form.get(f'pvc_{pvc.id}')
        acik_str = request.form.get(f'pvc_acik_{pvc.id}')
        if ((sayilan_str is not None and sayilan_str.strip() != '') or
                (acik_str is not None and acik_str.strip() != '')):
            sayilan_adet = parse_int(sayilan_str, pvc.adet)
            sayilan_acik_kg = parse_float(acik_str, pvc.acik_kg or 0)
            sayilan_kg = sayilan_adet * pvc.bigbag_tipi + sayilan_acik_kg
            onceki_kg = pvc.toplam_kg
            if round(sayilan_kg, 1) != round(onceki_kg, 1):
                fark = sayilan_kg - onceki_kg
                detay = SayimDetay(
                    sayim_fisi_id=yeni_sayim.id,
                    kalem_tipi='pvc_bigbag',
                    kalem_id=pvc.id,
                    kalem_adi=f"{pvc.bigbag_tipi} kg PVC Bigbag ({pvc.urun_kodu})",
                    onceki_miktar=onceki_kg,
                    sayilan_miktar=sayilan_kg,
                    fark=fark
                )
                db.session.add(detay)
                pvc.adet = sayilan_adet
                pvc.acik_kg = sayilan_acik_kg
                pvc.mevcut_kg = sayilan_kg
                pvc.updated_at = datetime.utcnow()
                degisim_var = True

    # 3. Geri Dönüşüm Bigbagleri işle
    gd_bigbagler = GeriDonusBigbagStok.query.all()
    for gd in gd_bigbagler:
        sayilan_str = request.form.get(f'gd_{gd.id}')
        if sayilan_str is not None and sayilan_str.strip() != '':
            sayilan = parse_int(sayilan_str)
            if sayilan != gd.adet:
                fark = sayilan - gd.adet
                detay = SayimDetay(
                    sayim_fisi_id=yeni_sayim.id,
                    kalem_tipi='geri_donus_bigbag',
                    kalem_id=gd.id,
                    kalem_adi=f"{gd.agirlik_kg} kg G.D. Bigbag",
                    onceki_miktar=gd.adet,
                    sayilan_miktar=sayilan,
                    fark=fark
                )
                db.session.add(detay)
                gd.adet = sayilan
                gd.updated_at = datetime.utcnow()
                degisim_var = True
                
    if degisim_var:
        db.session.commit()
        flash('Sayım kaydedildi ve stoklar eşitlendi.', 'success')
    else:
        db.session.rollback()
        flash('Herhangi bir stok farkı tespit edilmediği için sayım kaydedilmedi.', 'info')
        
    return redirect(url_for('sayim.index'))
