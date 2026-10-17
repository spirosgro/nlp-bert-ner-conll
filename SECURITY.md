# Security and data handling

Keep access tokens, raw datasets, checkpoints and prediction exports out of
public issues. If enabled on GitHub, use private vulnerability reporting for
sensitive findings; otherwise open an issue asking for a private channel without
including sensitive details.

Review model sources before download. Loading uses `trust_remote_code=False`
and safetensors. Examples are authored locally. The project makes no claim to
identify all personal data or to support automatic redaction safely.
