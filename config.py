from dotenv import load_dotenv
import os
import sqlalchemy

load_dotenv('.env')
DATABASE_URI = f"postgresql+psycopg2://{os.environ.get('DATABASE_URL')}"
engine: sqlalchemy.engine = \
    sqlalchemy.create_engine(DATABASE_URI, echo=True)
