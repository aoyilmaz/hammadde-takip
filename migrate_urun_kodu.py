import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'silo_takip.db')

def migrate():
    if not os.path.exists(db_path):
        print("Veritabanı bulunamadı:", db_path)
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if urun_kodu column already exists
        cursor.execute("PRAGMA table_info(tedarikci_hammadde)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'urun_kodu' not in columns:
            cursor.execute("ALTER TABLE tedarikci_hammadde ADD COLUMN urun_kodu VARCHAR(100)")
            print("Migration başarılı: 'urun_kodu' sütunu 'tedarikci_hammadde' tablosuna eklendi.")
        else:
            print("'urun_kodu' sütunu 'tedarikci_hammadde' tablosunda zaten mevcut.")

        # Check hammadde_giris table
        cursor.execute("PRAGMA table_info(hammadde_giris)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'urun_kodu' not in columns:
            cursor.execute("ALTER TABLE hammadde_giris ADD COLUMN urun_kodu VARCHAR(100)")
            print("Migration başarılı: 'urun_kodu' sütunu 'hammadde_giris' tablosuna eklendi.")
        else:
            print("'urun_kodu' sütunu 'hammadde_giris' tablosunda zaten mevcut.")

        # Check pvc_stok table
        cursor.execute("PRAGMA table_info(pvc_stok)")
        columns = [info[1] for info in cursor.fetchall()]
        if 'urun_kodu' not in columns:
            cursor.execute("ALTER TABLE pvc_stok ADD COLUMN urun_kodu VARCHAR(100) DEFAULT 'Standart'")
            print("Migration başarılı: 'urun_kodu' sütunu 'pvc_stok' tablosuna eklendi.")
        else:
            print("'urun_kodu' sütunu 'pvc_stok' tablosunda zaten mevcut.")
            
        conn.commit()
    except Exception as e:
        print("Hata oluştu:", e)
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
