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

func (s *Store) WriteJob(ctx context.Context, jobUUID string, filepath string) error{
	_ , err := s.postgres.Exec(ctx,
		"INSERT INTO jobs (id, file_path) VALUES ($1, $2)",
		jobUUID, filepath,
	)
	return err
}
