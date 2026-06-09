import psycopg2.extras

class Database:
	def __init__(self, conn: psycopg2.extensions.connection):
		self.conn = conn
	
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
	
	def write_track_analytics(self, job_id:str, duation: float, bpm: float, embedding: list[float]  ):
		with self.conn.cursor() as cur:
			cur.execute("""
				INSERT INTO tracks (job_id, duration, bpm, embedding)
				VALUES (%s, %s, %s, %s)
			""",(job_id, duation, bpm, embedding))
			self.conn.commit()
	
	def update_job_status(self, job_id:str, status: str):
		with self.conn.cursor() as cur:
			cur.execute("UPDATE jobs SET status = %s WHERE id = %s",
				(status, job_id))
			self.conn.commit()
