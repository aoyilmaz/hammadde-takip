"""
Dashboard route — Ana sayfa, silo seviyeleri ve günlük özet.
"""
from datetime import datetime, date
from flask import Blueprint, render_template
from models import db, Silo, PvcStok, Parti, HammaddeGiris

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def index():
    """Ana sayfa — silo seviyeleri, PVC stok, günlük özet."""
    # Silolar (geri dönüşüm hariç)
    silolar = Silo.query.filter(Silo.silo_tipi != 'geri_donus').all()

    # Geri dönüşüm tankları
    geri_donus_tanklari = Silo.query.filter_by(silo_tipi='geri_donus').all()

    # PVC bigbag stokları
    pvc_stoklar = PvcStok.query.all()
    pvc_toplam_kg = sum(s.toplam_kg for s in pvc_stoklar)
    pvc_toplam_adet = sum(s.adet for s in pvc_stoklar)

    # Bugünkü üretim özeti
    bugun = date.today()
    bugunun_partileri = Parti.query.filter_by(tarih=bugun).all()
    bugun_parti_sayisi = len(bugunun_partileri)
    bugun_toplam_kg = sum(p.toplam_hammadde_kg for p in bugunun_partileri)

    # Bugünkü hammadde tüketimleri (formül snapshot'larından hesapla)
    bugun_tuketim = {
        'PVC': 0, 'DOTP': 0, 'DOA': 0, 'ESBO': 0,
        'Antifog': 0, 'Stabilizer': 0, 'Slip': 0,
        'Pellet': 0, 'Kırma': 0
    }
    for parti in bugunun_partileri:
        if parti.formul_snapshot:
            s = parti.formul_snapshot
            bugun_tuketim['PVC'] += s.get('pvc_kg', 0)
            bugun_tuketim['DOTP'] += s.get('dotp_kg', 0)
            bugun_tuketim['DOA'] += s.get('doa_kg', 0)
            bugun_tuketim['ESBO'] += s.get('esbo_kg', 0)
            bugun_tuketim['Antifog'] += s.get('antifog_kg', 0)
            bugun_tuketim['Stabilizer'] += s.get('stabilizer_kg', 0)
            bugun_tuketim['Slip'] += s.get('slip_kg', 0)
            bugun_tuketim['Pellet'] += s.get('pellet_kg', 0)
        if parti.kirma_tuketim_kg:
            bugun_tuketim['Kırma'] += parti.kirma_tuketim_kg

    # Son 5 parti
    son_partiler = Parti.query.order_by(Parti.created_at.desc()).limit(5).all()

    return render_template('dashboard.html',
                           silolar=silolar,
                           geri_donus_tanklari=geri_donus_tanklari,
                           pvc_stoklar=pvc_stoklar,
                           pvc_toplam_kg=pvc_toplam_kg,
                           pvc_toplam_adet=pvc_toplam_adet,
                           bugun_parti_sayisi=bugun_parti_sayisi,
                           bugun_toplam_kg=bugun_toplam_kg,
                           bugun_tuketim=bugun_tuketim,
                           son_partiler=son_partiler)
