#!/bin/sh

cd deployment/certs || exit

openssl genrsa -out local-cert.key 2048

openssl req -x509 -new -nodes -key local-cert.key -sha256 -days 1825 -subj "/CN=local-cert" -out local-cert.pem

openssl req -new -passout pass:"password" -subj "/CN=local-cert" -key local-cert.key -out local-cert.csr

cat > local-cert.ext << EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names
[alt_names]
DNS.1 = local-cert
EOF

openssl x509 -req -in local-cert.csr -CA local-cert.pem -CAkey local-cert.key -CAcreateserial \
-out local-cert.crt -days 825 -sha256 -extfile local-cert.ext
