# TiDES-RM file downloads

This endpoint returns original FITS files, without conversion. It uses dedicated
bearer tokens, independent of TOM users and passwords. It does not expose a
directory listing.

## Deploy

1. Mount the TiDES-RM storage on the Compose host at `/mnt/data/tidesrm`.
   The production Compose file mounts that directory read-only inside the web
   container at `/data/tidesrm`. Ensure the container's web process can read
   the files and traverse the directories. The bind mount refuses to create a
   missing host path, so the web container will not start until it exists.
   Verify that the actual storage is mounted there, not just an empty directory.
2. Set `TIDESRM_TOKEN_SHA256` in the Compose environment or deployment secrets
   to a comma-separated list of SHA-256 hashes, one per collaborator token.
   No tokens, or a malformed hash, disables the endpoint with HTTP 503. These
   are hashes of high-entropy random tokens, not hashes of user-chosen passwords.
3. Rebuild and recreate the web container using the site's normal deployment
   procedure. Changing environment variables requires recreating the container.
4. Ensure requests reach the endpoint **only over HTTPS**, the proxy forwards the
   `Authorization` header, and the directly published Gunicorn port is not
   accessible to untrusted clients. This view does not enforce HTTPS itself.
   Confirm the full proxy route and authentication with a real external request.
   Do not log authorization headers or enable caching of these responses.
5. Apply rate limits at the proxy if needed. Authorized users can still download
   every date they know or discover; these tokens grant access to both processing
   environments and do not provide per-file permissions or download auditing.

When multiple files match, a temporary uncompressed ZIP is built on the web
container's temporary filesystem before the response is sent. Provision enough
temporary disk space for the combined files and avoid large concurrent requests.
The serving directory must be writable only by trusted storage administrators:
the view rejects symlinks, but cannot protect against files being swapped by a
writer during a request.

## Provision and revoke tokens

Generate a different random token for each collaborator. For example, on a
trusted machine with OpenSSL, run the following in a private shell:

```bash
TOKEN=$(openssl rand -hex 32)
printf '%s' "$TOKEN" | openssl dgst -sha256
```

Place only the resulting hexadecimal digest in `TIDESRM_TOKEN_SHA256`, and
securely convey the original value of `TOKEN` to the collaborator. Treat token
values like passwords: do not commit them, share them through chat, put them in
URLs, or log request headers. Protect the deployment environment file and shell
history. Revoke a token by removing its digest and recreating the web container;
existing in-flight downloads are not interrupted. Repeat for each collaborator.

## Download

The production route, assuming the configured `/marshal` prefix, is:

`GET /marshal/api/tidesrm/download/YYYYMMDD/?process_env=operations`

Use the observing date, not the processing date. `process_env` defaults to
`operations`; `reproc` is the only other accepted value. Within the selected
environment and date directory the filename must match
`YYYYMMDD_LJ11_<eight-digit-processing-date>_S1003.fits`, with the first date
matching the requested date. If one file matches, the original FITS is returned;
if multiple files match, they are returned together in a ZIP. No matches return
404. Invalid dates and environments return 400, invalid or missing tokens 401,
and unavailable storage or token configuration 503.

For example, after securely setting `TOKEN` in a private shell:

```bash
wget --content-disposition --header="Authorization: Bearer $TOKEN" \
  'https://tides.lsst.ac.uk/marshal/api/tidesrm/download/20260202/?process_env=reproc'
```

The `--header` argument can be visible in the local process list. On shared
machines use a protected wget configuration file or another client that can
read credentials securely rather than placing the token in command arguments.
Verify the actual public hostname and HTTPS proxy configuration before use.