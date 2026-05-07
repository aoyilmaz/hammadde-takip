"""
Formül yönetimi route — Mikser formüllerinin CRUD işlemleri.
"""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Formul

formul_bp = Blueprint('formul', __name__)


@formul_bp.route('/')
def index():
    """Formül listesi."""
    formuller = Formul.query.filter_by(aktif=True).order_by(Formul.varsayilan.desc(), Formul.ad).all()
    return render_template('formul.html', formuller=formuller)


@formul_bp.route('/kaydet', methods=['POST'])
def kaydet():
    """Yeni formül kaydet veya mevcut formülü güncelle."""
    formul_id = request.form.get('formul_id')
    if formul_id:
        formul = Formul.query.get_or_404(int(formul_id))
        flash_msg = f'"{formul.ad}" formülü güncellendi.'
    else:
        formul = Formul()
        db.session.add(formul)
        flash_msg = 'Yeni formül oluşturuldu.'

    formul.ad = request.form.get('ad', 'İsimsiz Formül')
    formul.pvc_kg = float(request.form.get('pvc_kg', 0) or 0)
    formul.dotp_kg = float(request.form.get('dotp_kg', 0) or 0)
    formul.doa_kg = float(request.form.get('doa_kg', 0) or 0)
    formul.esbo_kg = float(request.form.get('esbo_kg', 0) or 0)
    formul.antifog_kg = float(request.form.get('antifog_kg', 0) or 0)
    formul.stabilizer_kg = float(request.form.get('stabilizer_kg', 0) or 0)
    formul.slip_kg = float(request.form.get('slip_kg', 0) or 0)
    formul.pellet_kg = float(request.form.get('pellet_kg', 0) or 0)
    formul.kirma_sure_sn = float(request.form.get('kirma_sure_sn', 0) or 0)
    formul.updated_at = datetime.utcnow()

    varsayilan = request.form.get('varsayilan') == 'on'
    if varsayilan:
        Formul.query.filter(Formul.id != formul.id).update({'varsayilan': False})
        formul.varsayilan = True
    else:
        formul.varsayilan = False

    db.session.commit()
    flash(flash_msg, 'success')
    return redirect(url_for('formul.index'))


@formul_bp.route('/sil/<int:formul_id>', methods=['POST'])
def sil(formul_id):
    """Formülü pasif yap (soft delete)."""
    formul = Formul.query.get_or_404(formul_id)
    formul.aktif = False
    formul.updated_at = datetime.utcnow()
    db.session.commit()
    flash(f'"{formul.ad}" formülü silindi.', 'success')
    return redirect(url_for('formul.index'))


@formul_bp.route('/kopyala/<int:formul_id>', methods=['POST'])
def kopyala(formul_id):
    """Mevcut formülü kopyalayarak yeni formül oluştur."""
    kaynak = Formul.query.get_or_404(formul_id)
    yeni = Formul(
        ad=f'{kaynak.ad} (Kopya)', pvc_kg=kaynak.pvc_kg, dotp_kg=kaynak.dotp_kg,
        doa_kg=kaynak.doa_kg, esbo_kg=kaynak.esbo_kg, antifog_kg=kaynak.antifog_kg,
        stabilizer_kg=kaynak.stabilizer_kg, slip_kg=kaynak.slip_kg,
        pellet_kg=kaynak.pellet_kg, kirma_sure_sn=kaynak.kirma_sure_sn,
        varsayilan=False, aktif=True
    )
    db.session.add(yeni)
    db.session.commit()
    flash(f'"{kaynak.ad}" formülü kopyalandı.', 'success')
    return redirect(url_for('formul.index'))
