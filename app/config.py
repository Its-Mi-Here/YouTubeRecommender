import os
from dotenv import load_dotenv


load_dotenv()

CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', None)
CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', None)
API_KEY = os.environ.get('GOOGLE_API_KEY')