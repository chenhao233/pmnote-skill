"""Refresh, validate and package the public PMNote index (Python standard library)."""
import argparse
import datetime
import json
import importlib.util
from pathlib import Path
import re
import subprocess
import urllib.request
from urllib.parse import urlsplit
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REFS = ROOT / 'pmnote' / 'references'
spec = importlib.util.spec_from_file_location('public_read', ROOT / 'pmnote/scripts/read.py')
public = importlib.util.module_from_spec(spec)
spec.loader.exec_module(public)
SOURCE = 'https://pmnote.ai/agent-page-index.json'
TITLES = dict(articles='文章与视频配套文字', podcasts='播客公开页面',
              glossary='术语', jobs='公开岗位', services='课程与咨询介绍',
              guides='指南与栏目入口', channels='频道公开目录',
              tools='游戏研发 AI 工具', interviews='面经与公开分享')
HOSTS = {'pmnote.ai', 'www.bilibili.com', 'www.xiaoyuzhoufm.com', 'zhuanlan.zhihu.com'}
CHANNEL_PLATFORMS = {'www.xiaoyuzhoufm.com': '小宇宙',
                     'zhuanlan.zhihu.com': '知乎', 'www.bilibili.com': 'B站'}
LINK = re.compile(r'\]\(([^\s)]+)\)')


def fetch():
    return public.get_json(SOURCE)


def snapshot(source_index=None, expected_sha=None):
    before = public.get_json(public.BASE + '/build-info.json')['sha']
    if not re.fullmatch(r'[0-9a-f]{7,40}', before) or (expected_sha and before != expected_sha):
        raise ValueError('Production SHA differs from the release being synchronized')
    data = json.loads(source_index.read_text()) if source_index else fetch()
    data['interviews'] = public.Interviews().listing()
    after = public.get_json(public.BASE + '/build-info.json')['sha']
    if before != after:
        raise ValueError('Production changed during Skill snapshot; old files preserved')
    return data, before


def valid_url(url):
    p = urlsplit(url)
    interview = p.netloc == 'pmnote.ai' and p.path == '/community/experiences/' and re.fullmatch(r'entry=[0-9a-f-]{36}', p.fragment)
    if interview:
        public.canonical(p.fragment.removeprefix('entry='))
    if (p.scheme != 'https' or p.netloc not in HOSTS or p.query or (p.fragment and not interview)
            or any(c.isspace() for c in url) or any(c in url for c in '<>()')):
        raise ValueError('Unexpected source URL')
    return p


def render(data, day):
    if data.get('schemaVersion') != 3 or data.get('siteBase') != 'https://pmnote.ai':
        raise ValueError('Unexpected source schema')
    groups = {key: [] for key in TITLES}
    channels = {host: [] for host in CHANNEL_PLATFORMS}
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
            if source == 'catalog' and p.netloc not in CHANNEL_PLATFORMS:
                raise ValueError('Unexpected channel platform')
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
            elif path == '/tools' or (path.startswith('/tools/') and path != '/tools/career-check'): key = 'tools'
            title = title.replace('\\', '\\\\').replace('[', '\\[').replace(']', '\\]').replace('<', '&lt;').replace('>', '&gt;')
            entry = f'- [{title}]({url})'
            groups[key].append(entry)
            if key == 'channels': channels[p.netloc].append(entry)
    interviews = data.get('interviews')
    if not isinstance(interviews, list) or not interviews:
        raise ValueError('Missing public interviews; refusing a static-page-only index')
    for item in interviews:
        public.validate_interview(item)
        url = public.canonical(item['id'])
        if url in seen:
            raise ValueError('Duplicate interview URL')
        seen.add(url)
        groups['interviews'].append('- [' + public.label(item.get('title') or item['originalTitle']) + '](' + url + ') · 分享人 @' + public.label(item['sharer']))
    if any(not rows for rows in groups.values()):
        raise ValueError('Empty category; inspect the source before replacing the index')
    result = {key + '.md': '# ' + TITLES[key] + '\n\n' + '\n'.join(rows) + '\n'
              for key, rows in groups.items()}
    result['channels.md'] = '# ' + TITLES['channels'] + '\n\n' + '\n\n'.join(
        '## ' + CHANNEL_PLATFORMS[host] + '\n\n' + '\n'.join(rows)
        for host, rows in channels.items() if rows) + '\n'
    result['interviews.md'] = result['interviews.md'].replace('\n\n', '\n\n目录来自当前匿名公开接口，可能包括面试经历、题单与准备资料；按实际内容引用。链接可在浏览器原位阅读。HTTP只读到加载页时，用随包脚本 `python3 <Skill目录>/scripts/read.py interviews --id <链接中entry的值>` 读取当前公开正文。正文保留分享人署名，不将第三方经历归给Hao；撤下或不可读取时不引用旧缓存。\n\n', 1)
    result['tools.md'] = result['tools.md'].replace('\n\n', '\n\n先按职能与场景找工具，再读详情中的边界、费用和官方来源。可用随包脚本 `python3 <Skill目录>/scripts/read.py tool <工具slug>` 获取官网当前公开正文；价格与能力仍需核对官方来源及日期。\n\n', 1)
    index = ['# PMNote 公开内容索引', '', '更新日期：' + day, '',
             f'数据来源：[PMNote 公开索引]({SOURCE})', '']
    index += [f'- [{TITLES[k]}]({k}.md)：{len(v)} ' + ('条频道内容链接' if k == 'channels' else '个页面')
              for k, v in groups.items()]
    index += ['', '新内容可查阅 [PMNote 当前全站目录](https://pmnote.ai/llms.txt)。', '']
    result['index.md'] = '\n'.join(index)
    return result


