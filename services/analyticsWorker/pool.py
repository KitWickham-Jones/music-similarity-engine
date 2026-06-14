import threading
import psycopg2
from database import ListenerDatabase, WorkerDatabase
from worker import TrackProcessor
import logging
import sys
import uuid
import time

logger = logging.getLogger(__name__)

#propagate reference to job id via a list, lists are mutable
#and therefore var names are actual references to the mem location
#so when i update a list and pass it to the loop, i can update from the other
#thread. memorymogged
def heartbeat_loop(db_url: str, worker_id: str, current_job: list):
	try:
		conn = psycopg2.connect(db_url)
		logger.info(f"Heartbeat:{worker_id[:8]} connected to database.")
		heartbeat_db = WorkerDatabase(conn)
		while True:
			if current_job[0] is not None:
				heartbeat_db.worker_heartbeat(worker_id)
			time.sleep(5)
	except psycopg2.OperationalError as e:
		logger.error(f"Heartbeat:{worker_id[:8]} failed to connect to database: {e}. Exiting entire thread pool.")
		sys.exit(1)

def worker_loop(db_url: str, worker: TrackProcessor):
	try:
		worker_id = str(uuid.uuid4())
		conn = psycopg2.connect(db_url)
		logger.info(f"{worker_id[:8]} Connected to DB")
		#autocommiting mainly for creating consumer to listen/notify
		conn.set_isolation_level(0)
		worker_db = WorkerDatabase(conn)
		worker_db.register_worker(worker_id)
		listener_db = ListenerDatabase(conn)
		#current job can be mutated by worker thread which propagates to heartbeat thread
		current_job = [None]
		hb = threading.Thread(target=heartbeat_loop, args=(db_url, worker_id, current_job), daemon=True)
		hb.start()
		while True:
			job = listener_db.wait_for_job()
			#send to heartbeat thread
			current_job[0] = job["id"]
			worker_db.set_worker_job(worker_id, job["id"])
			logger.info(f"worker_id:{worker_id[:8]} claimed job {job["id"]}")
			worker_db.update_job_status(job["id"], 'processing')
			try:
				results = worker.process(job["file_path"], job["id"])
				worker_db.write_track_analytics(
					job["id"],
					results["metadata"]["duration"],
					results["metadata"]["bpm"],
					results["embedding"]
				)
				logger.info(f"Succesfully wrote {job["id"]} to db")
				worker_db.update_job_status(job["id"], 'complete')
				worker_db.clear_worker_job(worker_id)
				current_job[0] = None

			except Exception as e:
				logger.error(f"Job {job["id"]} failed: {e}")
				worker_db.clear_worker_job(worker_id)
				current_job[0] = None
	
	except psycopg2.OperationalError as e:
		logger.error(f"{worker_id[:8]} Failed to connect to database: {e}. Exiting entire thread pool.")
		#sys exit kills entire thread pool
		sys.exit(1)
	
	except psycopg2.DatabaseError as e:
		logger.error(f"{worker_id[:8]} Failed to register as worker: {e}. Exiting entire thread pool.")
		sys.exit(1)
	

def start_pool(db_url: str, num_workers: int):
	processor = TrackProcessor()
	#daemon allows for kill switch from main thread
	threads = [
		threading.Thread(target=worker_loop, args=(db_url, processor), daemon=True)
		for _ in range(num_workers)
	]
	for t in threads:
		t.start()
	for t in threads:
		t.join()


