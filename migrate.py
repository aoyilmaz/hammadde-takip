import os
import sqlite3
from app import app
from models import db

def migrate():
    # Create new tables (Tedarikci, TedarikciHammadde, GeriDonusBigbagStok, SayimFisi, SayimDetay)
    with app.app_context():
        db.create_all()

    # Add columns to existing tables using raw SQLite since Flask-Migrate is not setup
    db_path = os.path.join(app.root_path, 'instance', 'silo_takip.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('ALTER TABLE hammadde_giris ADD COLUMN tedarikci_id INTEGER REFERENCES tedarikciler(id);')
        print("Added tedarikci_id to hammadde_giris")
    except sqlite3.OperationalError as e:
        print(f"hammadde_giris alter error (might exist): {e}")

    try:
        cursor.execute('ALTER TABLE formuller ADD COLUMN ekstra_bilesenler JSON;')
        print("Added ekstra_bilesenler to formuller")
    except sqlite3.OperationalError as e:
        print(f"formuller alter error (might exist): {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == '__main__':
    migrate()
