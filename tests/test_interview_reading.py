import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location('interview_index', Path(__file__).parents[1] / 'scripts/index.py')
index = importlib.util.module_from_spec(spec)
spec.loader.exec_module(index)
public = index.public

LIVE_ID = '11111111-1111-4111-8111-111111111111'
ARCHIVE_ID = '22222222-2222-4222-8222-222222222222'
PAGE = public.BASE + '/community/experiences/'
OWNED_API = public.BASE + '/api/public-reading/interviews'
LEGACY_API = public.COMMUNITY_ORIGIN + '/functions/v1/community'
LEGACY_ATTRS = f'data-community-url="{public.COMMUNITY_ORIGIN}" data-community-key="fixture-publishable"'
LIVE = {'id': LIVE_ID, 'title': '项目管理面试', 'status': 'published', 'sharer': '公开分享者'}
ARCHIVE = {'id': ARCHIVE_ID, 'sourceKey': 'ix-01', 'title': '归档摘要',
           'originalTitle': '归档原题', 'sharer': '归档分享者', 'roleText': '游戏项目管理'}
ARCHIVE_HTML = f'<article data-interview-archive-id="{ARCHIVE_ID}"><h1>归档原题</h1>\n' \
               '<section data-interview-section="author_reflection"><h2>复盘</h2>\n' \
               '<p>原文 <em>与排期</em> &amp; 风险复盘</p></section><p class="attribution">分享人 @归档分享者</p></article>'


def owned_page(entries):
    return (f'<body data-public-reading="true" {LEGACY_ATTRS}>\n'
            '<script type="application/json" id="interview-archive">'
            f'{json.dumps(entries)}</script></body>')


class InterviewPublicReading(unittest.TestCase):
    def test_legacy_before_cutover_keeps_original_public_key_and_origin(self):
        result = {'items': [{**LIVE, 'body': '公开正文'}], 'hasMore': False}
        for attrs in (LEGACY_ATTRS, 'data-public-reading="false" ' + LEGACY_ATTRS):
            with self.subTest(attrs=attrs), patch.object(public, 'request', side_effect=[f'<body {attrs}>', json.dumps(result)]) as request:
                self.assertEqual(public.Interviews().listing(), result['items'])
                request.assert_called_with(LEGACY_API, {'action': 'interviews_list', 'payload': {'page': 0, 'q': ''}},
                                           {'Origin': public.BASE, 'apikey': 'fixture-publishable'})

    def test_owned_listing_merges_verified_archive_and_preserves_search_and_detail(self):
        routes = {PAGE: owned_page([ARCHIVE]), PAGE + ARCHIVE_ID + '/': ARCHIVE_HTML,
                  PAGE + 'archive-search.json': json.dumps({ARCHIVE_ID: '原文与排期及风险复盘'})}

        def request(url, payload=None, headers=None):
            if url in routes:
                self.assertIsNone(payload)
                self.assertIsNone(headers)
                return routes[url]
            self.assertEqual(url, OWNED_API)
            self.assertEqual(headers, {})
            if payload['action'] == 'interviews_detail':
                self.assertEqual(payload['payload'], {'id': LIVE_ID})
                return json.dumps({**LIVE, 'body': '此处是公开正文'})
            self.assertEqual(payload['action'], 'interviews_list')
            rows = [] if payload['payload']['q'] else [LIVE, {**LIVE, 'id': ARCHIVE_ID}]
            return json.dumps({'items': rows, 'hasMore': False, 'total': len(rows)})

        with patch.object(public, 'request', side_effect=request):
            api = public.Interviews()
            live, archived = api.listing()
            self.assertEqual(live, LIVE)
            self.assertEqual(archived['title'], '归档原题')
            self.assertEqual([row['id'] for row in api.listing('风险复盘')], [ARCHIVE_ID])
            self.assertIn('此处是公开正文', index.verify_interview_detail(live, api.detail(LIVE_ID)))
            self.assertIn('原文 与排期 & 风险复盘', index.verify_interview_detail(archived, api.detail(ARCHIVE_ID)))

    def test_owned_transport_failure_does_not_fall_back_to_legacy(self):
        with patch.object(public, 'request', side_effect=[owned_page([]), ValueError('Public source HTTP 503')]) as request:
            with self.assertRaisesRegex(ValueError, '503'):
                public.Interviews().listing()
            self.assertEqual(request.call_count, 2)
            self.assertEqual(request.call_args.args[0], OWNED_API)

    def test_owned_archive_detail_requires_matching_identity_attribution_and_body(self):
        for html in (ARCHIVE_HTML.replace(ARCHIVE_ID, LIVE_ID),
                     ARCHIVE_HTML.replace('归档分享者', '其他人'),
                     ARCHIVE_HTML.replace('原文 <em>与排期</em> &amp; 风险复盘', '')):
            with self.subTest(html=html), patch.object(public, 'request', side_effect=[owned_page([ARCHIVE]), html]):
                with self.assertRaisesRegex(ValueError, 'interview archive|Interview archive'):
                    public.Interviews().detail(ARCHIVE_ID)

    def test_markdown_keeps_prose_and_sections_without_duplicates(self):
        detail = {**LIVE, 'body': '单独的原文', 'sections': [{'heading': '复盘', 'items': ['复盘文字']}]}
        markdown = public.interview_markdown(detail)
        self.assertEqual(markdown.count('单独的原文'), 1)
        self.assertEqual(markdown.count('复盘文字'), 1)
        self.assertEqual(public.interview_markdown({**detail, 'body': '复盘文字'}).count('复盘文字'), 1)

    def test_detail_verification_requires_current_body_and_legacy_equality(self):
        full = {**LIVE, 'body': '可验证正文'}
        self.assertIn('可验证正文', index.verify_interview_detail(LIVE, full))
        with self.assertRaisesRegex(ValueError, 'body missing'):
            index.verify_interview_detail(LIVE, LIVE)
        for sample in ({**LIVE, 'sharer': '其他人'}, {**LIVE, 'body': '旧正文'}):
            with self.assertRaisesRegex(ValueError, 'changed'):
                index.verify_interview_detail(sample, full)


if __name__ == '__main__':
    unittest.main()
