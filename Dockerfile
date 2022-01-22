FROM 1.17.6-alpine3.15

ENV GO111MODULE=on

RUN apk add python3 \
    && go get -u \
		github.com/kisielk/errcheck \
		golang.org/x/tools/cmd/goimports \
		golang.org/x/lint/golint \
		github.com/securego/gosec/cmd/gosec \
		golang.org/x/tools/go/analysis/passes/shadow/cmd/shadow \
		honnef.co/go/tools/cmd/staticcheck

COPY entrypoint.py /entrypoint.py

ENTRYPOINT ["python3 /entrypoint.py"]
