package main

import (
	"encoding/json"
	"energy-trading-simulator/simulator"
	"fmt"
	"net/http"
	"time"
)

type RunRequest struct {
	NumMeters int64  `json:"numMeters"`
	StartDate string `json:"startDate"`
}

func runHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req RunRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, fmt.Sprintf("%s", err), http.StatusBadRequest)
		return
	}

	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-cache")
	w.Header().Set("Connection", "keep-alive")
	w.Header().Set("Access-Control-Allow-Origin", "*")

	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "Streaming unsupported", http.StatusInternalServerError)
		return
	}
	layout := "2006-01-02T15:04:05"
	startDate, err := time.Parse(layout, req.StartDate)
	if err != nil {
		fmt.Println("Error parsing time:", err)
		return
	}
	endDate := startDate.Add(24 * time.Hour)
	// ... setup code ...
	sim := simulator.Simulate(req.NumMeters, startDate, endDate, time.Minute)

	for state := range sim {
		payload := struct {
			Status string                    `json:"status"`
			State  simulator.SimulationState `json:"state"`
		}{
			Status: "running",
			State:  state,
		}

		jsonData, err := json.Marshal(payload)
		if err != nil {
			fmt.Printf("Error marshaling state: %v\n", err)
			continue
		}

		_, err = fmt.Fprintf(w, "data: %s\n\n", jsonData)
		if err != nil {
			return
		}

		flusher.Flush()
	}

	fmt.Fprintf(w, "data: {\"status\": \"done\"}\n\n")
	flusher.Flush()
}

func main() {
	http.HandleFunc("/run", runHandler)
	fmt.Println("SSE Server starting on :8080...")
	http.ListenAndServe(":8080", nil)
}
