# Skateboarding Preservation Project

Small local tooling for preserving access to an archived prototype environment.

## Start Here

Run `RUN_PRESERVATION_PROJECT.bat`.

## Usage

1. Place these files beside a supported local client build.
2. Run `RUN_PRESERVATION_PROJECT.bat`.
3. The launcher prepares a local preservation client on first run, starts the required local services, and closes those services when the client exits.

## Notes

- No original game assets are included.
- No original executable is included.
- Runtime logs are written to `logs`.
- Ports `80`, `443`, `42230`, `44325`, and `50051` must be available.
- Binding to ports `80` and `443` may require administrator permissions.
