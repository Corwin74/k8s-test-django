NAME   := corwinz/dj
TAG    ?= $(shell git log --format="%h" -n 1)
IMG    := ${NAME}:${TAG}
LATEST := ${NAME}:latest

build:
	@docker build -t ${IMG} .

push:
	@docker push ${IMG}