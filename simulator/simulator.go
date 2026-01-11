package simulator

import (
	"bytes"
	"compress/gzip"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"strconv"
	"time"
)

func safeDivide(numerator float64, denominator float64) float64 {
	if denominator == 0 {
		return 0
	}
	return numerator / denominator
}

type Meter struct {
	ID                 string  `json:"id"`
	Surplus            float64 `json:"s"`
	Purchased          float64 `json:"p"`
	From               string  `json:"f"`
	ParticipationCount int64   `json:"c"`
}

func NewMeter(id string) *Meter {
	return &Meter{ID: id}
}

func (m *Meter) ReadEnv(gen float64, con float64) float64 {
	m.Surplus = gen - con
	return m.Surplus
}

type SimulationState struct {
	Time      string             `json:"time"`
	Meters    []*Meter           `json:"meters"`
	GridState map[string]float64 `json:"grid"`
}

type CompressedSimulationState struct {
	Time      string             `json:"time"`
	Meters    string             `json:"meters"`
	GridState map[string]float64 `json:"grid"`
}

func compressor(data any) string {
	jsonData, _ := json.Marshal(data)

	var buf bytes.Buffer
	zw := gzip.NewWriter(&buf)
	zw.Write(jsonData)
	zw.Close()

	encodedData := base64.StdEncoding.EncodeToString(buf.Bytes())
	return encodedData
}

func NewCompressedSimulationState(s *SimulationState) *CompressedSimulationState {
	return &CompressedSimulationState{
		Time:      s.Time,
		Meters:    compressor(s.Meters),
		GridState: s.GridState,
	}

}

var GridStateParams = []string{
	"Grid load (GWh)",
	"Grid temperature (C)",
	"Voltage (V)",
	"Global intensity (A)",
}

func FmtGridState(gridState []float64) map[string]float64 {
	result := make(map[string]float64)

	for i, param := range GridStateParams {
		if i < len(gridState) {
			result[param] = roundTo(gridState[i], 2)
		}
	}

	return result
}

func roundTo(n float64, decimals uint32) float64 {
	s := fmt.Sprintf("%.*f", decimals, n)
	res, _ := strconv.ParseFloat(s, 64)
	return res
}

func fmtMeters(meters map[string]*Meter) []*Meter {
	var results []*Meter
	for _, m := range meters {
		m.Surplus = roundTo(m.Surplus, 2)
		m.Purchased = roundTo(m.Purchased, 2)
		results = append(results, m)
	}
	return results
}

func NewSimulationState(t time.Time, meters []*Meter, gridState []float64) *SimulationState {
	return &SimulationState{
		Time:      t.Format("15:04:05"),
		Meters:    meters,
		GridState: FmtGridState(gridState),
	}
}

func Simulate(n int64, startDate, endDate time.Time, increment time.Duration) <-chan *SimulationState {
	out := make(chan *SimulationState)
	trader := NewTrader()
	gridStateGenerator := MkGridStateGenerator()

	go func() {
		defer close(out)
		dataGenerator := MkInstanceGenerator(startDate, endDate, increment, 0.5)
		meters := make(map[string]*Meter)
		for i := range n {
			id := fmt.Sprintf("%d", i+1)
			meters[id] = NewMeter(id)
		}

		for t := startDate; t.Before(endDate); t = t.Add(increment) {
			gridState := gridStateGenerator(t)

			for _, m := range meters {
				gen, con := dataGenerator(t)
				m.ReadEnv(gen, con)
				if m.Surplus > 0 {
					m.From = ""
				}
			}

			requests := trader.CollectRequests(meters, gridState)
			_ = trader.ExecuteTrades(requests, meters, gridState, increment)
			formattedMeters := fmtMeters(meters)
			out <- NewSimulationState(t, formattedMeters, gridState)

		}
	}()

	return out
}
