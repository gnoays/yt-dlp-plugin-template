import itertools

import pytest
from yt_dlp import YoutubeDL

from examples.full_example import ExampleIE, ExamplePlaylistIE, _ExampleBaseIE

API = 'https://api.example.com/v1'


@pytest.fixture
def api(monkeypatch):
    """Replace network access with a dict of {url: response}; records every request."""
    responses, calls = {}, []

    def fake_download_json(self, url, video_id, note=None, *args, **kwargs):
        calls.append({'url': url, **kwargs})
        response = responses[url]
        return response(kwargs.get('query') or {}) if callable(response) else response

    monkeypatch.setattr(_ExampleBaseIE, '_download_json', fake_download_json)
    return responses, calls


def make_ie(cls, **params):
    # cachedir=False keeps tests from touching ~/.cache/yt-dlp
    return cls(YoutubeDL({'quiet': True, 'cachedir': False, **params}))


def test_extract_offline(api):
    responses, _ = api
    responses[f'{API}/videos/abc123'] = {
        'title': 'Hello',
        'chapters': [{'title': 'Intro', 'start': 0}, {'title': 'Broken', 'start': None}],
        'streams': [{'type': 'mp4', 'url': 'https://cdn.example.com/v.mp4'}],
    }
    info = make_ie(ExampleIE)._real_extract('https://example.com/video/abc123')
    assert info['title'] == 'Hello'
    assert info['chapters'] == [{'title': 'Intro', 'start_time': 0}]
    assert info['formats'] == [{'url': 'https://cdn.example.com/v.mp4'}]


def test_login_and_extractor_args_are_sent(api):
    responses, calls = api
    responses[f'{API}/login'] = {'token': 'tok'}
    responses[f'{API}/videos/abc123'] = {'title': 'Hello'}
    ie = make_ie(ExampleIE, extractor_args={'example': {'lang': ['ja']}})
    ie._perform_login('user@example.com', 'pass')
    ie._real_extract('https://example.com/video/abc123')
    assert calls[-1]['headers'] == {'Authorization': 'Bearer tok'}
    assert calls[-1]['query'] == {'lang': 'ja'}


def test_playlist_is_lazy(api):
    responses, calls = api
    responses[f'{API}/playlists/pl1'] = {'title': 'My list'}
    responses[f'{API}/playlists/pl1/videos'] = lambda query: {
        'items': [{'id': f'{query.get("cursor", "p1")}-{i}'} for i in range(3)],
        'next_cursor': 'p2' if 'cursor' not in query else None,
    }
    info = make_ie(ExamplePlaylistIE)._real_extract('https://example.com/playlist/pl1')
    assert [e['id'] for e in itertools.islice(info['entries'], 2)] == ['p1-0', 'p1-1']
    assert len(calls) == 2  # metadata + first page only
    assert [e['id'] for e in info['entries']][-1] == 'p2-2'
