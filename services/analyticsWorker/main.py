import psycopg2
from database import claim_job, write_track_analytics, update_job_status
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
		worker = TrackProcessor()
		while True:
			job = claim_job(conn)
			if not job:
				time.sleep(15)
				logger.info("No jobs present")
				continue
			logger.info(f"Claimed job {job["id"]}")
			try:
				results = worker.process(job["file_path"], job["id"])
				write_track_analytics(
					conn, job["id"], 
					results["metadata"]["duration"],
					results["metadata"]["bpm"],
					results["embedding"]
				)
				logger.info(f"Successfully wrote {job["id"]} to db")
				update_job_status(conn, job["id"], "complete")
			except Exception as e:
				logger.error(f"Job {job["id"]} failed: {e}")
				sys.exit(1)
	except Exception as e:
		logger.error(f"Failed to connect to DB: {e}")
		sys.exit(1)


if __name__ == "__main__":
	main()
