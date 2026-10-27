# yt-dlp-example-plugin

A [yt-dlp](https://github.com/yt-dlp/yt-dlp) plugin that adds support for example.com.

## Installation

Requires a recent version of yt-dlp (tested with the latest release).

**pip**

```
pip install -U yt-dlp-example-plugin
```

**uv tool**

```
uv tool install yt-dlp --with yt-dlp-example-plugin
```

**Standalone executable (yt-dlp.exe etc.)**

Download the `.zip` file from [Releases](https://github.com/gnoays/yt-dlp-example-plugin/releases)
and place it in one of the yt-dlp plugin directories, e.g. `%APPDATA%\yt-dlp\plugins\` on Windows
or `~/.config/yt-dlp/plugins/` on Linux/macOS.

See [installing yt-dlp plugins](https://github.com/yt-dlp/yt-dlp#installing-plugins) for all options.

Run `yt-dlp -v` and check that the plugin is listed under `[debug] Extractor Plugins`.

## Usage

```
yt-dlp https://example.com/video/abc123
```

The post-processor is opt-in:

```
yt-dlp --use-postprocessor "Example:when=after_move;extractors=example" URL
```

To enable it permanently, put that option in your
[yt-dlp config file](https://github.com/yt-dlp/yt-dlp#configuration).

## Development

```
uv sync                                   # installs this plugin (editable) + yt-dlp
uv run yt-dlp -v --skip-download URL
uv run pytest                             # offline tests
uv run pytest -m network                  # tests against the real site
uv run ruff check . && uv run ruff format .
```

See the [Plugin Development](https://github.com/yt-dlp/yt-dlp/wiki/Plugin-Development) wiki page.

Release: bump `version` in `pyproject.toml`, then push a tag (`git tag v0.1.0 && git push --tags`).
The release workflow builds the wheel and a drop-in zip, attaches them to a GitHub release and publishes to PyPI.

## Using this repository as a template

1. Rename `yt-dlp-example-plugin` in `pyproject.toml` and this README
2. Rename `yt_dlp_plugins/*/example.py` to a unique module name (all plugins share one namespace)
3. Set up [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) for `release.yml`

`examples/full_example.py` is a reference extractor (login, cache, API helper, extractor args,
playlists) with tests. It is not packaged or loaded by yt-dlp; copy what you need, then delete the folder.
