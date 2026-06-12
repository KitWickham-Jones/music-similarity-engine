import psycopg2.extras
import select

class Database:
	def __init__(self, conn: psycopg2.extensions.connection):
		self.conn = conn
		self.conn.set_isolation_level(0)
		
		#auto init the consumer
		with self.conn.cursor() as cur:
			cur.execute("LISTEN job_ready")
	
	
	def wait_for_job(self):
		# putting this in a loop to permit multithreading ()
		# librosa + CLAP are just wrappers for C processes meaning you can spawn multiple
		# threads, as when they go into c prcesses the GIL is free
		while True:	
			#this blocks until activity occurs on the connection (this must be specific to the worker)
			#(system call magic)
			select.select([self.conn], [], [])
			# literally just cleanup function, could jump straight into claiming the job but then messages accumulate in the buffer
			self.conn.poll()
			#poll -> notices which can then be cleared
			self.conn.notifies.clear()
			#actual job is claimed
			job = self.claim_job()
			if job is not None:
				return job

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
	
	def write_track_analytics(self, job_id:str, duration: float, bpm: float, embedding: list[float]  ):
		with self.conn.cursor() as cur:
			cur.execute("""
				INSERT INTO tracks (job_id, duration, bpm, embedding)
				VALUES (%s, %s, %s, %s)
			""",(job_id, duration, bpm, embedding))
			self.conn.commit()
	
	def update_job_status(self, job_id:str, status: str):
		with self.conn.cursor() as cur:
			cur.execute("UPDATE jobs SET status = %s WHERE id = %s",
				(status, job_id))
			self.conn.commit()
