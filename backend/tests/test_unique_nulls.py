from sqlalchemy import create_engine, Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

class TestModel(Base):
    __tablename__ = 'test_unique_nulls'
    id = Column(Integer, primary_key=True)
    val = Column(String, unique=True, nullable=True)

def test():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        print("Inserting First NULL...")
        db.add(TestModel(id=1, val=None))
        db.commit()
        print("Success.")
        
        print("Inserting Second NULL...")
        db.add(TestModel(id=2, val=None))
        db.commit()
        print("Success! SQLite supports multiple NULLs in unique column.")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test()
