package simulator

import (
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
	ID                 int64   `json:"id"`
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

type Offer struct {
	Source             string
	Amount             float64
	ParticipationCount int64
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
	Meters    []MeterState       `json:"meters"`
	GridState map[string]float64 `json:"grid"`
}

type CompressedSimulationState struct {
	Time      string             `json:"time"`
	Meters    string             `json:"meters"`
	GridState map[string]float64 `json:"grid"`
}

type SimulationAnalytics struct {
	EnergyWastedBefore      float64 `json:"Energy Wasted Before"`
	EnergyWastedAfter       float64 `json:"Energy Wasted After"`
	SavedEnergy             float64 `json:"Saved Energy"`
	StatesMissedOutOnTrades int64   `json:"States missed out on trades"`
	TotalStates             int64   `json:"Total States"`
}

func allHaveSurplus(meters []MeterState) bool {
	allSurplus := true

	for _, m := range meters {
		if m.Surplus < 0 {
			allSurplus = false
			break
		}
	}
	return allSurplus
}

func missedPotentialTrade(meters []MeterState) bool {
	cond := false

	for _, m := range meters {
		if m.From == nil && m.Surplus < 0 {
			cond = true
			break
		}
	}
	return cond
}

func countAvailableSurplusMeters(meters []MeterState) int64 {
	sellerCount := 0
	surplusCount := 0
	for _, m := range meters {
		if m.Surplus > 0 {
			surplusCount += 1
			continue
		}
		if m.From != nil {
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

func (sa *SimulationAnalytics) Aggregate(meters []MeterState) *SimulationAnalytics {
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

func mapMeterStates(meters map[string]*Meter, trades map[string]*string, transfers map[string]float64) []MeterState {
	var results []MeterState
	for id, m := range meters {
		inTrade := ""
		if sellerID, ok := trades[id]; ok && sellerID != nil {
			inTrade = sellerID
		}

		results = append(results, MeterState{
			ID:                 id,
			Surplus:            roundTo(m.Surplus, 2),
			Purchased:          roundTo(transfers[id], 2),
			From:               inTrade,
			ParticipationCount: m.ParticipationCount,
		})
	}
	return results
}

func Simulate(n int64, startDate, endDate time.Time, increment time.Duration) <-chan SimulationState {
	out := make(chan SimulationState)

	go func() {
		defer close(out)
		tradeChooser := MkChooseBestOffersFunction("models/grid-loss-weights.csv", "models/duration-weights.csv", "models/grid-loss.json", make([]float64, 0))
		dataGenerator := MkInstanceGenerator(startDate, endDate, increment, 0.5)
		gridStateGenerator := MkGridStateGenerator()
		meters := make(map[string]*Meter)
		meterDisplayIds := make(map[string]int64)
		for i := range n {
			id := fmt.Sprintf("%d", i+1)
			meters[id] = NewMeter(id)
		}

		for t := startDate; t.Before(endDate); t = t.Add(increment) {
			gridState := gridStateGenerator(t)
			var offers []Offer

			for id, m := range meters {
				gen, con := dataGenerator(t)
				m.ReadEnv(gen, con)
				if m.Surplus > 0 {
					offers = append(offers, m)
				}
			}

			if len(offers) == 0 {
				meterStates := mapMeterStates(meters, nil, nil)
				out <- SimulationState{
					Time:      t.Format("15:04:05"),
					Meters:    meterStates,
					GridState: FmtGridState(gridState),
				}
				continue
			}

			trades := make(map[string]*string)
			requests := make(map[string][]Request)

			for id, m := range meters {
				if m.Surplus > 0 {
					trades[id] = nil
					continue
				}

				choices := tradeChooser(m.Surplus, offers, gridState, len(offers)-1)
				for _, c := range choices {
					sid := c.Offer.Source
					requests[sid] = append(requests[sid], Request{
						Meter: m, Score: c.Score,
					})
				}
			}

			transfers := make(map[string]float64)
			for sellerID, buyers := range requests {
				sort.Slice(buyers, func(i, j int) bool {
					return buyers[i].Score > buyers[j].Score
				})

				buyerID := buyers[0].Meter.ID
				meters[sellerID].ParticipationCount++
				trades[buyerID] = &sellerID
				gridLimit := gridState[len(gridState)-1] * gridState[len(gridState)-2] * increment.Seconds()
				transferAmount := math.Min(
					math.Min(meters[sellerID].Surplus, gridLimit),
					math.Abs(meters[buyerID].Surplus),
				)

				transfers[buyerID] = transferAmount
				transfers[sellerID] = -transferAmount
			}

			meterStates := mapMeterStates(meters, trades, transfers)

			out <- SimulationState{
				Time:      t.Format("15:04:05"),
				GridState: FmtGridState(gridState),
				Meters:    meterStates,
			}
		}
	}()

	return out
}
