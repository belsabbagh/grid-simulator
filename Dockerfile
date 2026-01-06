FROM golang:1.25-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .

# CGO_ENABLED=0 is a common best practice for cross-system compatibility
# and statically linked binaries.
RUN CGO_ENABLED=0 go build -o /energy-trading-simulator ./main.go

FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

COPY --from=builder /energy-trading-simulator .
COPY --from=builder /app/models ./models/
COPY --from=builder /app/data ./data/

EXPOSE 5515

CMD ["./energy-trading-simulator"]

