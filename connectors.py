import os
from dotenv import load_dotenv

load_dotenv(".env.local")

DRIVER=os.environ.get('DRIVER')
SERVER=os.environ.get('SERVER')
DATABASE=os.environ.get('DATABASE')
USERNAME=os.environ.get('USERNAME')
PASSWORD=os.environ.get('PASSWORD')

dbconnectionString = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}'