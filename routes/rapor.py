"""
Raporlama route — Günlük/tarihsel tüketim raporları ve CSV çıktısı.
"""
import csv
import io
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, Response
from models import db, Parti, HammaddeGiris, GeriDonusGiris

rapor_bp = Blueprint('rapor', __name__)


@rapor_bp.route('/')
def index():
    """Rapor sayfası — filtreli raporlama."""
    # Tarih filtresi
    baslangic_str = request.args.get('baslangic', '')
    bitis_str = request.args.get('bitis', '')

    try:
        baslangic = datetime.strptime(baslangic_str, '%Y-%m-%d').date() if baslangic_str else date.today()
    except ValueError:
        baslangic = date.today()
    try:
        bitis = datetime.strptime(bitis_str, '%Y-%m-%d').date() if bitis_str else date.today()
    except ValueError:
        bitis = date.today()

    # Partiler
    partiler = Parti.query.filter(
        Parti.tarih >= baslangic, Parti.tarih <= bitis
    ).order_by(Parti.created_at.desc()).all()

    # Tüketim özeti
    tuketim = {
        'PVC': 0, 'DOTP': 0, 'DOA': 0, 'ESBO': 0,
        'Antifog': 0, 'Stabilizer': 0, 'Slip': 0,
        'Pellet': 0, 'Kırma': 0
    }
    for parti in partiler:
        if parti.formul_snapshot:
            s = parti.formul_snapshot
            tuketim['PVC'] += s.get('pvc_kg', 0)
            tuketim['DOTP'] += s.get('dotp_kg', 0)
            tuketim['DOA'] += s.get('doa_kg', 0)
            tuketim['ESBO'] += s.get('esbo_kg', 0)
            tuketim['Antifog'] += s.get('antifog_kg', 0)
            tuketim['Stabilizer'] += s.get('stabilizer_kg', 0)
            tuketim['Slip'] += s.get('slip_kg', 0)
            tuketim['Pellet'] += s.get('pellet_kg', 0)
        if parti.kirma_tuketim_kg:
            tuketim['Kırma'] += parti.kirma_tuketim_kg

    toplam_tuketim = sum(tuketim.values())

    # Hammadde girişleri
    girisler = HammaddeGiris.query.filter(
        HammaddeGiris.tarih >= baslangic, HammaddeGiris.tarih <= bitis
    ).order_by(HammaddeGiris.created_at.desc()).all()

    return render_template('rapor.html',
                           partiler=partiler,
                           tuketim=tuketim,
                           toplam_tuketim=toplam_tuketim,
                           girisler=girisler,
                           baslangic=baslangic,
                           bitis=bitis)


@rapor_bp.route('/csv')
def csv_export():
    """Parti geçmişini CSV olarak dışa aktar."""
    baslangic_str = request.args.get('baslangic', '')
    bitis_str = request.args.get('bitis', '')

    try:
        baslangic = datetime.strptime(baslangic_str, '%Y-%m-%d').date() if baslangic_str else date.today() - timedelta(days=30)
    except ValueError:
        baslangic = date.today() - timedelta(days=30)
    try:
        bitis = datetime.strptime(bitis_str, '%Y-%m-%d').date() if bitis_str else date.today()
    except ValueError:
        bitis = date.today()

    partiler = Parti.query.filter(
        Parti.tarih >= baslangic, Parti.tarih <= bitis
    ).order_by(Parti.tarih, Parti.saat).all()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(['Parti No', 'Tarih', 'Saat', 'Formül', 'PVC (kg)', 'DOTP (kg)',
                     'DOA (kg)', 'ESBO (kg)', 'Antifog (kg)', 'Stabilizer (kg)',
                     'Slip (kg)', 'Pellet (kg)', 'Kırma (kg)', 'Toplam (kg)'])

    for p in partiler:
        s = p.formul_snapshot or {}
        writer.writerow([
            p.parti_no, p.tarih.strftime('%d.%m.%Y'), p.saat, p.formul_adi,
            s.get('pvc_kg', 0), s.get('dotp_kg', 0), s.get('doa_kg', 0),
            s.get('esbo_kg', 0), s.get('antifog_kg', 0), s.get('stabilizer_kg', 0),
            s.get('slip_kg', 0), s.get('pellet_kg', 0), p.kirma_tuketim_kg or 0,
            p.toplam_hammadde_kg
        ])

    dosya_adi = f"parti_raporu_{baslangic.strftime('%Y%m%d')}_{bitis.strftime('%Y%m%d')}.csv"
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={dosya_adi}'}
    )
