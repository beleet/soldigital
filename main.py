from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from models import Base
import datetime
import gspread
from models import Supply, get_exchange_rates
import requests
import asyncio


# asynchronous function that updates information for every hour and saves it to the file
async def update_exchange_rates():
    while True:
        try:
            url = "https://www.cbr.ru/scripts/XML_daily.asp"
            response = requests.get(url=url)

            with open("exchange_rates.xml", "w") as file:
                file.write(response.text)
        except:
            pass

        await asyncio.sleep(60 * 60)


def get_engine(user, password, host, port, dbname):
    url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    if not database_exists(url):
        create_database(url)
    return create_engine(url, pool_size=50, echo=False)


engine = get_engine(user="postgres", dbname="soldigital", password="12345678", host="localhost", port="5432")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


def validate_time(date_text):
    try:
        datetime.datetime.strptime(date_text, '%d.%m.%Y')
        return True
    except:
        return False


service_account = gspread.service_account(filename="gspread/service_account2.json")
sheets = service_account.open("soldigital-test")
work_sheet = sheets.worksheet("Supply data")


# asynchronous function that updates or deletes values in database
async def database_update():
    while True:
        supplies = work_sheet.get(f"A2:H{work_sheet.row_count}")
        supplies_id = []

        for supply in supplies:
            if supply and len(supply) == 4:
                if supply[0].isdigit() and supply[1].isdigit() and supply[2].isdigit() and validate_time(supply[3]):

                    supplies_id.append(int(supply[0]))
                    row = session.query(Supply).get(supply[0])

                    if row is None:
                        new_row = Supply(*supply)
                        session.add(new_row)
                        session.commit()
                    else:
                        row.number = supply[1]
                        row.price = supply[2]
                        row.date_of_supply = supply[3]
                        row.price_in_rubles = float(supply[2]) * get_exchange_rates()
                        session.commit()

        all_rows = session.query(Supply).all()

        for db_row in all_rows:
            if db_row.id not in supplies_id:
                session.delete(db_row)
                session.commit()

        await asyncio.sleep(3)

io_loop = asyncio.get_event_loop()
tasks = [io_loop.create_task(update_exchange_rates()), io_loop.create_task(database_update())]
wait_tasks = asyncio.wait(tasks)
io_loop.run_until_complete(wait_tasks)
io_loop.close()
