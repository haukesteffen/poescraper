VERSION=0.1

all: build

build:
	go build -ldflags "-X main.GitCommit=$$(git rev-parse HEAD) -X main.BuildTime=$$(date -u --iso-8601=seconds)"
run:
	go run  -ldflags "-X main.GitCommit=$$(git rev-parse HEAD) -X main.BuildTime=$$(date -u --iso-8601=seconds)" .
docker-build:
	docker build -t jan104/poescraper -t jan104/poescraper:${VERSION} .
deploy:
	scripts/docker_push.sh ${VERSION}
