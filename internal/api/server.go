package api

import (
	"net/http"
	"log"
)

type Server struct{
	router *http.ServeMux
}

func New() *Server{
	s := &Server{
		router: http.NewServeMux(),
	}
	s.router.HandleFunc("POST /upload", s.handleUpload)
	return s 
}

func (s *Server) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	log.Printf("%s %s", r.Method, r.URL.Path)
	s.router.ServeHTTP(w, r)
}