
// package api

// import(
// 	"net/http"
// )

// func handleUpload(w http.ResponseWriter, r* http.Request){

// 	r.ParseMultipartForm(50 << 20)

// 	file, header, err := r.FormFile("audio")
// 	if err != nil{
// 		http.Error(w, "missing audio file", )
// 	}

// }