from dotenv import load_dotenv
import os
import sqlalchemy

load_dotenv('.env')
DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
engine: sqlalchemy.engine = \
    sqlalchemy.create_engine(DATABASE_URI, echo=True)
