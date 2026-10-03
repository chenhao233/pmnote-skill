"""Refresh, validate and package the public PMNote index (Python standard library)."""
import argparse
import datetime
import json
from pathlib import Path
import re
import subprocess
import urllib.request
from urllib.parse import urlsplit
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REFS = ROOT / 'pmnote' / 'references'
SOURCE = 'https://pmnote.ai/agent-page-index.json'
TITLES = dict(articles='文章与视频配套文字', podcasts='播客公开页面',
              glossary='术语', jobs='公开岗位', services='课程与咨询介绍',
              guides='指南、工具与栏目入口', channels='频道公开目录')
HOSTS = {'pmnote.ai', 'www.bilibili.com', 'www.xiaoyuzhoufm.com', 'zhuanlan.zhihu.com'}
LINK = re.compile(r'\]\(([^\s)]+)\)')


def fetch():
    request = urllib.request.Request(SOURCE, headers={'User-Agent': 'PMNote-Skill/1.0'})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(10_000_001)
    if len(data) > 10_000_000:
        raise ValueError('Source exceeds 10 MB; inspect before updating')
    return json.loads(data)


def valid_url(url):
    p = urlsplit(url)
    if (p.scheme != 'https' or p.netloc not in HOSTS or p.query or p.fragment
            or any(c.isspace() for c in url) or any(c in url for c in '<>()')):
        raise ValueError('Unexpected source URL')
    return p


def render(data, day):
    if data.get('schemaVersion') != 3 or data.get('siteBase') != 'https://pmnote.ai':
        raise ValueError('Unexpected source schema')
    groups = {key: [] for key in TITLES}
    seen = set()
    for source in ('pages', 'catalog'):
        rows = data.get(source)
        if not isinstance(rows, list) or not rows:
            raise ValueError('Missing source: ' + source)
        for item in rows:
            url, title = item['url'], item['title']
            p = valid_url(url)
            if source == 'pages' and p.netloc != 'pmnote.ai':
                raise ValueError('Non-PMNote page')
            if not isinstance(title, str) or not title.strip() or '\n' in title or '\r' in title:
                raise ValueError('Invalid title')
            if url in seen:
                raise ValueError('Duplicate URL')
            seen.add(url)
            path = p.path.rstrip('/')
            key = 'guides'
            if source == 'catalog': key = 'channels'
            elif path.startswith('/articles/') and not path.startswith('/articles/topics/'): key = 'articles'
            elif path.startswith('/podcast/'): key = 'podcasts'
            elif path.startswith('/glossary/'): key = 'glossary'
            elif path.startswith('/job-market/jobs/'): key = 'jobs'
            elif path.startswith('/courses/') or path in ('/services', '/en/services'): key = 'services'
            title = title.replace('\\', '\\\\').replace('[', '\\[').replace(']', '\\]').replace('<', '&lt;').replace('>', '&gt;')
            groups[key].append(f'- [{title}]({url})')
    if any(not rows for rows in groups.values()):
        raise ValueError('Empty category; inspect the source before replacing the index')
    result = {key + '.md': '# ' + TITLES[key] + '\n\n' + '\n'.join(rows) + '\n'
              for key, rows in groups.items()}
    index = ['# PMNote 公开内容索引', '', '更新日期：' + day, '',
             f'数据来源：[PMNote 公开索引]({SOURCE})', '']
    index += [f'- [{TITLES[k]}]({k}.md)：{len(v)} ' + ('条频道内容链接' if k == 'channels' else '个页面')
              for k, v in groups.items()]
    index += ['', '新内容可查阅 [PMNote 当前全站目录](https://pmnote.ai/llms.txt)。', '']
    result['index.md'] = '\n'.join(index)
    return result


def check():
    assert (ROOT / 'LICENSE').read_text().startswith('MIT License\n')
    assert (ROOT / 'pmnote/SKILL.md').read_text().startswith('---\nname: pmnote\n')
    for p in [*ROOT.glob('*.md'), *ROOT.glob('pmnote/**/*.md')]:
        for link in LINK.findall(p.read_text()):
            if link.startswith('https://'): continue
            if not (p.parent / link.split('#')[0]).resolve().is_file():
                raise ValueError(f'Broken relative link in {p.name}: {link}')
    urls = []
    for key in TITLES:
        urls += LINK.findall((REFS / (key + '.md')).read_text())
    for url in urls: valid_url(url)
    if len(set(urls)) != len(urls): raise ValueError('Duplicate index URL')
    # Check both author and committer; print no private data on failure.
    log = subprocess.check_output(['git', 'log', '--all', '--format=%ae%n%ce'], cwd=ROOT, text=True)
    if any(not line.endswith('@users.noreply.github.com') for line in log.splitlines() if line):
        raise ValueError('Commit history contains a non-noreply email')
    print(f'OK: {len(urls)} unique public links; references, license and commit identities valid')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['update', 'check', 'package'])
    parser.add_argument('--remote', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.command == 'update' or args.remote:
        day = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).date().isoformat()
        if args.command == 'check':
            day = re.search(r'更新日期：(\d{4}-\d{2}-\d{2})', (REFS / 'index.md').read_text())[1]
        result = render(fetch(), day)
        # An incomplete remote response must not erase an existing category.
        for name, body in result.items():
            old = (REFS / name).read_text() if (REFS / name).exists() else ''
            if name != 'index.md' and body.count('\n- ') < old.count('\n- ') * 0.8:
                raise ValueError(f'Unexpected shrink in {name}; old files left untouched')
        if args.command == 'check':
            stale = [name for name, body in result.items() if (REFS / name).read_text() != body]
            if stale: raise ValueError('Refresh needed: ' + ', '.join(stale))
        else:
            for name, body in result.items(): (REFS / name).write_text(body)
    check()
    if args.command == 'package':
        if args.output is None: parser.error('package requires --output')
        paths = [ROOT / 'pmnote/SKILL.md', ROOT / 'pmnote/agents/openai.yaml',
                 *[REFS / (key + '.md') for key in TITLES], REFS / 'index.md']
        with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in paths: archive.write(path, path.relative_to(ROOT))
            archive.write(ROOT / 'LICENSE', 'pmnote/LICENSE')
        print('Package written:', args.output)


if __name__ == '__main__':
    main()
