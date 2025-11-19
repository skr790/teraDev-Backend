package main

import (
	"fmt"
	"net/http"
)

func main() {
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintln(w, "Hello World from SKR!")
	})
	http.HandleFunc("/skr", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintln(w, "This is SKR endpoint")
	})

	fmt.Println("Server running on http://localhost:9090")
	http.ListenAndServe(":9090", nil)
}
