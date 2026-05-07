"""
Dashboard route — Ana sayfa, silo seviyeleri ve günlük özet.
"""
from datetime import datetime, date
from flask import Blueprint, render_template
from models import db, Silo, PvcStok, Parti, HammaddeGiris, Formul, Ayar

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

    # Tahmini Bitiş Süresi Hesaplama
    tahminler = {}
    varsayilan_formul = Formul.query.filter_by(varsayilan=True, aktif=True).first()
    ayar_parti = Ayar.query.filter_by(anahtar='haftalik_hedef_parti').first()
    haftalik_hedef = int(ayar_parti.deger) if ayar_parti and ayar_parti.deger.isdigit() else 100

    if varsayilan_formul and haftalik_hedef > 0:
        hammadde_map = {
            'PVC': varsayilan_formul.pvc_kg,
            'DOTP': varsayilan_formul.dotp_kg,
            'DOA': varsayilan_formul.doa_kg,
            'ESBO': varsayilan_formul.esbo_kg,
            'Antifog': varsayilan_formul.antifog_kg,
            'Stabilizer': varsayilan_formul.stabilizer_kg,
            'Slip': varsayilan_formul.slip_kg,
            'Pellet': varsayilan_formul.pellet_kg
        }
        
        # Ekstra bileşenleri ekle
        if varsayilan_formul.ekstra_bilesenler:
            for tip, kg in varsayilan_formul.ekstra_bilesenler.items():
                hammadde_map[tip] = float(kg)
                
        # Mevcut stokları topla
        stoklar = {}
        for silo in silolar + geri_donus_tanklari:
            stoklar[silo.hammadde_tipi] = stoklar.get(silo.hammadde_tipi, 0) + silo.mevcut_kg
        stoklar['PVC'] = pvc_toplam_kg
        
        # Tahminleri hesapla
        for tip, kg_per_parti in hammadde_map.items():
            if kg_per_parti > 0:
                haftalik_tuketim = kg_per_parti * haftalik_hedef
                mevcut_stok = stoklar.get(tip, 0)
                if haftalik_tuketim > 0:
                    hafta_kalan = mevcut_stok / haftalik_tuketim
                    tahminler[tip] = {
                        'haftalik_tuketim': haftalik_tuketim,
                        'mevcut_stok': mevcut_stok,
                        'hafta_kalan': hafta_kalan
                    }

    return render_template('dashboard.html',
                           silolar=silolar,
                           geri_donus_tanklari=geri_donus_tanklari,
                           pvc_stoklar=pvc_stoklar,
                           pvc_toplam_kg=pvc_toplam_kg,
                           pvc_toplam_adet=pvc_toplam_adet,
                           bugun_parti_sayisi=bugun_parti_sayisi,
                           bugun_toplam_kg=bugun_toplam_kg,
                           bugun_tuketim=bugun_tuketim,
                           son_partiler=son_partiler,
                           tahminler=tahminler,
                           haftalik_hedef=haftalik_hedef)
