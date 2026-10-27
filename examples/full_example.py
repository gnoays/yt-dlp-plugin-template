# Reference extractor showing common building blocks: login, cache, API helper, extractor args,
# metadata via traverse_obj, playlists. It lives outside yt_dlp_plugins/ so it is neither loaded
# by yt-dlp nor packaged; copy the parts you need into your plugin.
# Don't use relative imports (yt-dlp plugin convention)
import itertools
import time

from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.networking.exceptions import HTTPError
from yt_dlp.utils import (
    ExtractorError,
    float_or_none,
    int_or_none,
    parse_iso8601,
    url_or_none,
    urlencode_postdata,
)
from yt_dlp.utils.traversal import traverse_obj


# Shared logic lives in a base class whose name starts with "_" so it is not registered as an extractor
class _ExampleBaseIE(InfoExtractor):
    _API_BASE = 'https://api.example.com/v1'
    # Enables -u/-p, --netrc and --netrc-cmd; yt-dlp then calls _perform_login once per extractor instance
    _NETRC_MACHINE = 'example'
    _token = None

    def _perform_login(self, username, password):
        # Every extractor class logs in separately, so reuse the token across classes and runs
        # (stored under ~/.cache/yt-dlp, cleared with --rm-cache-dir)
        cached = self.cache.load('example', username)
        if cached and cached.get('expires', 0) > time.time():
            self._token = cached['token']
            return
        try:
            data = self._download_json(
                f'{self._API_BASE}/login',
                None,
                'Logging in',
                data=urlencode_postdata({'email': username, 'password': password}),
            )
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status == 401:
                # expected=True: a user error, so no "please report this bug" message
                raise ExtractorError('Invalid username or password', expected=True) from e
            raise
        self._token = data['token']
        expires_in = int_or_none(data.get('expires_in')) or 3600
        self.cache.store('example', username, {'token': self._token, 'expires': time.time() + expires_in})

    def _call_api(self, path, item_id, note='Downloading API JSON', query=None, **kwargs):
        # --extractor-args "example:lang=ja"; ie_key makes the option shared by all classes in this plugin
        lang = self._configuration_arg('lang', ['en'], ie_key='example')[0]
        headers = {'Authorization': f'Bearer {self._token}'} if self._token else {}
        return self._download_json(
            f'{self._API_BASE}/{path}', item_id, note, query={'lang': lang, **(query or {})}, headers=headers, **kwargs
        )

    def _extract_video(self, video, video_id):
        formats = []
        for stream in traverse_obj(video, ('streams', lambda _, v: url_or_none(v['url']))):
            if stream.get('type') == 'hls':
                # fatal=False: one broken stream should not fail the whole extraction
                formats.extend(self._extract_m3u8_formats(stream['url'], video_id, 'mp4', m3u8_id='hls', fatal=False))
            else:
                formats.append(
                    {
                        'url': stream['url'],
                        **traverse_obj(
                            stream,
                            {
                                'format_id': ('label', {str}),
                                'height': ('height', {int_or_none}),
                                'tbr': ('bitrate', {int_or_none}),
                            },
                        ),
                    }
                )
        if not formats and video.get('premium') and not self._token:
            self.raise_login_required('This video is only available to premium members', method='password')

        return {
            'id': video_id,
            'formats': formats,
            # traverse_obj drops missing keys instead of raising, so API changes degrade gracefully
            **traverse_obj(
                video,
                {
                    'title': ('title', {str}),
                    'description': ('description', {str}),
                    'thumbnail': ('thumbnail', {url_or_none}),
                    'duration': ('duration', {float_or_none}),
                    'timestamp': ('published_at', {parse_iso8601}),
                    'uploader': ('channel', 'name', {str}),
                    'uploader_id': ('channel', 'id', {str}),
                    'tags': ('tags', ..., {str}),
                    'chapters': (
                        'chapters',
                        lambda _, v: v['start'] is not None,
                        {
                            'title': ('title', {str}),
                            'start_time': ('start', {float_or_none}),
                        },
                    ),
                },
            ),
        }


# The class name must end in "IE"
class ExampleIE(_ExampleBaseIE):
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
        video = self._call_api(f'videos/{video_id}', video_id)
        return self._extract_video(video, video_id)


class ExamplePlaylistIE(_ExampleBaseIE):
    IE_NAME = 'example:playlist'
    _VALID_URL = r'https?://(?:www\.)?example\.com/playlist/(?P<id>[\w-]+)'
    _TESTS = [
        {
            'url': 'https://example.com/playlist/pl1',
            'only_matching': True,
        }
    ]

    # A generator is fetched lazily: --playlist-items 1-5 stops after the first page.
    # For APIs with page numbers use OnDemandPagedList (total unknown) or InAdvancePagedList
    # (total known), which can jump straight to the requested page.
    def _entries(self, playlist_id):
        cursor = None
        for page in itertools.count(1):
            data = self._call_api(
                f'playlists/{playlist_id}/videos',
                playlist_id,
                f'Downloading page {page}',
                query={'cursor': cursor} if cursor else None,
            )
            for video_id in traverse_obj(data, ('items', ..., 'id', {str})):
                # Hand each entry over to ExampleIE instead of extracting it here
                yield self.url_result(f'https://example.com/video/{video_id}', ExampleIE, video_id)
            cursor = data.get('next_cursor')
            if not cursor:
                break

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        meta = self._call_api(f'playlists/{playlist_id}', playlist_id, 'Downloading playlist metadata')
        return self.playlist_result(
            self._entries(playlist_id),
            playlist_id,
            **traverse_obj(
                meta,
                {
                    'title': ('title', {str}),
                    'description': ('description', {str}),
                },
            ),
        )
