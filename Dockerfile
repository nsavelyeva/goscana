FROM golang:1.20.0-alpine3.17

ENV GO111MODULE=on

RUN apk add build-base python3 \
    && go install github.com/kisielk/errcheck@v1.6.3 \
    && go install golang.org/x/tools/cmd/goimports@v0.5.0 \
    && go install golang.org/x/lint/golint@v0.0.0-20210508222113-6edffad5e616 \
    && go install github.com/securego/gosec/v2/cmd/gosec@latest \
    && go install golang.org/x/tools/go/analysis/passes/shadow/cmd/shadow@v0.5.0 \
    && go install honnef.co/go/tools/cmd/staticcheck@v0.4.0

COPY goscana.py /goscana.py
RUN chmod a+rx /goscana.py

COPY entrypoint.sh /entrypoint.sh
RUN chmod a+x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
