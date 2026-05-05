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

## Custom Parks

Custom park files go in `custom_parks`.

The filename is the code you enter in-game. For example, the included `custom_parks/parklol` file uses code `parklol`.

Supported filename styles include no extension, `.txt`, `.json`, `.dmop`, and `.park`.

To load a custom park:

1. Use the map to fast travel into a private park.
2. Open `Create`.
3. Open `My Parks`.
4. Select `Enter Park Code`.
5. Enter the filename code, such as `parklol`.

After the park loads, you can choose `Save Park as New` from `My Parks` to save it locally. Once it is saved locally, it appears in the park list and you do not need to enter the code every time.
