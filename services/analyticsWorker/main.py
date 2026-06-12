from pool import start_pool
from dotenv import load_dotenv 
import logging

import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

def main():
	load_dotenv()
	db_url = os.getenv("DATABASE_URL")
	start_pool(db_url, 2)

if __name__ == "__main__":
	main()
