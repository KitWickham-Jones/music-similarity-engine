import psycopg2.extras
from worker import TrackProcessor
from dotenv import load_dotenv 
import logging
import sys
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

def claim_job(conn: psycopg2.extensions.connection) -> dict | None:
	with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
		cur.execute("""
			SELECT id, file_path FROM jobs
			WHERE status = 'pending'
			ORDER BY created_at
			LIMIT 1
			FOR UPDATE SKIP LOCKED
		""")
		return cur.fetchone()

def main():
	try:
		logger.info("Worker started, connecting to DB")
		load_dotenv()
		db_url = os.getenv("DATABASE_URL")
		conn = psycopg2.connect(db_url)
		logger.info("DB Connection succesfull. Checking jobs")
		job = claim_job(conn)
		logger.info(f"Job claimed: {job["id"]} location: {job["file_path"]}")
	except Exception as e:
		logger.error(f"Failed to connect to DB: {e}")
		sys.exit(1)


if __name__ == "__main__":
	main()
