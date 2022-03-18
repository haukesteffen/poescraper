VERSION=0.1

all: build

build:
	go build
run:
	go run
docker-build:
	docker build -t jan104/poescraper -t jan104/poescraper:${VERSION} .
deploy:
	scripts/docker_push.sh ${VERSION}