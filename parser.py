import sqlite3
from tqdm import tqdm
from dotenv import load_dotenv
import os

load_dotenv()

owner = os.getenv('OWNER')