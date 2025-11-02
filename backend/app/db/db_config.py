from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql://plts_puskesmas_tanah_toraja:QbzpW6ZrbA00fL7Orc3fy1rCknp0CL9h@localhost:5432/plts?options=-c search_path=dbo"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
sessionlocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()
