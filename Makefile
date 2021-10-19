include .env

build:
	docker build . -t ${REGISTRY}:${VERSION}
	docker push ${REGISTRY}:${VERSION}

lint:
	pylint app.py
