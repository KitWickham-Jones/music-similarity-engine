package db

import (
	"github.com/jackc/pgx/v5/pgxpool"
	"context"
)
type Store struct{
	postgres *pgxpool.Pool
}

func New (db *pgxpool.Pool) *Store{
	return &Store{
		postgres : db,
	}
}

func (s *Store) WriteJob(ctx context.Context, jobUUID string, track_title string, filepath string) error{
	_ , err := s.postgres.Exec(ctx,
		"INSERT INTO jobs (id, track_title,file_path) VALUES ($1, $2, $3)",
		jobUUID, track_title, filepath,
	)
	return err
}

func (s *Store) QueryJobStatus(ctx context.Context, jobUUID string) (string, error){
	var status string
	err := s.postgres.QueryRow(ctx,
		"SELECT status FROM jobs WHERE id = ($1)",
		jobUUID,
	).Scan(&status)
	return status, err
}