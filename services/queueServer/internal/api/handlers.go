package api

import (
	"encoding/json"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"github.com/google/uuid"
)

func (s *Server) handleUpload(w http.ResponseWriter, r* http.Request){

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