import re
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r'\]\((https://pmnote\.ai/courses/[^)]+)\)')

class CourseGuidePackage(unittest.TestCase):
    def test_course_links_correspond_to_public_services_index(self):
        guide = (ROOT / 'pmnote/references/course-guide.md').read_text()
        services = (ROOT / 'pmnote/references/services.md').read_text()
        guide_urls = {url.rstrip('/') for url in LINK.findall(guide)}
        service_urls = {url.rstrip('/') for url in LINK.findall(services)}
        self.assertEqual(len(guide_urls), 5)
        self.assertTrue(guide_urls <= service_urls)
        self.assertNotIn('chenhao159328404', guide)
        self.assertNotRegex(guide, r'[¥￥]\s*\d')

    def test_package_contains_course_guide_and_resolvable_references(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / 'candidate.zip'
            subprocess.run(['python3', str(ROOT / 'scripts/index.py'), 'package', '--output', str(package)], cwd=ROOT, check=True, capture_output=True, text=True)
            with zipfile.ZipFile(package) as archive:
                names = set(archive.namelist())
                guide_path = 'pmnote/references/course-guide.md'
                self.assertIn(guide_path, names)
                self.assertIn('pmnote/references/services.md', names)
                skill = archive.read('pmnote/SKILL.md').decode()
                self.assertIn('references/course-guide.md', skill)
                self.assertIn('references/services.md', skill)
                self.assertEqual(archive.read(guide_path).decode(), (ROOT / guide_path).read_text())

if __name__ == '__main__':
    unittest.main()
