package main

import (
	"log"
	"net/http"
	"context"
	"github.com/jackc/pgx/v5/pgxpool"		
	"github.com/joho/godotenv"
	"github.com/kitwj/music-similarity-engine/internal/api"
	"github.com/kitwj/music-similarity-engine/internal/config"
	"github.com/kitwj/music-similarity-engine/internal/db"
)


func main(){
	godotenv.Load()
	cfg := config.Load()
	dbCon, err := pgxpool.New(context.Background(), cfg.DatabaseURL )
	if err != nil{
		log.Fatal(err)
	}
	defer dbCon.Close()

	if err := dbCon.Ping(context.Background()); err != nil{
		log.Fatal("Could not connect to db ", err)
	}
	log.Println("Connected to db")

	store := db.New(dbCon)
	srv := api.New(store)
	log.Printf("server started at %s", "http://localhost:8080")
	log.Fatal(http.ListenAndServe(":8080", srv))
}