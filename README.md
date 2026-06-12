# Music Similarity Engine

A distributed audio analysis engine for DnB/jungle music. Upload an MP3, extract audio features, and find sonically similar tracks from a corpus.

## What it does

1. Client uploads an MP3 via the Go API
2. Go saves the file to disk and inserts a job into PostgreSQL
3. A PostgreSQL trigger fires `NOTIFY job_ready` on the jobs channel
4. Python workers wake up, race to claim the job via `SELECT FOR UPDATE SKIP LOCKED`
5. The winning worker runs CLAP inference and librosa feature extraction
6. Results (BPM, duration, 512-dimension embedding) are written back to PostgreSQL

## Stack

| Layer | Technology |
|---|---|
| API | Go (net/http, pgx) |
| Audio analysis | Python (CLAP, librosa, torchaudio) |
| Database | PostgreSQL + pgvector |
| Infrastructure | Docker Compose |

## Architecture

```
Client
  ↓  POST /tracks/upload (multipart MP3)
Go API server
  ↓  INSERT INTO jobs
PostgreSQL
  ↓  NOTIFY job_ready (trigger)
Python worker pool (N threads)
  ↓  SELECT FOR UPDATE SKIP LOCKED
  ↓  CLAP inference + librosa BPM
  ↓  INSERT INTO tracks (embedding, bpm, duration)
PostgreSQL (pgvector)
```

## API

| Method | Endpoint | Description |
|---|---|---|
| POST | `/tracks/upload` | Upload an MP3, returns job ID |
| GET | `/jobs/:id` | Poll job status |

### Upload a track
```bash
curl -X POST http://localhost:8080/tracks/upload \
  -F "audio=@track.mp3"
# {"job_id": "...", "track_title": "track", "filepath": "/tmp/uploads/track.mp3"}
```

### Poll job status
```bash
curl http://localhost:8080/jobs/<job_id>
# {"job_id": "...", "status": "complete"}
```

## Database schema

```sql
jobs    — job lifecycle (pending → processing → complete/failed)
tracks  — extracted features + 512-dim CLAP embedding
workers — heartbeat tracking for worker health (not yet implemented)
```

A PostgreSQL trigger on `jobs` INSERT fires `pg_notify('job_ready', job_id)` — workers block on this channel rather than polling.

## Worker pool

Workers use Python threads rather than processes. CLAP and librosa are C/C++ extensions that release the GIL during inference, so threads get real parallelism without the memory cost of loading the CLAP model (~500MB) once per process.

Each thread owns its own PostgreSQL connection and `LISTEN`s on `job_ready` independently. `FOR UPDATE SKIP LOCKED` ensures only one thread claims each job — no application-level locking needed.

```
Thread 0: LISTEN job_ready → claim job → CLAP inference (GIL released) → write results
Thread 1: LISTEN job_ready → claim job → CLAP inference (GIL released) → write results
```

## Running locally

```bash
# start PostgreSQL
docker compose up -d

# start Go API
cd services/queueServer
go run cmd/api/main.go

# start Python workers
cd services/analyticsWorker
python main.py
```

Requires a `.env` file with `DATABASE_URL`.
