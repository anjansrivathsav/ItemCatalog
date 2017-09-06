from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import User,CatalogItem,Items,Base


engine = create_engine('sqlite:///catalogitems.db')

Base.metadata.bind = engine

DBsession = sessionmaker(bind=engine)

session = DBsession()


User1 = User(name ="anjan",email = "anjansrivathsav1997@gmail.com")
session.add(User1)
session.commit()


CatalogItem1 = CatalogItem(name = "badminton",user_id = 1)
session.add(CatalogItem1)
session.commit()


CatalogItem2 = CatalogItem(name = "cricket",user_id = 1)
session.add(CatalogItem2)
session.commit()

CatalogItem3 = CatalogItem(name = "football",user_id = 1)
session.add(CatalogItem3)
session.commit()



Item1 = Items(name = "shettil",description = "to play the badminton",user_id = 1,catalog_id =1)
session.add(Item1)
session.commit()


Item2 = Items(name = "shettilbat",description = "to play with shettil",user_id =1,catalog_id =1)
session.add(Item2)
session.commit()


Item3 = Items(name = "ball",description = "to play the cricket",user_id = 1,catalog_id =2)
session.add(Item3)
session.commit()

Item4 = Items(name = "bat",description = "to play with ball",user_id = 1,catalog_id =2)
session.add(Item4)
session.commit()


Item5= Items(name = "football",description = "to play football",user_id = 1,catalog_id =3)
session.add(Item5)
session.commit()

Item6 = Items(name = "nets",description = "to play with football",user_id = 1,catalog_id = 3)
session.add(Item6)
session.commit()



print "items are added"



























