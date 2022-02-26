from dotenv import load_dotenv
import os
import sqlalchemy

load_dotenv('.env')
DATABASE_URI = os.environ.get('DATABASE_URL').replace("s://", "sql://", 1)
engine: sqlalchemy.engine = \
    sqlalchemy.create_engine(DATABASE_URI, echo=True)
