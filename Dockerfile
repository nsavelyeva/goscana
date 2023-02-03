FROM golang:1.20.0-alpine3.17

ENV GO111MODULE=on

RUN apk add build-base python3 \
    && go install \
		github.com/kisielk/errcheck@latest \
		golang.org/x/tools/cmd/goimports@latest \
		golang.org/x/lint/golint@latest \
		github.com/securego/gosec/cmd/gosec@latest \
		golang.org/x/tools/go/analysis/passes/shadow/cmd/shadow@latest \
		honnef.co/go/tools/cmd/staticcheck@latest

COPY goscana.py /goscana.py
RUN chmod a+rx /goscana.py

COPY entrypoint.sh /entrypoint.sh
RUN chmod a+x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
