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
- Static cache folders are local-only and ignored by git.
- Runtime logs are written to `logs`.
- Ports `80`, `443`, `42230`, `44325`, and `50051` must be available.
- Binding to ports `80` and `443` may require administrator permissions.

## Local Static Cache

Cosmetics, inventory cards, build-kit categories, and other static catalog data depend on local HTTP cache files from a previously working install. These cache files are not included in this repository.

The launcher checks for a local cache in:

- `cache\http\0\3768241699`
- `%LOCALAPPDATA%\Skate\data\cache\http\0\3768241699`

If neither cache exists, the game can still boot, but `GameData/getData` will return no static chunks and cosmetics or inventory cards may appear empty.

To make a setup self-contained without committing cache files, import a cache from an existing local install:

```powershell
powershell -ExecutionPolicy Bypass -File .\Import_Local_Cache.ps1 -Source "C:\path\to\cache\http\0\3768215040"
```

If no `-Source` is provided, the importer checks the common local Skate cache locations. The generated `cache` and `reference_cache` folders are ignored by git and should stay out of official commits.

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
