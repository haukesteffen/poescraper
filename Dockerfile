FROM golang AS builder

WORKDIR $GOPATH/src/github.com/haukesteffen/poescraper/
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -a -ldflags "-w -extldflags -static" -o /go/bin/poescraper

FROM alpine:3.15
COPY --from=builder /go/bin/poescraper /go/bin/poescraper
RUN chmod +x /go/bin/poescraper
USER guest
ENTRYPOINT ["/go/bin/poescraper"]

