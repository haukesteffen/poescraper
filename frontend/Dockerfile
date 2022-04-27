FROM golang AS builder

WORKDIR $GOPATH/src/github.com/haukesteffen/poescraper/frontend
RUN go mod init
COPY frontend.go frontend.go
RUN CGO_ENABLED=0 GOOS=linux go build -a -ldflags "-w -extldflags -static " -o /go/bin/frontend

FROM alpine:3.15
COPY --from=builder /go/bin/frontend /app/frontend
RUN chmod +x /app/frontend
WORKDIR /app
COPY index.html index.html
USER guest
ENTRYPOINT ["/app/frontend"]


