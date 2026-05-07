from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Tedarikci, TedarikciHammadde, Silo

tedarikci_bp = Blueprint('tedarikci', __name__)

@tedarikci_bp.route('/')
def index():
    """Tedarikçi listesi ve ekleme formu."""
    tedarikciler = Tedarikci.query.filter_by(aktif=True).order_by(Tedarikci.ad).all()
    
    # Mevcut hammadde tipleri (Silo'daki tiplere göre + PVC)
    silolar = db.session.query(Silo.hammadde_tipi).distinct().all()
    hammadde_tipleri = sorted(list(set([s[0] for s in silolar] + ['PVC'])))
    
    return render_template('tedarikci.html', tedarikciler=tedarikciler, hammadde_tipleri=hammadde_tipleri)

@tedarikci_bp.route('/ekle', methods=['POST'])
def ekle():
    """Yeni tedarikçi kaydet."""
    tedarikci_id = request.form.get('tedarikci_id')
    
    if tedarikci_id:
        tedarikci = Tedarikci.query.get_or_404(int(tedarikci_id))
        flash_msg = f'"{tedarikci.ad}" başarıyla güncellendi.'
    else:
        tedarikci = Tedarikci()
        db.session.add(tedarikci)
        flash_msg = 'Yeni tedarikçi başarıyla eklendi.'

    tedarikci.ad = request.form.get('ad', 'İsimsiz Tedarikçi')
    tedarikci.iletisim_kisi = request.form.get('iletisim_kisi', '')
    tedarikci.telefon = request.form.get('telefon', '')
    tedarikci.eposta = request.form.get('eposta', '')
    tedarikci.notlar = request.form.get('notlar', '')
    
    # Eski eşleştirmeleri sil
    if tedarikci_id:
        TedarikciHammadde.query.filter_by(tedarikci_id=tedarikci.id).delete()
        
    db.session.commit() # id'yi almak için
    
    # Yeni eşleştirmeleri ekle
    secilen_hammaddeler = request.form.getlist('hammadde_tipleri')
    for ht in secilen_hammaddeler:
        kodu = request.form.get(f'urun_kodu_{ht}', '')
        eslesme = TedarikciHammadde(tedarikci_id=tedarikci.id, hammadde_tipi=ht, urun_kodu=kodu)
        db.session.add(eslesme)
        
    db.session.commit()
    flash(flash_msg, 'success')
    return redirect(url_for('tedarikci.index'))

@tedarikci_bp.route('/sil/<int:tedarikci_id>', methods=['POST'])
def sil(tedarikci_id):
    """Tedarikçiyi pasif yap (soft delete)."""
    tedarikci = Tedarikci.query.get_or_404(tedarikci_id)
    tedarikci.aktif = False
    db.session.commit()
    flash(f'"{tedarikci.ad}" silindi.', 'success')
    return redirect(url_for('tedarikci.index'))
