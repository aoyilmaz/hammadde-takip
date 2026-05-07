"""
Uygulama konfigürasyon ayarları.
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Flask uygulama konfigürasyonu."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'silo-takip-gizli-anahtar-2026')
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'silo_takip.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
