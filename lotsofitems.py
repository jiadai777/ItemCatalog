from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import random
import string
from database_setup import User, Base, Item
from datetime import datetime

"""
######################### WARNING #########################
RUNNING THIS FILE WILL DELETE ALL THE DATABASE ITEMS YOU HAVE
AND CREATE 20 ITEMS WITH RANDOM NAMES, DESCRIPTIONS, AND
CATEGORIES.

This program is intended for quick test of the main.py and its
templates and websites. You do not have to run this program in
order to visit the Item Catalog website.
"""

engine = create_engine('sqlite:///itemswithusers.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

session.query(Item).delete()
session.commit()

# generate 20 random items
categories = ["soccer", "basketball", "baseball", "frisbee",
			"snowboarding", "rockclimbing", "football",
			"skating", "hockey"]

for x in xrange(20):
	name = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(5))
	description = ''.join(random.choice(string.ascii_lowercase + string.digits)
                    for x in xrange(200))
	cate = categories[random.randint(0, len(categories) - 1)]
	item = Item(name=name, category=cate, user_id=x,
				description=description)
	session.add(item)
	session.commit()


print "items added!"