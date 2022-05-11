FROM golang AS builder

WORKDIR $GOPATH/src/github.com/haukesteffen/poescraper/scraper/
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -ldflags "-w -extldflags -static -X main.GitCommit=$(git rev-parse HEAD) -X main.BuildTime=$(date -u --iso-8601=seconds)" -o /go/bin/poescraper

FROM alpine:3.15
COPY --from=builder /go/bin/poescraper /go/bin/poescraper
RUN chmod +x /go/bin/poescraper && mkdir /data && chown guest /data
USER guest
ENTRYPOINT ["/go/bin/poescraper"]


