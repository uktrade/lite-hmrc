FROM alpine AS certs

ARG CN
RUN apk --update add openssl
RUN openssl req -batch -x509 -newkey rsa:4096 -nodes -keyout key.pem -out cert.pem -sha256 -days 3650 -subj "/CN=${CN}"

FROM axllent/mailpit
RUN mkdir /certs
COPY --from=certs *.pem /certs
