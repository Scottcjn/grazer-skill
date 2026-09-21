import json
import os
import re
import unittest

class TestPackagingVersions(unittest.TestCase):
    def test_version_consistency_across_manifests(self):
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 1. package.json
        with open(os.path.join(repo_root, "package.json"), "r", encoding="utf-8") as f:
            pkg_version = json.load(f)["version"]
            
        # 2. setup.py
        with open(os.path.join(repo_root, "setup.py"), "r", encoding="utf-8") as f:
            setup_content = f.read()
            m = re.search(r'version\s*=\s*["\']([^"\']+)["\']', setup_content)
            self.assertIsNotNone(m, "setup.py version not found")
            setup_version = m.group(1)
            self.assertEqual(setup_version, pkg_version)
            
        # 3. debian/control
        with open(os.path.join(repo_root, "debian", "control"), "r", encoding="utf-8") as f:
            deb_content = f.read()
            m_deb = re.search(r'Version:\s*([^\s]+)', deb_content)
            self.assertIsNotNone(m_deb, "debian/control version not found")
            self.assertEqual(m_deb.group(1), pkg_version)
            
        # 4. homebrew/grazer.rb
        with open(os.path.join(repo_root, "homebrew", "grazer.rb"), "r", encoding="utf-8") as f:
            brew_content = f.read()
            self.assertIn(f"grazer-skill-{pkg_version}.tgz", brew_content)
            self.assertIn(f'assert_match "{pkg_version}"', brew_content)

if __name__ == "__main__":
    unittest.main()
