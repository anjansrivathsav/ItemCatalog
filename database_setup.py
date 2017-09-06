from sqlalchemy import  Column,INTEGER,ForeignKey,String
from sqlalchemy.orm import relationship
from sqlalchemy.engine import  create_engine
from sqlalchemy.ext.declarative import declarative_base

#user class for the login users
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    name = Column(String(20),nullable=False)
    id = Column(INTEGER,primary_key = True)
    email = Column(String(20),nullable=False)

# Main catalog
class CatalogItem(Base):
    __tablename__ = 'catalogitems'
    id = Column(INTEGER,primary_key =True)
    name = Column(String(250),nullable=False)
    user_id = Column(INTEGER,ForeignKey('user.id'))
    user = relationship(User)


    @property
    def serialize(self):
        return {
            'name':self.name,
            'id':self.id
        }


class Items(Base):
    __tablename__ = 'items'
    id = Column(INTEGER,primary_key=True)
    name = Column(String(250),nullable=False)
    description =Column(String(250),nullable=False)
    user_id = Column(INTEGER,ForeignKey('user.id'))
    catalog_id = Column(INTEGER,ForeignKey('catalogitems.id'))
    user = relationship(User)
    catalogitems = relationship(CatalogItem)

    @property
    def serialize(self):
        return {
            'id':self.id,
            'name':self.name,
            'description':self.description,
            'catalog_id' :self.catalog_id
        }


engine = create_engine('sqlite:///catalogitems.db')

Base.metadata.create_all(engine)
