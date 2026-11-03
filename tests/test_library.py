import copy
import datetime
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location('reader', ROOT / 'pmnote/scripts/read.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


class WorkReader(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.site = Path(self.temp.name)
        date = '2026-08-22T06:08:50.000Z'
        millis = int(datetime.datetime.fromisoformat(date.replace('Z', '+00:00')).timestamp() * 1000)
        targets = [('zhihu:123', 'https://zhuanlan.zhihu.com/p/123', 'article', '知乎原题'),
                   ('xiaoyuzhou:abc', 'https://www.xiaoyuzhoufm.com/episode/abc', 'podcast', '第162期 JIRA 原题'),
                   ('local:/articles/demo/', '/articles/demo/', 'article', '站内原题')]
        self.index = {'version': 8, 'full': True, 'revision': 'test', 'topics': [['ai', 'AI']],
                      'counts': {'works': 1, 'platformVariants': 2, 'localTargets': 1},
                      'redirects': {'zhihu:123': 'demo-work'},
                      'works': [['demo-work', '合并作品', '轻摘要', 5, 1, millis,
                                 [['zhihu:123', 0], ['xiaoyuzhou:abc', 2], ['local:/articles/demo/', 4]],
                                 1, reader.search_key('知乎原题 第162期 JIRA 原题 站内原题')]]}
        self.detail = {'schemaVersion': 1, 'workId': 'demo-work',
                       'work': {'id': 'demo-work', 'title': '合并作品', 'date': date,
                                'aliases': ['合并作品', *[t[3] for t in targets]]},
                       'platformVariants': [], 'localTargets': []}
        for identity, url, media, title in targets:
            local = identity.startswith('local:')
            record = {'variantId': identity, 'workId': 'demo-work', 'url': url,
                      'platform': 'pmnote' if local else identity.split(':')[0], 'mediaType': media,
                      'title': title, 'publishedAt': date, 'updatedAt': '2026-10-21' if local else None,
                      'summary': title + '：完整来源摘要末尾。',
                      'summaryKind': 'frontmatter_metadata_not_body' if local else 'source_metadata_not_body',
                      'media': {'audioUrl': 'https://audio.example/episode.m4a'} if media == 'podcast' else None}
            self.detail['localTargets' if local else 'platformVariants'].append(record)
        self.write(reader.LIBRARY + 'index.json', self.index)
        self.write(reader.work_path('demo-work'), self.detail)

    def write(self, path, data):
        file = self.site / path.lstrip('/')
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps(data), encoding='utf-8')

    def test_offline_search_alias_and_old_id_keep_complete_detail(self):
        with patch.object(reader, 'get_json', side_effect=AssertionError('Network forbidden')):
            works = reader.Works(self.site)
            self.assertEqual(works.listing('ＪＩＲＡ 第162期')[0]['id'], 'demo-work')
            self.assertEqual(works.listing('JIRA', media='video'), [])
            self.assertEqual(works.detail('zhihu:123'), self.detail)
            self.assertIn('完整来源摘要末尾', reader.work_markdown(self.detail))
            self.assertIn('https://pmnote.ai/articles/demo/', reader.work_markdown(self.detail))
            self.assertNotIn('?', works.listing()[0]['readUrl'])

    def test_public_mode_requests_only_index_and_canonical_detail(self):
        calls = []
        def get(url):
            calls.append(url)
            return self.index if url.endswith('index.json') else self.detail
        with patch.object(reader, 'get_json', side_effect=get):
            self.assertEqual(reader.Works().detail('zhihu:123'), self.detail)
        self.assertEqual(calls, [reader.BASE + reader.LIBRARY + 'index.json', reader.BASE + reader.work_path('demo-work')])

    def test_partial_counts_duplicate_versions_and_redirect_cycles_fail(self):
        for mutate in (lambda d: d.update(full=False), lambda d: d.update(version=9),
                       lambda d: d['counts'].update(works=2), lambda d: d['works'].append(d['works'][0]),
                       lambda d: d['redirects'].update(a='b', b='a')):
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                value = copy.deepcopy(self.index)
                mutate(value)
                self.write(reader.LIBRARY + 'index.json', value)
                reader.Works(self.site)

    def test_wrong_detail_id_missing_variant_and_changed_url_fail(self):
        works = reader.Works(self.site)
        for mutate in (lambda d: d.update(workId='other'), lambda d: d['platformVariants'].pop(),
                       lambda d: d['platformVariants'][0].update(url='https://wrong.example/'),
                       lambda d: d['work'].update(title='changed')):
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                value = copy.deepcopy(self.detail)
                mutate(value)
                self.write(reader.work_path('demo-work'), value)
                works.detail('demo-work')

    def test_missing_local_source_never_falls_back_to_production(self):
        (self.site / reader.work_path('demo-work').lstrip('/')).unlink()
        with patch.object(reader, 'get_json', side_effect=AssertionError('Network forbidden')):
            with self.assertRaisesRegex(ValueError, 'no online fallback'):
                reader.Works(self.site).detail('demo-work')

    def test_reader_and_listing_link_direct_body_or_selected_programme(self):
        work = reader.Works(self.site).listing()[0]
        self.assertIn('](https://pmnote.ai/articles/demo/)', reader.work_listing_markdown(work))
        self.assertIn('](https://www.xiaoyuzhoufm.com/episode/abc)', reader.work_listing_markdown(work, 'podcast'))
        body = reader.work_markdown(self.detail)
        self.assertEqual(body.splitlines()[2], '原文：https://pmnote.ai/articles/demo/')
        self.assertEqual(reader.work_markdown(self.detail, 'podcast').splitlines()[2], '原文：https://www.xiaoyuzhoufm.com/episode/abc')
        self.assertIn('发布于：2026-08-22', body)
        self.assertNotIn('已知发布', body)
        self.assertNotIn('作品资料：', body)

    def test_dates_use_beijing_day_and_unknown_is_not_displayed(self):
        self.assertEqual(reader.publication_day('2022-10-15T17:01:29Z'), '2022-10-16')
        self.assertEqual(reader.publication_day('2022-10-15'), '2022-10-15')
        work = reader.Works(self.site).listing()[0]
        work['publishedAt'] = ''
        self.assertNotIn('发布于', reader.work_listing_markdown(work))
        self.detail['work']['date'] = ''
        for variant in self.detail['platformVariants'] + self.detail['localTargets']:
            variant['publishedAt'] = None
        body = reader.work_markdown(self.detail)
        self.assertNotIn('发布于', body)
        self.assertNotIn('待核', body)

    def test_primary_avoids_shownotes_and_removed_source_intermediary(self):
        targets = [{'url': '/community/library/?work=demo&panel=sources', 'local': True, 'mediaType': 'article'},
                   {'url': '/podcast/demo/', 'local': True, 'mediaType': 'podcast'},
                   {'url': 'https://www.xiaoyuzhoufm.com/episode/abc', 'local': False, 'mediaType': 'podcast'}]
        self.assertEqual(reader.primary_url(targets), targets[2]['url'])
        with self.assertRaisesRegex(ValueError, 'No direct'):
            reader.primary_url(targets[:1])


@unittest.skipUnless(os.environ.get('PMNOTE_CANDIDATE_DIST'), 'Explicit real candidate directory required')
class CandidateWorks(unittest.TestCase):
    def test_every_current_detail_and_original_title_is_readable(self):
        with patch.object(reader, 'get_json', side_effect=AssertionError('Network forbidden')):
            works = reader.Works(os.environ['PMNOTE_CANDIDATE_DIST'])
            total = 0
            for work in works.works:
                detail = works.detail(work['id'])
                direct = reader.primary_url(work['targets'])
                self.assertNotIn('panel=sources', direct)
                self.assertNotIn('?work=', direct)
                self.assertIn('](' + direct + ')', reader.work_listing_markdown(work))
                if not work['id'].startswith('thought-'):
                    self.assertEqual(reader.work_markdown(detail).splitlines()[2], '原文：' + direct)
                total += len(detail['platformVariants']) + len(detail['localTargets'])
                for title in detail['work']['aliases']:
                    self.assertIn(work['id'], [w['id'] for w in works.listing(title)])
            self.assertEqual(total, works.index['counts']['platformVariants'] + works.index['counts']['localTargets'])
            self.assertTrue(works.listing('JIRA'))
            self.assertTrue(works.listing('第162期'))
            money = works.detail('hao-ai-economics-money')
            self.assertEqual(len(money['platformVariants']), 2)
            for old in ('zhihu:2074497837753169589', 'xiaoyuzhou:6a89398c1352af56ff3a2665'):
                self.assertEqual(works.detail(old), money)
            self.assertEqual({v['publishedAt'] for v in money['platformVariants']},
                             {'2026-08-22T06:08:50.000Z', '2026-08-22T06:09:20.000Z'})


if __name__ == '__main__':
    unittest.main()
