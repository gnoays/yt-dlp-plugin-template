from yt_dlp import YoutubeDL

from yt_dlp_plugins.postprocessor.example import ExamplePP


def test_run():
    with YoutubeDL({'quiet': True}) as ydl:
        files, info = ExamplePP(ydl).run({'id': 'x', 'title': 't', 'extractor': 'youtube'})
    assert files == []
    assert info['id'] == 'x'


def test_skips_other_extractors():
    info = {'id': 'x', 'extractor': 'youtube'}
    with YoutubeDL({'quiet': True}) as ydl:
        _, result = ExamplePP(ydl, extractors='example').run(info)
    assert result is info
