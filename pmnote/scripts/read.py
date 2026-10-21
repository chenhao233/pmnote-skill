"""Read PMNote public interviews and AI tool text; Python 3.9+, no login."""
import argparse
from html.parser import HTMLParser
import json
import re
import urllib.error
import urllib.request

BASE = 'https://pmnote.ai'
UUID = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$')


def request(url, payload=None, headers=None):
    data = None if payload is None else json.dumps(payload).encode()
    options = {'User-Agent': 'PMNote-Skill/1.2', **(headers or {})}
    if data is not None:
        options['Content-Type'] = 'application/json'
    # One retry for transient transport errors, never for an HTTP denial.
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, data=data, headers=options)
            with urllib.request.urlopen(req, timeout=25) as response:
                raw = response.read(10_000_001)
            if len(raw) > 10_000_000:
                raise ValueError('Public response exceeds 10 MB; nothing truncated')
            return raw.decode('utf-8')
        except urllib.error.HTTPError as error:
            raise ValueError('Public source HTTP ' + str(error.code)) from None
        except (urllib.error.URLError, TimeoutError):
            if attempt:
                raise ValueError('Public source unavailable; no current result verified') from None


def get_json(url):
    return json.loads(request(url))


def label(value):
    return str(value or '').replace('\\', '\\\\').replace('[', '\\[').replace(']', '\\]').replace('\n', ' ').replace('\r', ' ').replace('<', '&lt;').replace('>', '&gt;')


def canonical(entry_id):
    if not UUID.fullmatch(entry_id):
        raise ValueError('Invalid public interview id')
    return BASE + '/community/experiences/#entry=' + entry_id


class PublicConfig(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag == 'body':
            self.values = dict(attrs)


class Interviews:
    def __init__(self):
        parser = PublicConfig()
        parser.feed(request(BASE + '/community/experiences/'))
        attrs = getattr(parser, 'values', {})
        url, key = attrs.get('data-community-url', ''), attrs.get('data-community-key', '')
        if not re.fullmatch(r'https://[a-z0-9-]+\.supabase\.co', url) or not key:
            raise ValueError('Public interview connection missing; use the website browser')
        # Only the publishable value already shipped to anonymous website visitors.
        # It stays in memory; no account token, cookie or private configuration is read.
        self.url = url + '/functions/v1/community'
        self.headers = {'Origin': BASE, 'apikey': key}

    def call(self, action, payload):
        if action not in ('interviews_list', 'interviews_detail'):
            raise ValueError('Only anonymous public reads are supported')
        return json.loads(request(self.url, {'action': action, 'payload': payload}, self.headers))

    def listing(self, query=''):
        if len(query) > 200:
            raise ValueError('Use short generic topic keywords')
        items, seen, total = [], set(), None
        for page in range(500):
            result = self.call('interviews_list', {'page': page, 'q': query})
            if not isinstance(result.get('items'), list) or not isinstance(result.get('hasMore'), bool):
                raise ValueError('Incomplete public interview list')
            if len(result['items']) > 20 or (result['hasMore'] and not result['items']):
                raise ValueError('Invalid public interview page; no pagination progress')
            if total is None:
                total = result.get('total')
            if result.get('total') != total:
                raise ValueError('Interview list changed while paging; retry a new snapshot')
            for item in result['items']:
                validate_interview(item)
                if item['id'] in seen:
                    raise ValueError('Duplicate interview while paging')
                seen.add(item['id'])
                items.append(item)
            if not result['hasMore']:
                # Older live deployments expose hasMore without a total.
                # When supplied, total is an additional completeness check.
                if total is not None and (not isinstance(total, int) or total != len(items)):
                    raise ValueError('Incomplete interview coverage')
                return items
        raise ValueError('Interview pagination limit reached; incomplete result rejected')

    def detail(self, entry_id):
        canonical(entry_id)
        item = self.call('interviews_detail', {'id': entry_id})
        validate_interview(item)
        if item['id'] != entry_id:
            raise ValueError('Interview detail identity mismatch')
        return item


def validate_interview(item):
    canonical(item.get('id', ''))
    if item.get('status') != 'published' or not item.get('sharer') or not (item.get('title') or item.get('originalTitle')):
        raise ValueError('Not a published attributed interview')


def interview_markdown(item):
    validate_interview(item)
    lines = ['# ' + label(item.get('title') or item['originalTitle']), '',
             '原文：' + canonical(item['id']), '分享人 @' + label(item['sharer']), '',
             '内容范围：PMNote 当前公开分享文字；面试题与作者复盘按原文区分，不代表 Hao 本人的经历或建议。', '']
    for key, title in [('company', '公司'), ('role', '原岗位'), ('roundLabel', '轮次'), ('recruitmentType', '招聘类型'), ('interviewDate', '面试时间'), ('outcome', '结果')]:
        if item.get(key):
            lines.append(title + '：' + label(item[key]))
    if item.get('summary'):
        lines += ['', item['summary'], '']
    sections = item.get('sections') or []
    if sections:
        for section in sections:
            lines += ['## ' + label(section['heading']), '']
            lines += ['- ' + text for text in section['items']]
            lines += ['']
    elif isinstance(item.get('body'), str) and item['body'].strip():
        lines += [item['body'], '']
    else:
        raise ValueError('Public interview body missing; title is not evidence')
    return '\n'.join(lines)


def tool_text(slug):
    if not re.fullmatch(r'[a-z0-9-]+', slug):
        raise ValueError('Invalid tool slug')
    index = get_json(BASE + '/agent/knowledge/index.json')
    url = BASE + '/tools/' + slug + '/'
    entries = [row for row in index['entries'] if row['canonical'] == url]
    if len(entries) != 1:
        raise ValueError('No published tool text found; use the current tool directory')
    read_url = entries[0]['readUrl']
    if not re.fullmatch(re.escape(BASE) + r'/agent/knowledge/pages/[a-f0-9]+\.md', read_url):
        raise ValueError('Unexpected public tool read URL')
    body = request(read_url)
    if url not in body or len(body.split('---', 1)[-1].strip()) < 80:
        raise ValueError('Tool source body or canonical missing')
    return body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='kind', required=True)
    interviews = sub.add_parser('interviews')
    interviews.add_argument('--search', default='')
    interviews.add_argument('--id')
    tools = sub.add_parser('tool')
    tools.add_argument('slug')
    args = parser.parse_args()
    if args.kind == 'tool':
        print(tool_text(args.slug))
    elif args.id:
        print(interview_markdown(Interviews().detail(args.id)))
    else:
        for item in Interviews().listing(args.search):
            print('- [' + label(item.get('title') or item['originalTitle']) + '](' + canonical(item['id']) + ') · 分享人 @' + label(item['sharer']))
            print('  正文读取：python3 <Skill目录>/scripts/read.py interviews --id ' + item['id'])


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError) as error:
        raise SystemExit(str(error))
