import pytest
from yt_dlp import YoutubeDL

from yt_dlp_plugins.extractor.example import ExampleIE

VIDEO = {
    'title': 'Hello & World',
    'duration': 90,
    'streams': [{'url': 'https://cdn.example.com/v.mp4', 'label': '720p', 'height': 720}, {'url': None}],
}


def test_suitable():
    assert ExampleIE.suitable('https://example.com/video/abc123')
    assert not ExampleIE.suitable('https://example.com/user/abc123')


def test_extract_offline(monkeypatch):
    monkeypatch.setattr(ExampleIE, '_download_json', lambda self, *args, **kwargs: VIDEO)
    ie = ExampleIE(YoutubeDL({'quiet': True}))
    info = ie._real_extract('https://example.com/video/abc123')
    assert info['id'] == 'abc123'
    assert info['title'] == 'Hello & World'
    assert info['formats'] == [{'url': 'https://cdn.example.com/v.mp4', 'format_id': '720p', 'height': 720}]
    assert 'description' not in info


def test_loaded_as_plugin():
    with YoutubeDL({'quiet': True}) as ydl:
        # yt-dlp re-executes plugin modules on load, so compare by name rather than identity
        assert type(ydl.get_info_extractor('Example')).__qualname__ == ExampleIE.__qualname__


@pytest.mark.network
def test_extract_real():
    with YoutubeDL({'quiet': True, 'skip_download': True}) as ydl:
        info = ydl.extract_info('https://example.com/video/abc123', download=False)
    assert info['extractor_key'] == 'Example'
