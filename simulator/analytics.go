package simulator

type SimulationAnalytics struct {
	Surplus                 int64   `json:"Surplus Meters"`
	Sufficient              int64   `json:"Sufficient Meters"`
	Deficient               int64   `json:"Deficient Meters"`
	EnergyWastedBefore      float64 `json:"Energy Wasted Before"`
	EnergyWastedAfter       float64 `json:"Energy Wasted After"`
	SavedEnergy             float64 `json:"Saved Energy"`
	StatesMissedOutOnTrades int64   `json:"States missed out on trades"`
	TotalStates             int64   `json:"Total States"`
}

func allHaveSurplus(meters []*Meter) bool {
	allSurplus := true

	for _, m := range meters {
		if m.Surplus < 0 {
			allSurplus = false
			break
		}
	}
	return allSurplus
}

func missedPotentialTrade(meters []*Meter) bool {
	cond := false

	for _, m := range meters {
		if m.Trade == "" && m.Surplus < 0 {
			cond = true
			break
		}
	}
	return cond
}

func countAvailableSurplusMeters(meters []*Meter) int64 {
	sellerCount := 0
	surplusCount := 0
	for _, m := range meters {
		if m.Surplus > 0 {
			surplusCount += 1
			continue
		}
		if m.Trade != "" {
			sellerCount += 1
		}

	}
	return int64(surplusCount - sellerCount)
}

func NewSimulationAnalytics() *SimulationAnalytics {
	return &SimulationAnalytics{
		Surplus:                 0,
		Sufficient:              0,
		Deficient:               0,
		EnergyWastedBefore:      0,
		EnergyWastedAfter:       0,
		SavedEnergy:             0,
		StatesMissedOutOnTrades: 0,
		TotalStates:             0,
	}
}

func (sa *SimulationAnalytics) Aggregate(meters []*Meter) *SimulationAnalytics {
	sa.TotalStates += 1
	available := countAvailableSurplusMeters(meters)
	if available > 0 && missedPotentialTrade(meters) {
		sa.StatesMissedOutOnTrades += 1
	}
	sa.Surplus = 0
	sa.Sufficient = 0
	sa.Deficient = 0
	for _, m := range meters {
		if m.Surplus > 0 {
			sa.Surplus++
			sa.EnergyWastedBefore += m.Surplus
		}
		if m.Surplus == 0 {
			sa.Sufficient++
		}
		if m.Surplus < 0 {
			sa.Deficient++
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
