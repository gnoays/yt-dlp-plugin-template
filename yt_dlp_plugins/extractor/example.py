# Don't use relative imports (yt-dlp plugin convention)
from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.utils import float_or_none, int_or_none, url_or_none
from yt_dlp.utils.traversal import traverse_obj


# The class name must end in "IE". For login, caching, playlists etc. see examples/full_example.py
class ExampleIE(InfoExtractor):
    IE_NAME = 'example'
    _VALID_URL = r'https?://(?:www\.)?example\.com/video/(?P<id>[\w-]+)'
    _TESTS = [
        {
            'url': 'https://example.com/video/abc123',
            'only_matching': True,
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video = self._download_json(f'https://api.example.com/v1/videos/{video_id}', video_id)
        return {
            'id': video_id,
            # traverse_obj drops missing keys instead of raising, so API changes degrade gracefully
            **traverse_obj(
                video,
                {
                    'title': ('title', {str}),
                    'description': ('description', {str}),
                    'thumbnail': ('thumbnail', {url_or_none}),
                    'duration': ('duration', {float_or_none}),
                    'formats': (
                        'streams',
                        lambda _, v: url_or_none(v['url']),
                        {
                            'url': 'url',
                            'format_id': ('label', {str}),
                            'height': ('height', {int_or_none}),
                        },
                    ),
                },
            ),
        }
