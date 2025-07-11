#!/usr/bin/env python3
from OpenSSL import crypto
import os

def create_self_signed_cert():
    # Crear una clave privada
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)
    
    # Crear un certificado autofirmado
    cert = crypto.X509()
    cert.get_subject().C = "ES"
    cert.get_subject().ST = "Madrid"
    cert.get_subject().L = "Madrid"
    cert.get_subject().O = "Silenda"
    cert.get_subject().OU = "Development"
    cert.get_subject().CN = "localhost"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365*24*60*60)  # Válido por 1 año
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha256')
    
    # Guardar la clave privada
    with open("key.pem", "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
    
    # Guardar el certificado
    with open("cert.pem", "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    
    print("Certificado y clave generados correctamente.")
    print("cert.pem y key.pem han sido creados en el directorio actual.")

if __name__ == "__main__":
    create_self_signed_cert()
