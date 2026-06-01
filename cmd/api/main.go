package main

import(
	"github.com/kitwj/music-similarity-engine/internal/api"
	"log"
	"net/http"
)


func main(){
	srv := api.New()
	log.Printf("server started at %s", "http://localhost:8080")
	log.Fatal(http.ListenAndServe(":8080", srv))
}