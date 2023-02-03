FROM golang:1.20.0-alpine3.17

ENV GO111MODULE=on

RUN apk add build-base python3 \
    && go get -u \
		github.com/kisielk/errcheck \
		golang.org/x/tools/cmd/goimports \
		golang.org/x/lint/golint \
		github.com/securego/gosec/cmd/gosec \
		golang.org/x/tools/go/analysis/passes/shadow/cmd/shadow \
		honnef.co/go/tools/cmd/staticcheck

COPY goscana.py /goscana.py
RUN chmod a+rx /goscana.py

COPY entrypoint.sh /entrypoint.sh
RUN chmod a+x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
