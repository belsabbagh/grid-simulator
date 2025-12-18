package simulator

import (
	"fmt"
	"math"
	"sort"
	"time"
)

type Meter struct {
	ID        string
	Surplus   float64
	SoldCount int64
}

func NewMeter(id string) *Meter {
	return &Meter{ID: id}
}

func (m *Meter) ReadEnv(gen, con float64) float64 {
	m.Surplus = gen - con
	return m.Surplus
}

type Offer struct {
	Source             string
	Amount             float64
	ParticipationCount int64
}

type Choice struct {
	Offer   Offer
	Fitness float64
}

type MeterState struct {
	ID                 int64   `json:"id"`
	Surplus            float64 `json:"surplus"`
	Sent               float64 `json:"sent"`
	InTrade            *int64  `json:"in_trade"`
	ParticipationCount int64   `json:"participation_count"`
}

type SimulationState struct {
	Time      string             `json:"time"`
	Meters    []MeterState       `json:"meters"`
	GridState map[string]float64 `json:"grid_state"`
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
			result[param] = gridState[i]
		}
	}

	return result
}
func mapMeterStates(meters map[string]*Meter, displayIds map[string]int64, trades map[string]*string, transfers map[string]float64) []MeterState {
	var results []MeterState
	for id, m := range meters {
		var inTrade *int64
		if sellerID, ok := trades[id]; ok && sellerID != nil {
			val := displayIds[*sellerID]
			inTrade = &val
		}

		results = append(results, MeterState{
			ID:                 displayIds[id],
			Surplus:            m.Surplus,
			Sent:               transfers[id],
			InTrade:            inTrade,
			ParticipationCount: m.SoldCount,
		})
	}
	return results
}

func Simulate(n int64, startDate, endDate time.Time, increment time.Duration) <-chan SimulationState {
	out := make(chan SimulationState)

	go func() {
		defer close(out)
		tradeChooser := MkChooseBestOffersFunction("models/grid-loss-weights.csv", "models/duration-weights.csv", "models/grid-loss.json", 3, make([]float64, 0))
		dataGenerator := MkInstanceGenerator(startDate, endDate, increment, 0.1)
		gridStateGenerator := MkGridStateGenerator()

		meters := make(map[string]*Meter)
		meterDisplayIds := make(map[string]int64)
		for i := range n {
			id := fmt.Sprintf("%d", i)
			meters[id] = NewMeter(id)
			meterDisplayIds[id] = i + 1
		}

		for t := startDate; t.Before(endDate); t = t.Add(increment) {
			gridState := gridStateGenerator(t)
			var offers []Offer

			for id, m := range meters {
				gen, con := dataGenerator(t)
				m.ReadEnv(gen, con)
				if m.Surplus > 0 {
					offers = append(offers, Offer{
						Source:             id,
						Amount:             m.Surplus,
						ParticipationCount: m.SoldCount,
					})
				}
			}

			if len(offers) == 0 {
				out <- SimulationState{
					Time:      t.Format(time.RFC3339),
					Meters:    mapMeterStates(meters, meterDisplayIds, nil, nil),
					GridState: FmtGridState(gridState),
				}
				continue
			}

			trades := make(map[string]*string)
			requests := make(map[string][]Choice)

			for id, m := range meters {
				if m.Surplus > 0 {
					trades[id] = nil
					continue
				}

				choices := tradeChooser(m.Surplus, offers, gridState)
				if len(choices) > 0 {
					bestChoice := choices[0]
					sellerID := bestChoice.Offer.Source
					trades[id] = &sellerID
					requests[sellerID] = append(requests[sellerID], Choice{
						Offer:   Offer{Source: id},
						Fitness: bestChoice.Score,
					})
				}
			}

			transfers := make(map[string]float64)
			for sellerID, buyers := range requests {
				sort.Slice(buyers, func(i, j int) bool {
					return buyers[i].Fitness > buyers[j].Fitness
				})

				buyerID := buyers[0].Offer.Source
				amount := meters[sellerID].Surplus
				meters[sellerID].SoldCount++

				gridLimit := gridState[len(gridState)-1] * gridState[len(gridState)-2] * increment.Seconds()
				transferAmount := math.Min(
					math.Min(amount, gridLimit),
					math.Abs(meters[buyerID].Surplus),
				)

				transfers[buyerID] = transferAmount
				transfers[sellerID] = -transferAmount
			}

			// 5. Yield State
			out <- SimulationState{
				Time:      t.Format("15:04:05"),
				GridState: FmtGridState(gridState),
				Meters:    mapMeterStates(meters, meterDisplayIds, trades, transfers),
			}
		}
	}()

	return out
}
