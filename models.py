from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, Float, String
import xml.etree.ElementTree as ET


def get_exchange_rates():

    tree = ET.parse("exchange_rates.xml")
    root = tree.getroot()

    for child in root:
        if child.attrib['ID'] == "R01235":
            for parameter in child:
                if parameter.tag == "Value":
                    return float(parameter.text.replace(",", "."))


Base = declarative_base()


class Supply(Base):

    __tablename__ = "supply"

    def __init__(self, id, number, price, date_of_supply):
        try:
            self.id = int(id)
            self.number = int(number)
            self.price = float(price)
            self.price_in_rubles = float(price) * get_exchange_rates()
            self.date_of_supply = str(date_of_supply)
        except ValueError:
            print("Invalid data")
        except Exception as exc:
            print(exc)

    id = Column("№", Integer, primary_key=True)
    number = Column("заказ №", Integer, nullable=False)
    price = Column("стоимость,$", Float, nullable=False)
    price_in_rubles = Column("стоимость в руб.", Float, nullable=False)
    date_of_supply = Column("срок поставки", String, nullable=False)
