package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"

	"github.com/KeatonBrink/gologger"
)

type State struct {
	// some state
	isSprinklerOn bool
	rpiLogs       []string
}

type UserRequest struct {
	SetSprinkler int `json:"setSprinkler"`
}

var rpiLogs []string

var s State

var userRequest UserRequest

// type page struct {
// 	Title string
// 	Body  []byte
// }

func statusHandler(w http.ResponseWriter, r *http.Request) {
	type Status struct {
		IsSprinklerOn bool `json:"status"`
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
	fmt.Println("Start rpiPolling")

	type Request struct {
		sprinklerStatus string `json:"sprinklerStatus"`
	}

	var request Request

	err := json.NewDecoder(r.Body).Decode(&request)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		gologger.QueueMessage("Error decoding request")
		return
	}

	if request.sprinklerStatus == "on" {
		s.isSprinklerOn = true
	} else {
		s.isSprinklerOn = false
	}

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
	fmt.Println("End of rpiPolling")
}

func rpiLogReport(w http.ResponseWriter, r *http.Request) {
	fmt.Println("Start rpiLogReport")

	var logs []string

	err := json.NewDecoder(r.Body).Decode(&logs)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		fmt.Println("Error decoding request:", err)
		return
	}

	s.rpiLogs = logs

	fmt.Println("Received logs:", s.rpiLogs)
	fmt.Println("End of rpiLogReport")

	w.WriteHeader(http.StatusOK)
	w.Write([]byte("Logs received successfully"))
}

// func handler(w http.ResponseWriter, r *http.Request) {
// 	fmt.Fprintf(w, "Hi there, I love %s!", r.URL.Path[1:])
// }

func main() {
	err := gologger.InitGoLogger(false, "output.log")
	if err != nil {
		log.Fatal(err)
	}
	defer gologger.EmptyMessageQueue()

	s = State{isSprinklerOn: false, rpiLogs: []string{}}

	userRequest = UserRequest{SetSprinkler: 0}

	fs := http.FileServer(http.Dir("./static"))
	http.Handle("/", fs)

	http.HandleFunc("/status", statusHandler)

	http.HandleFunc("/rpi-polling", rpiPolling)

	http.HandleFunc("/rpi-logs", rpiLogReport)

	log.Fatal(http.ListenAndServe(":8080", nil))
}
