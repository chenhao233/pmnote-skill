import copy
import importlib.util
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location('index', ROOT / 'scripts/index.py')
index = importlib.util.module_from_spec(spec)
spec.loader.exec_module(index)
reader = index.public


class Thoughts(unittest.TestCase):
    def setUp(self):
        self.work = {'id': 'thought-259', 'title': '工作思考 #259', 'date': '2026-11-03',
                     'dateBasis': 'archive-content-match', 'thought': {'issue': 259,
                     'sourceUrl': 'https://example.com/wiki#heading', 'bodyHash': 'a' * 64,
                     'bodyHtml': '<h3>第一段思考</h3><p>' + '这是一段用于验证完整正文和日期语义的公开测试文字。' * 4 + '</p><hr /><blockquote><p>The main thing.</p></blockquote><p>参考：<a href="https://example.com/?a=1&amp;b=2">原文</a>。</p>'}}

    def test_body_keeps_issue_number_quote_links_and_hides_archive_day(self):
        text = reader.thought_markdown(self.work)
        self.assertTrue(text.startswith('# 工作思考 · 第259期\n'))
        self.assertNotIn('2026-11-03', text)
        self.assertNotIn('写于', text)
        self.assertNotIn('发布于', text)
        self.assertNotIn('最早已知发布', text)
        self.assertIn('## 第一段思考', text)
        self.assertIn('> The main thing.', text)
        self.assertIn('[原文](https://example.com/?a=1&b=2)', text)
        self.assertIn('https://example.com/wiki#heading', text)
        self.assertNotIn('<h3>', text)

    def test_listing_keeps_issue_when_source_title_changes_to_date(self):
        row = {'id': 'thought-259', 'title': '工作思考 2026-11-03', 'publishedAt': '2026-11-03',
               'targets': [{'url': '/community/library/?thought=thought-259', 'local': True, 'mediaType': 'article'}]}
        text = reader.work_listing_markdown(row)
        self.assertIn('[工作思考 · 第259期](https://pmnote.ai/community/library/?thought=thought-259)', text)
        self.assertNotIn('2026-11-03', text)
        self.work['title'] = row['title']
        self.assertTrue(reader.thought_markdown(self.work).startswith('# 工作思考 · 第259期\n'))

    def test_missing_body_identity_date_and_active_html_fail(self):
        changes = [lambda w: w['thought'].update(issue=258), lambda w: w.update(date='2026-02-30'),
                   lambda w: w.update(dateBasis='mtime'), lambda w: w['thought'].update(bodyHtml='<p>摘要</p>'),
                   lambda w: w['thought'].update(bodyHtml='<script>alert(1)</script>'),
                   lambda w: w['thought'].update(bodyHtml='<p><a href="javascript:alert(1)">危险</a></p>')]
        for change in changes:
            work = copy.deepcopy(self.work)
            change(work)
            with self.subTest(change=change), self.assertRaises(ValueError):
                reader.thought_markdown(work)


@unittest.skipUnless(os.environ.get('PMNOTE_CANDIDATE_DIST'), 'Explicit real candidate directory required')
class RealCandidate(unittest.TestCase):
    def test_all_thoughts_discovered_and_read_without_network_or_private_fields(self):
        site = Path(os.environ['PMNOTE_CANDIDATE_DIST'])
        data = json.loads((site / 'agent-page-index.json').read_text())
        with patch.object(reader, 'get_json', side_effect=AssertionError('Network forbidden')):
            evidence = index.verify_thoughts(data, site)
            self.assertEqual(evidence['indexed'], len(data['thoughts']))
            self.assertGreaterEqual(evidence['indexed'], 4)
            initial = {row['id']: row['writtenAt'] for row in evidence['issues'] if row['id'] in {'thought-259', 'thought-258', 'thought-257', 'thought-256'}}
            self.assertEqual(initial, {'thought-259':'2026-11-03', 'thought-258':'2026-10-30', 'thought-257':'2026-10-29', 'thought-256':'2026-10-28'})
            self.assertTrue(all(row['bodyChars'] > 500 and row['referenceLinks'] >= 1 for row in evidence['issues']))
            works = reader.Works(site)
            for row in works.listing(topic='work-thoughts'):
                text = reader.work_markdown(works.detail(row['id']))
                self.assertNotIn('notion.com', text)
                self.assertNotIn('privacyNotes', text)
                self.assertNotIn('写于', text)
                self.assertNotIn('发布于', text)
                self.assertIn('第' + row['id'][8:] + '期', text)
                self.assertNotIn(row['publishedAt'], reader.work_listing_markdown(row))


if __name__ == '__main__':
    unittest.main()