def check():
    license_body = (ROOT / 'LICENSE').read_bytes()
    if not license_body.decode('utf-8').startswith('PMNote Skill 个人学习许可\n'):
        raise ValueError('Unexpected license')
    if (ROOT / 'pmnote/LICENSE').read_bytes() != license_body:
        raise ValueError('Bundled license differs from repository license')
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
    parser.add_argument('command', choices=['update', 'check', 'package', 'impact', 'verify'])
    parser.add_argument('--remote', action='store_true')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--source-index', type=Path)
    parser.add_argument('--expected-sha')
    args = parser.parse_args()
    if args.source_index and args.command != 'impact':
        parser.error('--source-index is only for candidate impact checks; published indices must come from production')
    if args.command in ('update', 'impact', 'verify') or args.remote:
        day = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).date().isoformat()
        if (REFS / 'index.md').exists():
            day = re.search(r'更新日期：(\d{4}-\d{2}-\d{2})', (REFS / 'index.md').read_text())[1]
        data, site_sha = snapshot(args.source_index, args.expected_sha)
        result = render(data, day)
        # An incomplete remote response must not erase an existing category.
        for name, body in result.items():
            old = (REFS / name).read_text() if (REFS / name).exists() else ''
            if name != 'index.md' and body.count('\n- ') < old.count('\n- ') * 0.8:
                raise ValueError(f'Unexpected shrink in {name}; old files left untouched')
        stale = [name for name, body in result.items() if not (REFS / name).exists() or (REFS / name).read_text() != body]
        if args.command == 'impact':
            print(json.dumps({'decision': 'skill_update_required' if stale else 'skill_no_change', 'files': stale, 'productionSha': site_sha, 'candidateIndexVersion': data.get('version')}, ensure_ascii=False))
            return
        if args.command == 'check' or args.command == 'verify':
            if stale: raise ValueError('Refresh needed: ' + ', '.join(stale))
        elif stale:
            day = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).date().isoformat()
            result = render(data, day)
            for name, body in result.items(): (REFS / name).write_text(body)
            provenance = {'schemaVersion': 1, 'siteSha': site_sha, 'pageIndexVersion': data.get('version'), 'interviews': len(data['interviews']), 'date': day}
            (REFS / 'source.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n')
        if args.command == 'verify':
            sample = next((x for x in data['interviews'] if x.get('company') == '腾讯'), data['interviews'][0])
            detail = public.Interviews().detail(sample['id'])
            if public.interview_markdown(sample) != public.interview_markdown(detail):
                raise ValueError('Interview changed between discovery and body read')
            tool = public.tool_text('tripo')
            evidence = {'siteSha': site_sha, 'pageIndexVersion': data.get('version'), 'interviewsIndexed': len(data['interviews']), 'interview': {'title': detail.get('title'), 'url': public.canonical(detail['id']), 'attribution': '分享人 @' + detail['sharer'], 'bodyChars': len(public.interview_markdown(detail))}, 'tool': {'url': public.BASE + '/tools/tripo/', 'bodyChars': len(tool)}}
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n')
            print(json.dumps(evidence, ensure_ascii=False))
    check()
    if args.command == 'package':
        if args.output is None: parser.error('package requires --output')
        paths = [ROOT / 'pmnote/SKILL.md', ROOT / 'pmnote/agents/openai.yaml', ROOT / 'pmnote/LICENSE', ROOT / 'pmnote/scripts/read.py',
                 *[REFS / (key + '.md') for key in TITLES], REFS / 'index.md', REFS / 'source.json']
        with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in paths: archive.write(path, path.relative_to(ROOT))
        print('Package written:', args.output)


if __name__ == '__main__':
    main()
