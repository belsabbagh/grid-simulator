package simulator

import (
	"encoding/csv"
	"fmt"
	"math"
	"math/rand"
	"os"
	"time"

	"github.com/sixdouglas/suncalc"
)

const TimeFormat = "15:04:05"

func PrepareGenerationLookup(start time.Time, end time.Time, increment time.Duration) (map[time.Time]float64, error) {
	lat := 32.2
	lon := 30.0
	gen := make(map[time.Time]float64)

	st := suncalc.GetTimes(start, lat, lon)
	for t := start; !t.After(end); t = t.Add(increment) {
		var power float64 = 0
		if t.After(st["sunrise"].Value) && t.Before(st["sunset"].Value) {
			totalDaylight := st["sunset"].Value.Sub(st["sunrise"].Value).Seconds()
			elapsed := t.Sub(st["sunrise"].Value).Seconds()
			intensity := math.Sin(math.Pi * (elapsed / totalDaylight))
			power = intensity * (2.3 / 1000.0) * 1000

		}
		gen[t] = power
	}
	return gen, nil
}

func PrepareConsumptionLookup(start time.Time, end time.Time, increment time.Duration, filePath string) (map[time.Time]float64, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	reader := csv.NewReader(file)
	records, err := reader.ReadAll()
	if err != nil {
		return nil, err
	}

	rawCon := make(map[string]float64)
	for _, record := range records[1:] {
		var val float64
		fmt.Sscanf(record[1], "%f", &val)
		rawCon[record[0]] = val
	}

	conMap := make(map[time.Time]float64)
	for t := start; !t.After(end); t = t.Add(increment) {
		timeKey := t.Format(TimeFormat)
		conMap[t] = rawCon[timeKey]
	}

	return conMap, nil
}

type InstanceGenerator func(time.Time) (float64, float64)

func GenerateRandom(t time.Time, data map[time.Time]float64, deviation float64) float64 {
	val, ok := data[t]
	if !ok {
		return 0.0
	}
	randomVal := (rand.Float64() * 2 * deviation) - deviation
	return val + randomVal
}

func MkInstanceGenerator(start, end time.Time, increment time.Duration, deviation float64) InstanceGenerator {
	genData, _ := PrepareGenerationLookup(start, end, increment)
	conData, _ := PrepareConsumptionLookup(start, end, increment, "data/output.txt")

	return func(t time.Time) (float64, float64) {
		return GenerateRandom(t, genData, deviation), GenerateRandom(t, conData, deviation)
	}
}

type GridStateGenerator func(t time.Time) []float64

func MkGridStateGenerator() GridStateGenerator {
	// means and devs for: [load, temperature, voltage, intensity]
	means := []float64{0.4, 20, 239.696, 3.132}
	devs := []float64{0.1, 1, 1, 0.1}

	return func(_t time.Time) []float64 {
		results := make([]float64, len(means))

		for i := 0; i < len(means); i++ {
			// rand.NormFloat64 returns a normal distribution with:
			// mean = 0, stddev = 1.
			// To adjust: (StandardNormal * dev) + mean
			results[i] = (rand.NormFloat64() * devs[i]) + means[i]
		}

		return results
	}
}
