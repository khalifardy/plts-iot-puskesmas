# app/db/models/__init__.py
from app.db.db_config import Base, engine
from sqlalchemy import text, inspect

def create_tables():
    # Periksa apakah schema dbo sudah ada
    with engine.connect() as conn:
        inspector = inspect(engine)
        if 'dbo' not in inspector.get_schema_names():
            # Buat schema dbo jika belum ada
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS dbo;"))
            conn.commit()
            print("Schema 'dbo' berhasil dibuat")
    
    # Import model setelah memastikan schema ada
    from app.db.models.user import User, Profile
    
    # Buat tabel di schema dbo
    Base.metadata.create_all(bind=engine)
    print("Tabel berhasil dibuat di schema 'dbo'")

# Export model harus berada setelah create_tables (untuk menghindari import siklik)
__all__ = ["create_tables"]