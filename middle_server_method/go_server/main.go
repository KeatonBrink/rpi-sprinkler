package main

import (
	"encoding/json"
	"log"
	"net/http"

	"github.com/KeatonBrink/gologger"
)

type State struct {
	// some state
	isSprinklerOn bool
	currentLogs   []string
}

var s State

// type page struct {
// 	Title string
// 	Body  []byte
// }

func statusHandler(w http.ResponseWriter, r *http.Request) {
	type Status struct {
		IsSprinklerOn bool `json:"isSprinklerOn"`
	}

	status := Status{IsSprinklerOn: s.isSprinklerOn}
	statusJson, err := json.Marshal(status)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		gologger.QueueMessage("Error marshalling state to JSON")
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(statusJson)
}

// func handler(w http.ResponseWriter, r *http.Request) {
// 	fmt.Fprintf(w, "Hi there, I love %s!", r.URL.Path[1:])
// }

func main() {
	// err := gologger.InitGoLogger(true, "output.log")
	// if err != nil {
	// 	log.Fatal(err)
	// }
	go gologger.EmptyMessageQueue()

	s = State{isSprinklerOn: false, currentLogs: []string{}}

	fs := http.FileServer(http.Dir("./static"))
	http.Handle("/", fs)

	http.HandleFunc("/status", statusHandler)

	log.Fatal(http.ListenAndServe(":8080", nil))
}
