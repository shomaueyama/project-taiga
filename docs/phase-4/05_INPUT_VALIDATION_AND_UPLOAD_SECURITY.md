# Input Validation and Upload Security

## Input Validation Changes

- Request models now forbid unknown fields where client input is accepted.
- User-controlled strings have explicit maximum lengths.
- Arrays such as upload IDs and exam answers have bounded lengths.
- Numeric fields such as upload sizes have explicit ranges.
- Security-sensitive booleans must parse as true or false and fail closed otherwise.
- Malformed JSON is handled as validation failure without stack traces.

## Upload Rules

Accepted upload metadata must satisfy:

- original filename is non-empty and at most 255 characters,
- no control characters,
- no absolute paths or home-relative paths,
- no `/`, `\`, `..`, or `:` path markers,
- extension is in the allowlist,
- media type matches the extension allowlist,
- size is greater than zero and no larger than 50 MiB,
- SHA-256 is exactly 64 lowercase hexadecimal characters.

Storage keys are generated from principal ID, upload ID, and a safe extension. The original filename is preserved only as metadata and is not used to construct storage paths.

## Tested Attacks

- `../` and absolute path traversal,
- empty files,
- extension spoofing through double extensions,
- MIME mismatch,
- unsafe shell-looking runner payloads,
- unknown request fields,
- malformed JSON.

## Deferred Controls

- Content scanning is not implemented.
- Archive uploads are not accepted; decompression-bomb handling remains out of scope.
- Actual object-store signed URL enforcement is deferred until the AWS adapter phase.
