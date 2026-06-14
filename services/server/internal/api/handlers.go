package api

import (
	"encoding/json"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
)

func (s *Server) handleUpload(w http.ResponseWriter, r *http.Request){
	r.ParseMultipartForm(50 << 20)

	file, header, err := r.FormFile("audio")
	if err != nil{
		http.Error(w, "missing audio file", http.StatusBadRequest)
		return
	}
	defer file.Close()

	if filepath.Ext(header.Filename) != ".mp3"{
		http.Error(w, "only mp3 files can be accepted", http.StatusBadRequest)
		return
	}

	savePath := filepath.Join("/tmp/uploads", header.Filename)
	os.MkdirAll("/tmp/uploads", 0755)
	dst, err := os.Create(savePath)
	if err != nil {
		http.Error(w, "failed to save file", http.StatusInternalServerError)
		return
	}
	defer dst.Close()
	io.Copy(dst, file)

	track_title :=  strings.TrimSuffix(header.Filename, filepath.Ext(header.Filename))

	id := uuid.New().String()

	err = s.store.WriteJob(r.Context(), id, track_title ,savePath)
	if err != nil{
		http.Error(w, "failed to write job to database", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusAccepted)
	json.NewEncoder(w).Encode(map[string]string{"track_title": track_title, "job_id" : id, "filepath" : savePath})
}

func (s *Server) handleQueryJobStatus(w http.ResponseWriter, r *http.Request){
	
	jobID := r.PathValue("jobID")
	if jobID == ""{
		http.NotFound(w, r)
		return
	}

	status, err := s.store.QueryJobStatus(r.Context(), jobID)
	if err == pgx.ErrNoRows{
		http.Error(w, "job not found", http.StatusNotFound)
		return
	}
	if err != nil {
		log.Printf("GetJobStatus failed for job %s: %v", jobID, err)
		http.Error(w, "Internal failure", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"job_id" : jobID,
		"status" : status,
	})
}
