from pool import start_process
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
	if db_url is None:
		raise ValueError("DATABASE_URL environment var not set")
	start_process(db_url, 2, 2)

if __name__ == "__main__":
	main()
