import threading
import psycopg2
from database import Database
from worker import TrackProcessor
import logging
import sys

logger = logging.getLogger(__name__)

def worker_loop(db_url: str , worker: TrackProcessor):
	try:
		thread_name = threading.current_thread().name
		conn = psycopg2.connect(db_url)
		logger.info(f"{thread_name} Connected to DB")
		database = Database(conn)
		while True:
			job = database.wait_for_job()
			logger.info(f"{thread_name} claimed job {job["id"]}")
			database.update_job_status(job["id"], "processing")
			try:
				results = worker.process(job["file_path"], job["id"])
				database.write_track_analytics(
					job["id"],
					results["metadata"]["duration"],
					results["metadata"]["bpm"],
					results["embedding"]
				)
				logger.info(f"Succesfully wrote {job["id"]} to db")
				database.update_job_status(job["id"], "complete")

			except Exception as e:
				logger.error(f"Job {job["id"]} failed: {e}")

	except Exception as e:
		logger.error(f"{thread_name} Failed to connect to DB: {e}")
		sys.exit(1)

def start_pool(db_url: str, num_workers: int):
	processor = TrackProcessor()
	threads = [
		threading.Thread(target=worker_loop, args=(db_url, processor), name=f"worker-{i}", daemon=True)
		for i in range(num_workers)
	]
	for t in threads:
		t.start()
	for t in threads:
		t.join()


