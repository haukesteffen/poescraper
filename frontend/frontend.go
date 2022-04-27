package main

import (
	"fmt"
	"net/http"
)

func main() {
	fmt.Printf("Starting server at port 8080\n")
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		http.ServeFile(w, r, "index.html")
	})
	if err := http.ListenAndServe(":8080", nil); err != nil {
		panic(err)
	}
}
