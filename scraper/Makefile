VERSION=0.1
LOCAL_ACCOUNT=jan104
LOCAL_PROJ=poescraper
LOCAL_DOCKER=${LOCAL_ACCOUNT}/${LOCAL_PROJ}
#NEW_VERSION=$(shell docker images | awk -v PROJ=${LOCAL_DOCKER} '($1 == PROJ) {print $2 += .01; exit})')
#NEW_VERSION=$(shell docker images | awk -v PROJ=${LOCAL_DOCKER} '($1 == 'jan104/poescraper') {print PROJ; exit}')

all: build

build:
	go build -ldflags "-X main.BuildTime=$$(date -u --iso-8601=seconds)" -o ${LOCAL_PROJ}
run:
	go run  -ldflags "-X main.BuildTime=$$(date -u --iso-8601=seconds)" .
docker-build:
	docker build -t ${LOCAL_DOCKER} -t ${LOCAL_DOCKER}:${VERSION} .
deploy:
	../scripts/docker_push.sh ${VERSION}
