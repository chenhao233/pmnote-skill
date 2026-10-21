import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('index', Path(__file__).parents[1] / 'scripts/index.py')
index = importlib.util.module_from_spec(spec)
spec.loader.exec_module(index)


class SourceValidation(unittest.TestCase):
    def setUp(self):
        paths = ['/articles/a', '/podcast/a', '/glossary/a', '/job-market/jobs/a', '/services', '/', '/tools/tripo']
        self.data = {'schemaVersion': 3, 'siteBase': 'https://pmnote.ai',
                     'pages': [{'url': 'https://pmnote.ai' + p, 'title': p} for p in paths],
                     'catalog': [{'url': 'https://www.bilibili.com/video/test/', 'title': 'test'}],
                     'interviews': [{'id': '11111111-1111-4111-8111-111111111111', 'title': '面试复盘', 'sharer': '分享者', 'status': 'published', 'sections': [{'heading': '一面', 'kind': 'questions', 'items': ['怎样拆解排期？']}]}]}

    def test_all_entries_survive_in_one_category(self):
        result = index.render(self.data, '2026-10-03')
        links = [u for key in index.TITLES for u in index.LINK.findall(result[key + '.md'])]
        expected = [r['url'] for key in ('pages', 'catalog') for r in self.data[key]]
        expected += [index.public.canonical(row['id']) for row in self.data['interviews']]
        self.assertCountEqual(links, expected)

    def test_invalid_source_does_not_render(self):
        for value in ['http://pmnote.ai/a', 'https://pmnote.ai.evil.example/a', 'file:///tmp/a',
                      'https://pmnote.ai/a?token=secret', 'https://pmnote.ai/a)\n# injected']:
            with self.subTest(url=value), self.assertRaises(ValueError):
                data = copy.deepcopy(self.data)
                data['pages'][0]['url'] = value
                index.render(data, '2026-10-03')

    def test_incomplete_and_duplicate_source_rejected(self):
        for mutate in (lambda d: d.update(catalog=[]),
                       lambda d: d['pages'].append(d['pages'][0]),
                       lambda d: d.update(schemaVersion=4)):
            with self.assertRaises(ValueError):
                data = copy.deepcopy(self.data)
                mutate(data)
                index.render(data, '2026-10-03')

    def test_title_cannot_inject_markdown_link(self):
        self.data['pages'][0]['title'] = '[click](https://example.com) <script>'
        result = index.render(self.data, '2026-10-03')['articles.md']
        self.assertIn('\\[click\\]', result)
        self.assertNotIn('<script>', result)

    def test_channel_groups_preserve_links_and_order_within_each_platform(self):
        self.data['catalog'] = [
            {'url': 'https://' + host + '/' + item, 'title': item}
            for host, item in [('www.bilibili.com', 'b1'),
                               ('www.xiaoyuzhoufm.com', 'x1'),
                               ('zhuanlan.zhihu.com', 'z1'),
                               ('www.xiaoyuzhoufm.com', 'x2'),
                               ('www.bilibili.com', 'b2')]]
        body = index.render(self.data, '2026-10-04')['channels.md']
        sections = body.split('\n## ')[1:]
        expected = [('小宇宙', 'www.xiaoyuzhoufm.com'),
                    ('知乎', 'zhuanlan.zhihu.com'), ('B站', 'www.bilibili.com')]
        self.assertEqual(len(sections), len(expected))
        for section, (title, host) in zip(sections, expected):
            with self.subTest(platform=title):
                self.assertEqual(section.splitlines()[0], title)
                urls = index.LINK.findall(section)
                self.assertEqual(urls, [r['url'] for r in self.data['catalog']
                                       if index.valid_url(r['url']).netloc == host])
        self.assertCountEqual(index.LINK.findall(body),
                              [r['url'] for r in self.data['catalog']])

    def test_catalog_cannot_silently_drop_an_unsupported_platform(self):
        self.data['catalog'].append({'url': 'https://pmnote.ai/article', 'title': 'test'})
        with self.assertRaisesRegex(ValueError, 'Unexpected channel platform'):
            index.render(self.data, '2026-10-04')

    def test_dynamic_interviews_cannot_be_omitted_or_withdrawn(self):
        for value in (None, [], [{**self.data['interviews'][0], 'status': 'withdrawn'}]):
            with self.subTest(value=value), self.assertRaises(ValueError):
                index.render({**self.data, 'interviews': value}, '2026-10-21')

    def test_interview_body_keeps_attribution_canonical_and_last_question(self):
        item = self.data['interviews'][0]
        body = index.public.interview_markdown(item)
        self.assertIn('分享人 @分享者', body)
        self.assertIn(index.public.canonical(item['id']), body)
        self.assertIn('怎样拆解排期？', body)
        index.valid_url(index.public.canonical(item['id']))
        with self.assertRaises(ValueError):
            index.valid_url('https://pmnote.ai/community/experiences/#entry=not-a-uuid')
        with self.assertRaises(ValueError):
            index.public.interview_markdown({**item, 'sections': [], 'body': ''})

    def test_incomplete_pagination_and_mismatched_details_are_rejected(self):
        api = object.__new__(index.public.Interviews)
        api.call = lambda *_: {'items': self.data['interviews'], 'hasMore': False}
        self.assertEqual(len(api.listing()), 1, 'current live API need not provide total')
        api.call = lambda *_: {'items': [], 'hasMore': True}
        with self.assertRaisesRegex(ValueError, 'no pagination progress'):
            api.listing()
        api.call = lambda *_: {'items': self.data['interviews'], 'total': 2, 'hasMore': False}
        with self.assertRaisesRegex(ValueError, 'Incomplete interview coverage'):
            api.listing()
        api.call = lambda *_: self.data['interviews'][0]
        with self.assertRaisesRegex(ValueError, 'identity mismatch'):
            api.detail('22222222-2222-4222-8222-222222222222')


if __name__ == '__main__':
    unittest.main()
