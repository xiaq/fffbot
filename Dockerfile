FROM golang:alpine as builder
COPY . /app
WORKDIR /app
RUN apk add git
RUN go get -d -v
RUN go build -o ./binary

FROM alpine
COPY --from=builder /app/binary /app/binary
RUN apk update && apk add ca-certificates && rm -rf /var/cache/apk
RUN adduser -D -g '' appuser
USER appuser
WORKDIR /data
VOLUME /data/token.txt
CMD ["/app/binary"]
