# nginx/certs



This directory stores locally trusted development SSL certificates (e.g., created using `mkcert`).

**Do not** commit any `.pem` or `.key` files to version control. These files are sensitive and machine-specific.

If you're setting up HTTPS locally, use a tool like `mkcert` to generate:

- `cert.pem` – The certificate
- `key.pem` – The private key

Add your generated certs here, and make sure they are ignored by Git.
