from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import datetime

Base = declarative_base()

# defines a user
class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)
    picture = Column(String(250))

# defines a category
class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    items = relationship('Item', cascade="save-update, merge, delete")

    @property
    def serialize(self):
        return {
            'name': self.name,
            'id': self.id,
            'items': [i.serialize for i in self.items]
        }

# defines an item
class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    time_added = Column(DateTime, default=datetime.datetime.now())
    name = Column(String(50), nullable=False)
    description = Column(String(500), nullable=False)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return item data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
            'category': self.category.name,
            'description': self.description
        }

engine = create_engine('sqlite:///itemswithusers.db')

Base.metadata.create_all(engine)