# Don't use relative imports (yt-dlp plugin convention)
from yt_dlp.postprocessor.common import PostProcessor


# The class name must end in "PP".
# Enable with: --use-postprocessor "Example:when=after_move;extractors=youtube,example"
class ExamplePP(PostProcessor):
    def __init__(self, downloader=None, extractors=None, **kwargs):
        # Only kwargs can be passed from the CLI, and all values are strings.
        # "downloader", "when" and "key" are reserved names
        super().__init__(downloader)
        self._extractors = set(extractors.split(',')) if extractors else None

    def run(self, info):
        if self._extractors and info.get('extractor') not in self._extractors:
            return [], info
        self.to_screen(f'{info.get("id")}: {info.get("title")}')
        return [], info  # (files to delete, info dict)
