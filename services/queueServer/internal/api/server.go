package api

import (
	"log"
	"net/http"
	"github.com/kitwj/music-similarity-engine/internal/db"
)

type Server struct{
	router *http.ServeMux
	store *db.Store
}

func New(db* db.Store) *Server{
	s := &Server{
		router: http.NewServeMux(),
		store: db,
	}
	s.router.HandleFunc("POST /upload", s.handleUpload)
	s.router.HandleFunc("GET /jobs/{jobID}", s.handleQueryJobStatus)
	return s 
}

func (s *Server) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	log.Printf("%s %s", r.Method, r.URL.Path)
	s.router.ServeHTTP(w, r)
}