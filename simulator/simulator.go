package simulator

import (
	"bytes"
	"compress/gzip"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"math"
	"sort"
	"strconv"
	"time"
)

func safeDivide(numerator, denominator float64) float64 {
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

func (m *Meter) ReadEnv(gen, con float64) float64 {
	m.Surplus = gen - con
	return m.Surplus
}

type Request struct {
	Meter Meter
	Score float64
}

type MeterState struct {
	ID                 string  `json:"id"`
	Surplus            float64 `json:"s"`
	Purchased          float64 `json:"p"`
	From               string  `json:"f"`
	ParticipationCount int64   `json:"c"`
}

type SimulationState struct {
	Time      string             `json:"time"`
	Meters    []*MeterState      `json:"meters"`
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

type SimulationAnalytics struct {
	EnergyWastedBefore      float64 `json:"Energy Wasted Before"`
	EnergyWastedAfter       float64 `json:"Energy Wasted After"`
	SavedEnergy             float64 `json:"Saved Energy"`
	StatesMissedOutOnTrades int64   `json:"States missed out on trades"`
	TotalStates             int64   `json:"Total States"`
}

func allHaveSurplus(meters []*MeterState) bool {
	allSurplus := true

	for _, m := range meters {
		if m.Surplus < 0 {
			allSurplus = false
			break
		}
	}
	return allSurplus
}

func missedPotentialTrade(meters []*MeterState) bool {
	cond := false

	for _, m := range meters {
		if m.From == "" && m.Surplus < 0 {
			cond = true
			break
		}
	}
	return cond
}

func countAvailableSurplusMeters(meters []*MeterState) int64 {
	sellerCount := 0
	surplusCount := 0
	for _, m := range meters {
		if m.Surplus > 0 {
			surplusCount += 1
			continue
		}
		if m.From != "" {
			sellerCount += 1
		}

	}
	return int64(surplusCount - sellerCount)
}

func NewSimulationAnalytics() *SimulationAnalytics {
	return &SimulationAnalytics{
		EnergyWastedBefore:      0,
		EnergyWastedAfter:       0,
		SavedEnergy:             0,
		StatesMissedOutOnTrades: 0,
		TotalStates:             0,
	}
}

func (sa *SimulationAnalytics) Aggregate(meters []*MeterState) *SimulationAnalytics {
	sa.TotalStates += 1
	available := countAvailableSurplusMeters(meters)
	if available > 0 && missedPotentialTrade(meters) {
		sa.StatesMissedOutOnTrades += 1
	}
	for _, m := range meters {
		if m.Surplus > 0 {
			sa.EnergyWastedBefore += m.Surplus
		}
		remaining := m.Surplus + m.Purchased

		if remaining > 0 {
			sa.EnergyWastedAfter += remaining
		}
	}
	sa.SavedEnergy = safeDivide(sa.EnergyWastedBefore-sa.EnergyWastedAfter, sa.EnergyWastedBefore)

	sa.SavedEnergy = roundTo(sa.SavedEnergy, 2)
	sa.EnergyWastedBefore = roundTo(sa.EnergyWastedBefore, 2)
	sa.EnergyWastedAfter = roundTo(sa.EnergyWastedAfter, 2)

	return sa
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

func mapMeterStates(meters map[string]*Meter, trades map[string]*string, transfers map[string]float64) []*MeterState {
	var results []*MeterState
	for id, m := range meters {
		inTrade := ""
		if sellerID, ok := trades[id]; ok && sellerID != nil {
			inTrade = *sellerID
		}

		results = append(results, &MeterState{
			ID:                 id,
			Surplus:            roundTo(m.Surplus, 2),
			Purchased:          roundTo(transfers[id], 2),
			From:               inTrade,
			ParticipationCount: m.ParticipationCount,
		})
	}
	return results
}

func NewSimulationState(t Time, meterStates []*MeterState) *SimulationState {
	return &SimulationState{
		Time:      t.Format("15:04:05"),
		Meters:    meterStates,
		GridState: FmtGridState(gridState),
	}
}

func Simulate(n int64, startDate, endDate time.Time, increment time.Duration) <-chan *SimulationState {
	out := make(chan *SimulationState)
	tradeChooser := MkChooseBestOffersFunction("models/grid-loss-weights.csv", "models/duration-weights.csv", "models/grid-loss.json", make([]float64, 0))
	trader := NewTrader(tradeChooser)
	go func() {
		defer close(out)
		dataGenerator := MkInstanceGenerator(startDate, endDate, increment, 0.5)
		gridStateGenerator := MkGridStateGenerator()
		meters := make(map[string]*Meter)
		for i := range n {
			id := fmt.Sprintf("%d", i+1)
			meters[id] = NewMeter(id)
		}

		for t := startDate; t.Before(endDate); t = t.Add(increment) {
			gridState := gridStateGenerator(t)
			var offers []*Meter

			for _, m := range meters {
				gen, con := dataGenerator(t)
				m.ReadEnv(gen, con)
				if m.Surplus > 0 {
					offers = append(offers, m)
				}
			}

			if len(offers) == 0 {
				meterStates := mapMeterStates(meters, nil, nil)
				out <- &SimulationState{
					Time:      t.Format("15:04:05"),
					Meters:    meterStates,
					GridState: FmtGridState(gridState),
				}
				continue
			}

			requests := make(map[string][]*Request)

			for id, m := range meters {
				if m.Surplus > 0 {
					trader.Trades[id] = nil
					continue
				}
				scoredOffers := trader.ScoreOffers(m, offers, gridState, len(offers)-1)
				for _, o := range scoredOffers {
					sid := o.Offer.ID
					requests[sid] = append(requests[sid], Request{
						Meter: *m, Score: o.Score,
					})
				}
			}
			transfers := trader.ExecuteTrades(requests, meters, gridState)
			meterStates := mapMeterStates(meters, trader.Trades, transfers)

			out <- &SimulationState{
				Time:      t.Format("15:04:05"),
				GridState: FmtGridState(gridState),
				Meters:    meterStates,
			}
		}
	}()

	return out
}
