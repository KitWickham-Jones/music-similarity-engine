import psycopg2.extras

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
	
def write_track_analytics(conn: psycopg2.extensions.connection, job_id : str, duation: float, bpm: float, embedding ) -> bool:
	with conn.cursor() as cur:
		cur.execute("""
			INSERT INTO tracks (job_id, duration, bpm, embedding)
			VALUES (%s, %s, %s, %s)
		""",(job_id, duation, bpm, embedding))
		return conn.commit()
