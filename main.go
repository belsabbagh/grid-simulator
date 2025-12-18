package main

import (
	"encoding/json"
	"energy-trading-simulator/simulator"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/joho/godotenv"
)

type RunRequest struct {
	NumMeters int64  `json:"numMeters"`
	StartDate string `json:"startDate"`
}

func runHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost && r.Method != http.MethodOptions {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusOK)
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
	w.Header().Set("Transfer-Encoding", "chunked")

	flusher, ok := w.(http.Flusher)
	if !ok {
		http.Error(w, "Streaming unsupported", http.StatusInternalServerError)
		return
	}
	layout := "2006-01-02T15:04"
	startDate, err := time.Parse(layout, req.StartDate)
	if err != nil {
		http.Error(w, fmt.Sprintf("Time Parsing error: %s", err), http.StatusUnprocessableEntity)
		return
	}
	endDate := startDate.Add(24 * time.Hour)
	analytics := simulator.NewSimulationAnalytics()
	sim := simulator.Simulate(req.NumMeters, startDate, endDate, time.Minute)

	for state := range sim {
		analytics.Aggregate(state.Meters)
		payload := struct {
			Status    string                        `json:"status"`
			State     simulator.SimulationState     `json:"state"`
			Analytics simulator.SimulationAnalytics `json:"analytics"`
		}{
			Status:    "running",
			State:     state,
			Analytics: *analytics,
		}

		jsonData, err := json.Marshal(payload)
		if err != nil {
			log.Printf("Error marshaling state: %v\n", err)
			continue
		}

		_, err = fmt.Fprintf(w, "data: %s\n\n", jsonData)
		if err != nil {
			return
		}

		flusher.Flush()
		time.Sleep(100 * time.Millisecond)
	}

	fmt.Fprintf(w, "data: {\"status\": \"done\"}\n\n")
	flusher.Flush()
}

func main() {
	err := godotenv.Load()
	if err != nil {
		log.Println("Warning: No .env file found, using system env or defaults")
	}

	// 2. Get the PORT variable
	port := os.Getenv("PORT")
	if port == "" {
		port = "5515" // Default fallback
		log.Printf("PORT not set in .env, defaulting to %s", port)
	}

	http.HandleFunc("/run", runHandler)

	// 3. Use the port variable
	address := ":" + port
	log.Printf("SSE Server starting on %s...\n", address)

	if err := http.ListenAndServe(address, nil); err != nil {
		log.Fatal(err)
	}
}
