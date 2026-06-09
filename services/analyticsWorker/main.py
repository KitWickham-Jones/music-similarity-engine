import psycopg2
from database import Database
from worker import TrackProcessor
from dotenv import load_dotenv 
import logging
import sys
import os
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

def main():
	try:
		logger.info("Worker started, connecting to DB")
		load_dotenv()
		db_url = os.getenv("DATABASE_URL")
		conn = psycopg2.connect(db_url)
		logger.info("DB Connection succesfull.")
		database = Database(conn)
		worker = TrackProcessor()
		while True:
			job = database.claim_job()
			if not job:
				time.sleep(15)
				logger.info("No jobs present")
				continue
			logger.info(f"Claimed job {job["id"]}")
			try:
				results = worker.process(job["file_path"], job["id"])
				database.write_track_analytics(
					job["id"],
					results["metadata"]["duration"],
					results["metadata"]["bpm"],
					results["embedding"]
				)
				logger.info(f"Successfully wrote {job["id"]} to db")
				database.update_job_status(job["id"], "complete")
			except Exception as e:
				logger.error(f"Job {job["id"]} failed: {e}")
				sys.exit(1)
	except Exception as e:
		logger.error(f"Failed to connect to DB: {e}")
		sys.exit(1)


if __name__ == "__main__":
	main()
