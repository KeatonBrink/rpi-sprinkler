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

type UserRequest struct {
	SetSprinkler unsigned int 'json:"setSprinkler"'
}

var s State

var userRequest UserRequest
userRequest = UserRequest{SetSprinkler: 0}

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

func rpiPolling(w http.ResponseWriter, r *http.Request) {
	// Needs to get the state from the request, and then return an updated state

	err := json.NewDecoder(r.Body).Decode(&request)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		gologger.QueueMessage("Error decoding request")
		return
	}

	s.isSprinklerOn = request.IsSprinklerOn

	// The request will contain
	// 0 if nothing should change
	// 1 if the sprinkler should be on
	// 2 if the sprinkler should be off
	userRequestJson, err := json.Marshal(userRequest)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		gologger.QueueMessage("Error marshalling user request to JSON")
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write(userRequestJson)
	userRequest.SetSprinkler = 0
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

	http.HandleFunc("/rpi-polling")

	log.Fatal(http.ListenAndServe(":8080", nil))
}
