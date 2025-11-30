#!/bin/bash
mkdir -p ca/{certs,csr,private}

cd ca

# ROOT CA
openssl genrsa -out private/ca.key 4096
openssl req -x509 -new -nodes -key private/ca.key -sha256 -days 3650 \
  -subj "/CN=Local-CA" \
  -out certs/ca.crt

# SCG CERT
openssl genrsa -out private/scg.key 2048
openssl req -new -key private/scg.key -out csr/scg.csr \
  -subj "/CN=SCG"
openssl x509 -req -in csr/scg.csr -CA certs/ca.crt -CAkey private/ca.key \
  -CAcreateserial -out certs/scg.crt -days 825 -sha256

# CLIENT CERT
openssl genrsa -out private/client.key 2048
openssl req -new -key private/client.key -out csr/client.csr \
  -subj "/CN=OperatorClient"
openssl x509 -req -in csr/client.csr -CA certs/ca.crt -CAkey private/ca.key \
  -CAcreateserial -out certs/client.crt -days 365 -sha256

# Extract public key for SCG
openssl x509 -in certs/client.crt -pubkey -noout > client_pub.pem

echo "CA, SCG certs, and Client certs generated successfully."
