from dotenv import load_dotenv
import os

load_dotenv('.env')
DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
