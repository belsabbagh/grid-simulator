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

type CompressedResponse struct {
	Status    string                               `json:"status"`
	State     *simulator.CompressedSimulationState `json:"state"`
	Analytics *simulator.SimulationAnalytics       `json:"analytics"`
}
type Response struct {
	Status    string                         `json:"status"`
	State     *simulator.SimulationState     `json:"state"`
	Analytics *simulator.SimulationAnalytics `json:"analytics"`
}

func LogMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		startTime := time.Now()

		next.ServeHTTP(w, r)

		elapsedTime := time.Since(startTime)
		log.Printf("[%s] [%s] [%s]\n", r.Method, r.URL.Path, elapsedTime)
	})
}

func CORSMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		w.Header().Set("Access-Control-Allow-Origin", "*")
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func runHandler(w http.ResponseWriter, r *http.Request) {
	timeoutStr := os.Getenv("SIMULATION_STEP_DELAY_MS")
	delay, err := time.ParseDuration(timeoutStr)
	if err != nil {
		delay = 100 * time.Millisecond
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
		compressed := simulator.NewCompressedSimulationState(state)

		payload := CompressedResponse{
			Status:    "running",
			State:     compressed,
			Analytics: analytics,
		}
		// payload := Response{
		// 	Status:    "running",
		// 	State:     state,
		// 	Analytics: analytics,
		// }

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
		time.Sleep(delay)
	}

	fmt.Fprintf(w, "data: {\"status\": \"done\"}\n\n")
	flusher.Flush()
}

func healthCheckHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte("ok"))
}

func main() {
	err := godotenv.Load()
	if err != nil {
		log.Println("Warning: No .env file found, using system env or defaults")
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "5515"
		log.Printf("PORT not set in .env, defaulting to %s", port)
	}
	mux := http.NewServeMux()
	mux.HandleFunc("/run", runHandler)
	mux.HandleFunc("/health", healthCheckHandler)
	wrappedMux := LogMiddleware(CORSMiddleware(mux))
	address := ":" + port
	log.Printf("Server starting on %s...\n", address)

	if err := http.ListenAndServe(address, wrappedMux); err != nil {
		log.Fatal(err)
	}
}
