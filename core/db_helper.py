from contextlib import contextmanager
from core.database import SessionLocal

@contextmanager
def get_db_session():
    """
    Flet olaylarında (event handlers) ve masaüstü uygulamasında veritabanı işlemlerini 
    güvenli bir şekilde yönetmek için Context Manager.
    """
    db = SessionLocal()
    try:
        # Session'ı çağrıldığı yere (with bloğunun içine) ver
        yield db
        
        # Eğer okuma/yazma işlemi hatasız bittiyse değişiklikleri kaydet
        db.commit()
    except Exception as e:
        # Bir hata olduysa değişiklikleri geri al (rollback)
        db.rollback()
        # Hatayı UI katmanında yakalamak için fırlat
        raise e
    finally:
        # İşlem ne olursa olsun session'ı kesinlikle kapat
        db.close()
