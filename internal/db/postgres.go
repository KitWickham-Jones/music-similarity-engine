package db

import (
	"github.com/jackc/pgx/v5/pgxpool"
)

type Store struct{
	postgres *pgxpool.Pool
}

func New (db *pgxpool.Pool) *Store{
	return &Store{
		postgres : db,
	}
}


