"""
Ayarlar route — Sistem ayarları, silo kapasiteleri, yedekleme/geri yükleme.
"""
import os
import shutil
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from models import db, Ayar
from services.stok import parse_float, parse_int

ayarlar_bp = Blueprint('ayarlar', __name__)


@ayarlar_bp.route('/')
def index():
    """Ayarlar sayfası."""
    ayarlar = {a.anahtar: a for a in Ayar.query.all()}
    return render_template('ayarlar.html', ayarlar=ayarlar)


@ayarlar_bp.route('/kaydet', methods=['POST'])
def kaydet():
    """Sistem ayarlarını kaydet."""
    # Kırma akış hızı
    kirma_hiz = request.form.get('kirma_akis_hizi', '0.1')
    ayar = Ayar.query.filter_by(anahtar='kirma_akis_hizi').first()
    if ayar:
        ayar.deger = kirma_hiz
        ayar.updated_at = datetime.utcnow()
    else:
        db.session.add(Ayar(anahtar='kirma_akis_hizi', deger=kirma_hiz, aciklama='Kırma tankı akış hızı (kg/sn)'))

    # Haftalık Hedef Parti
    hedef_parti = request.form.get('haftalik_hedef_parti', '100')
    ayar_parti = Ayar.query.filter_by(anahtar='haftalik_hedef_parti').first()
    if ayar_parti:
        ayar_parti.deger = hedef_parti
        ayar_parti.updated_at = datetime.utcnow()
    else:
        db.session.add(Ayar(anahtar='haftalik_hedef_parti', deger=hedef_parti, aciklama='Haftalık hedeflenen üretim parti sayısı'))

    db.session.commit()
    flash('Ayarlar kaydedildi.', 'success')
    return redirect(url_for('ayarlar.index'))

@ayarlar_bp.route('/yedekle')
def yedekle():
    """Veritabanı dosyasını indir (yedekleme)."""
    db_path = os.path.join(current_app.root_path, 'instance', 'silo_takip.db')
    if os.path.exists(db_path):
        tarih = datetime.now().strftime('%Y%m%d_%H%M%S')
        return send_file(db_path, as_attachment=True,
                         download_name=f'silo_takip_yedek_{tarih}.db')
    flash('Veritabanı dosyası bulunamadı.', 'error')
    return redirect(url_for('ayarlar.index'))


@ayarlar_bp.route('/yukle', methods=['POST'])
def yukle():
    """Yedek veritabanı dosyasını yükle (geri yükleme)."""
    if 'db_file' not in request.files:
        flash('Dosya seçilmedi.', 'error')
        return redirect(url_for('ayarlar.index'))

    file = request.files['db_file']
    if file.filename == '':
        flash('Dosya seçilmedi.', 'error')
        return redirect(url_for('ayarlar.index'))

    if file and file.filename.endswith('.db'):
        db_path = os.path.join(current_app.root_path, 'instance', 'silo_takip.db')
        # Mevcut DB'yi yedekle
        if os.path.exists(db_path):
            tarih = datetime.now().strftime('%Y%m%d_%H%M%S')
            shutil.copy2(db_path, f'{db_path}.bak_{tarih}')
        file.save(db_path)
        flash('Veritabanı başarıyla geri yüklendi. Sayfayı yenileyin.', 'success')
    else:
        flash('Geçersiz dosya formatı. .db uzantılı dosya yükleyin.', 'error')

    return redirect(url_for('ayarlar.index'))
