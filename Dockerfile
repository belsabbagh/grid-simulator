FROM golang:1.25-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .

# CGO_ENABLED=0 is a common best practice for cross-system compatibility
# and statically linked binaries.
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -trimpath -o /energy-trading-simulator ./main.go

FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

COPY --from=builder /energy-trading-simulator .
COPY --from=builder /app/models ./models/
COPY --from=builder /app/data ./data/

RUN apk add --no-cache curl
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5515/health || exit 1

EXPOSE 5515

ENTRYPOINT ["./energy-trading-simulator"]

