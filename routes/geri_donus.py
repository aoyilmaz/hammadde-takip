"""
Geri dönüşüm route — Kırma ve pellet tankı giriş/takip.
"""
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Silo, GeriDonusGiris

geri_donus_bp = Blueprint('geri_donus', __name__)


@geri_donus_bp.route('/')
def index():
    """Geri dönüşüm sayfası — tank durumu ve giriş geçmişi."""
    kirma_tank = Silo.query.filter_by(hammadde_tipi='Kırma').first()
    pellet_tank = Silo.query.filter_by(hammadde_tipi='Pellet').first()
    girisler = GeriDonusGiris.query.order_by(GeriDonusGiris.created_at.desc()).limit(20).all()

    return render_template('geri_donus.html',
                           kirma_tank=kirma_tank,
                           pellet_tank=pellet_tank,
                           girisler=girisler)


@geri_donus_bp.route('/ekle', methods=['POST'])
def ekle():
    """Geri dönüşüm tankına giriş kaydet."""
    tank_tipi = request.form.get('tank_tipi')
    miktar_kg = float(request.form.get('miktar_kg', 0) or 0)
    notlar = request.form.get('notlar', '')
    tarih_str = request.form.get('tarih', '')

    try:
        tarih = datetime.strptime(tarih_str, '%Y-%m-%d').date() if tarih_str else date.today()
    except ValueError:
        tarih = date.today()

    if miktar_kg <= 0:
        flash('Miktar 0\'dan büyük olmalıdır.', 'error')
        return redirect(url_for('geri_donus.index'))

    if tank_tipi not in ('kirma', 'pellet'):
        flash('Geçersiz tank tipi.', 'error')
        return redirect(url_for('geri_donus.index'))

    # Tank güncelle
    hammadde_tipi = 'Kırma' if tank_tipi == 'kirma' else 'Pellet'
    tank = Silo.query.filter_by(hammadde_tipi=hammadde_tipi).first()
    if tank:
        tank.mevcut_kg += miktar_kg
        tank.updated_at = datetime.utcnow()

    # Giriş kaydı
    giris = GeriDonusGiris(
        tank_tipi=tank_tipi,
        miktar_kg=miktar_kg,
        tarih=tarih,
        notlar=notlar
    )
    db.session.add(giris)
    db.session.commit()

    tank_adi = 'Kırma Tankı' if tank_tipi == 'kirma' else 'Pellet Tankı'
    flash(f'{tank_adi} → {miktar_kg} kg giriş yapıldı.', 'success')
    return redirect(url_for('geri_donus.index'))
