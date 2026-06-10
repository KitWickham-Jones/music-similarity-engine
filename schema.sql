CREATE EXTENSION IF NOT EXISTS vector;
CREATE TYPE job_status AS ENUM ('pending', 'processing', 'complete', 'failed');
CREATE TYPE worker_status AS ENUM ('idle', 'processing');

CREATE TABLE IF NOT EXISTS jobs(
	id UUID PRIMARY KEY,
	status job_status NOT NULL DEFAULT 'pending',
	file_path TEXT NOT NULL,
	track_title TEXT,
	created_at TIMESTAMPTZ DEFAULT NOW(),
	updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tracks(
	id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
	job_id UUID REFERENCES jobs(id),
	artist TEXT,
	duration FLOAT,
	bpm FLOAT,
	embedding vector(512),
	created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS workers(
	id UUID PRIMARY KEY,
	last_heartbeat TIMESTAMPTZ DEFAULT NOW(),
	current_job_id UUID REFERENCES jobs(id),
	status worker_status NOT NULL DEFAULT 'idle'
);


CREATE OR REPLACE FUNCTION notify_job_ready()
RETURNS trigger AS $$
BEGIN
	PERFORM pg_notify('job_ready', NEW.id::text);
	RETURN NEW;
END;

$$ LANGUAGE plpgsql;

CREATE TRIGGER job_insert_notify
AFTER INSERT ON jobs
FOR EACH ROW EXECUTE FUNCTION notify_job_ready();
