import psycopg2.extras
import select
class ListenerDatabase:
	def __init__(self, conn: psycopg2.extensions.connection):
		self.conn = conn
		#auto init the consumer
		with self.conn.cursor() as cur:
			cur.execute("LISTEN job_ready")
	
	def wait_for_job(self):
		# putting this in a loop to permit multithreading ()
		# librosa + CLAP are just wrappers for C processes meaning you can spawn multiple
		# threads, as when they go into c prcesses the GIL is free
		while True:	
			#check for pending jobs before blocking
			job = self.claim_job()
			if job is not None:
				return job
			#this blocks until activity occurs on the connection (this must be specific to the worker)
			#(system call magic)
			select.select([self.conn], [], [])
			# literally just cleanup function, could jump straight into claiming the job but then messages accumulate in the buffer
			self.conn.poll()
			#poll -> notices which can then be cleared
			self.conn.notifies.clear()
			#actual job is claimed by going back to the top and also drains job buffer
	
	def claim_job(self):
		with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
			cur.execute("""
				SELECT id, file_path FROM jobs
				WHERE status = 'pending'
				ORDER BY created_at
				LIMIT 1
				FOR UPDATE SKIP LOCKED
			""")
			return cur.fetchone()
	
class WorkerDatabase:
	def __init__(self, conn: psycopg2.extensions.connection):
		self.conn = conn
	
	def register_worker(self, worker_uuid: str):
		with self.conn.cursor() as cur:
			cur.execute("""
				INSERT INTO workers (id)
				VALUES (%s)
			""",(worker_uuid,))
	
	def set_worker_job(self, worker_uuid: str, current_job):
		with self.conn.cursor() as cur:
			cur.execute("UPDATE workers SET current_job_id = %s, status = 'processing' WHERE id = %s",
				(current_job, worker_uuid))
	
	def clear_worker_job(self, worker_uuid: str):
		with self.conn.cursor() as cur:
			cur.execute("UPDATE workers SET current_job_id = NULL, status = 'idle' WHERE id = %s",
			   (worker_uuid,))
	
	def write_track_analytics(self, job_id:str, duration: float, bpm: float, embedding: list[float]  ):
		with self.conn.cursor() as cur:
			cur.execute("""
				INSERT INTO tracks (job_id, duration, bpm, embedding)
				VALUES (%s, %s, %s, %s)
			""",(job_id, duration, bpm, embedding))
	
	def update_job_status(self, job_id:str, status: str):
		with self.conn.cursor() as cur:
			cur.execute("UPDATE jobs SET status = %s WHERE id = %s",
				(status, job_id))

	#this is called on a non-autocommiting connection
	def worker_heartbeat(self, worker_uuid: str):
		with self.conn.cursor() as cur:
			cur.execute("UPDATE workers SET last_heartbeat = NOW() WHERE id = %s",
				(worker_uuid,))
			self.conn.commit()
