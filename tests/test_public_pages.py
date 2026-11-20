import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('public_reader', Path(__file__).parents[1] / 'pmnote/scripts/read.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
ID = '00000000-0000-4000-8000-000000000001'


class PublicPages(unittest.TestCase):
    def test_current_question_and_sources_without_private_ui(self):
        html = '<body data-public-rendered="true"><form>PRIVATE-DRAFT</form><div data-ex-list><article><h3>问题</h3><p>原回答[7]</p><noscript><a href="https://pmnote.ai/articles/a/">原始来源</a></noscript><button>分享操作</button><div hidden>PRIVATE-HIDDEN</div><script>PRIVATE-SCRIPT</script></article></div></body>'
        urls = []
        text = reader.public_page('ask', ID, reader=lambda url: urls.append(url) or html)
        self.assertIn('原回答[7]', text)
        self.assertIn('[原始来源](https://pmnote.ai/articles/a/)', text)
        self.assertNotIn('PRIVATE-', text)
        self.assertNotIn('分享操作', text)
        self.assertIn('AI 整理', text)
        self.assertEqual(urls, ['https://pmnote.ai/ask/?question=' + ID])

    def test_each_fixed_section_and_pagination(self):
        for section, attr in [('hiring', 'data-hiring-list'), ('job-seekers', 'data-careers-list'), ('discussions', 'id="feed"')]:
            urls = []
            text = reader.public_page(section, page=1, reader=lambda url: urls.append(url) or '<body data-public-rendered="true"><div ' + attr + '><h2>公开条目</h2><p>当前正文</p></div></body>')
            self.assertIn('当前正文', text)
            query = '?type=opening&page=1' if section == 'hiring' else '?page=1'
            self.assertEqual(urls, [reader.BASE + reader.PUBLIC_SECTIONS[section][0] + query])

    def test_hiring_list_excludes_profiles_before_pagination(self):
        urls = []

        def fetch(url):
            urls.append(url)
            if url.endswith('?type=opening'):
                return '<body data-public-rendered="true"><article data-hiring-list><h2>较早且仍公开的招人信息</h2></article></body>'
            # The combined directory may contain only newer profiles on its first page.
            return '<body data-public-rendered="true"><article>较新的求职资料</article><span data-hiring-list></span></body>'

        text = reader.public_page('hiring', reader=fetch)
        self.assertEqual(urls, [reader.BASE + '/community/hiring/?type=opening'])
        self.assertIn('较早且仍公开的招人信息', text)

    def test_hiring_detail_preserves_old_direct_url(self):
        urls = []
        html = '<body data-public-rendered="true"><article data-hiring-list><h2>岗位职责原文</h2></article></body>'
        text = reader.public_page('hiring', ID, reader=lambda url: urls.append(url) or html)
        self.assertEqual(urls, [reader.BASE + '/community/hiring/?id=' + ID])
        self.assertIn('岗位职责原文', text)

    def test_discussion_direct_body_and_replies(self):
        text = reader.public_page('discussions', ID, reader=lambda url: '<body data-public-rendered="true"><div id="post-detail"><h1>帖子</h1><p>完整正文</p></div><div id="replies"><p>公开回复</p></div></body>')
        self.assertIn('?post=' + ID, text)
        self.assertIn('完整正文', text)
        self.assertIn('公开回复', text)

    def test_empty_current_response_is_distinct_from_old_loading_shell(self):
        self.assertIn('当前没有公开条目', reader.public_page('hiring', reader=lambda url: '<body data-public-rendered="true"><div data-hiring-list></div></body>'))
        for html in ['<body><div data-hiring-list>正在加载</div></body>', '<body data-public-rendered="true"><div>导航</div></body>']:
            with self.assertRaises(ValueError):
                reader.public_page('hiring', reader=lambda url: html)

    def test_invalid_identity_or_section_never_fetches(self):
        def unexpected(url):
            self.fail('must not fetch invalid public identity')
        for section, entry, page in [('admin', None, 0), ('ask', '../../private', 0), ('ask', None, -1), ('ask', None, 1001)]:
            with self.assertRaises(ValueError):
                reader.public_page(section, entry, page, reader=unexpected)

    def test_http_failure_does_not_restore_an_old_body(self):
        def failed(url):
            raise ValueError('Public source HTTP 404')
        with self.assertRaisesRegex(ValueError, 'HTTP 404'):
            reader.public_page('ask', ID, reader=failed)

    def test_release_verification_rejects_old_or_missing_renderer_source(self):
        html = '<head><meta name="pmnote-public-source" content="' + 'a' * 40 + '"></head><body data-public-rendered="true"><div data-hiring-list>公开岗位</div></body>'
        self.assertIn('公开岗位', reader.public_page('hiring', reader=lambda url: html, expected_sha='a' * 7))
        with self.assertRaises(ValueError):
            reader.public_page('hiring', reader=lambda url: html, expected_sha='b' * 40)
        with self.assertRaises(ValueError):
            reader.public_page('hiring', reader=lambda url: html.replace('pmnote-public-source', 'other'), expected_sha='a' * 40)


if __name__ == '__main__':
    unittest.main()
