"""Run with scripts/.venv/bin/python3 -B -m unittest discover -s evals."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
LANGUAGES = {
    'python': ('.py', 'class AuthRetry: pass\n', 'from Anchor import AuthRetry\nclass Helper(AuthRetry): pass\n'),
    'ts': ('.ts', 'export class AuthRetry {}\n', 'import {AuthRetry} from "../Anchor";\nexport class Helper extends AuthRetry {}\n'),
    'java': ('.java', 'class AuthRetry {}\n', 'class Helper extends AuthRetry {}\n'),
    'kotlin': ('.kt', 'open class AuthRetry\n', 'class Helper : AuthRetry()\n'),
}


class SearchScripts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='context-builder-test-')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.env = {**os.environ, 'XDG_CACHE_HOME': str(self.base / 'cache'),
                    'PYTHONDONTWRITEBYTECODE': '1'}

    def fixture(self, lang):
        ext, anchor, helper = LANGUAGES[lang]
        root = self.base / lang
        (root / 'src').mkdir(parents=True)
        (root / 'Anchor').with_suffix(ext).write_text(anchor)
        (root / 'src' / 'Helper').with_suffix(ext).write_text(helper)
        return root

    def module(self, lang):
        spec = importlib.util.spec_from_file_location(lang, SCRIPTS / f'search-{lang}-sources.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def run_cli(self, lang, root, *args, json_output=True, expected=0):
        command = [sys.executable, '-B', str(SCRIPTS / f'search-{lang}-sources.py'),
                   '--root', str(root), '--no-git', *args]
        if json_output:
            command.append('--json')
        result = subprocess.run(command, capture_output=True, text=True, env=self.env)
        self.assertEqual(result.returncode, expected, result.stderr)
        return json.loads(result.stdout) if json_output and expected == 0 else result

    def test_root_coverage_and_all_filter(self):
        for lang, (ext, _, _) in LANGUAGES.items():
            with self.subTest(lang=lang):
                root = self.fixture(lang)
                result = self.run_cli(lang, root, 'AuthRetry', '--fuzzy', '0')
                self.assertEqual(result['sources_searched'], 2)
                self.assertEqual(result['results'][0]['file'], 'Anchor' + ext)
                self.assertIn('AuthRetry', result['results'][0]['evidence'])
                self.assertEqual({r['file'] for r in result['results']}, {'Anchor' + ext, 'src/Helper' + ext})
                # Helper also references AuthRetry, so use its own independent term
                # to require the declaration AND a literal marker in the anchor.
                anchor = root / ('Anchor' + ext)
                comment = '# target_marker\n' if lang == 'python' else '// target_marker\n'
                anchor.write_text(anchor.read_text() + comment)
                result = self.run_cli(lang, root, 'AuthRetry', 'target_marker', '--all', '--fuzzy', '0')
                self.assertEqual([r['file'] for r in result['results']], ['Anchor' + ext])

    def test_cache_reuse_rename_and_edit(self):
        for lang, (ext, _, _) in LANGUAGES.items():
            with self.subTest(lang=lang), mock.patch.dict(os.environ, self.env):
                root = self.fixture(lang)
                m = self.module(lang)
                roots, _ = m.find_source_roots(str(root))
                files = m.list_sources(roots)
                initial, _ = m.build_index(roots, files)
                with mock.patch.object(m, 'captures', side_effect=AssertionError('warm cache reparsed')):
                    cached, _ = m.build_index(roots, files)
                self.assertEqual(initial, cached)
                anchor = root / ('Anchor' + ext)
                renamed = root / ('Renamed' + ext)
                anchor.rename(renamed)
                files = m.list_sources(roots)
                updated, _ = m.build_index(roots, files)
                self.assertNotIn(str(anchor), updated['decls'])
                self.assertIn(str(renamed), updated['decls'])
                # A newer peer must not mask this file's edit.
                helper = root / 'src' / ('Helper' + ext)
                future = 4_000_000_000_000_000_000
                os.utime(helper, ns=(future, future))
                m.build_index(roots, files)
                renamed.write_text(renamed.read_text().replace('AuthRetry', 'Replacement'))
                updated, _ = m.build_index(roots, files)
                self.assertEqual(updated['decls'][str(renamed)][0][0], 'Replacement')

    def test_empty_output_and_argument_validation(self):
        for lang, (ext, _, _) in LANGUAGES.items():
            with self.subTest(lang=lang):
                root = self.fixture(lang)
                self.assertEqual(self.run_cli(lang, root, 'AuthRetry', '-n', '0')['results'], [])
                result = self.run_cli(lang, root, 'AuthRetry', '-n', '0', json_output=False)
                self.assertIn('0 files', result.stdout)
                for flags in [('-n', '-1'), ('--seeds', '0'), ('--fuzzy', '2'), ('--fuzzy', 'nan')]:
                    self.run_cli(lang, root, 'AuthRetry', *flags, expected=2)
                testroot = root / 'tests'
                testroot.mkdir()
                filename = 'retry.test.ts' if lang == 'ts' else 'TestRetry' + ext
                text = 'def test_retry(): pass\n' if lang == 'python' else 'class TestRetry {}\n'
                (testroot / filename).write_text(text)
                result = self.run_cli(lang, testroot, 'retry', '--no-tests', '--fuzzy', '0', json_output=False)
                self.assertIn('0 files', result.stdout)

    def test_disabled_work_and_defaults(self):
        for lang in LANGUAGES:
            with self.subTest(lang=lang):
                root = self.fixture(lang)
                m = self.module(lang)
                roots, _ = m.find_source_roots(str(root))
                files = m.list_sources(roots)
                index, _ = m.build_index(roots, files, use_cache=False)
                with mock.patch.object(m, 'similarity', side_effect=AssertionError('fuzzy ran')), \
                     mock.patch.object(m, 'first_hit', side_effect=AssertionError('evidence ran')):
                    m.score_keyword('AuthRetry', files, roots, str(root), index, {}, {}, 0, evidence=False)
                result = self.run_cli(lang, root, 'AuthRetry', '--no-evidence')
                self.assertTrue(all(r['evidence'] is None for r in result['results']))
                self.assertTrue(all(r['hops'] <= 1 for r in result['results']))
                self.assertLessEqual(len(result['results']), 20)
                # --depth 0 must skip git expansion even without --no-git.
                with mock.patch.object(sys, 'argv', ['search', 'AuthRetry', '--root', str(root), '--depth', '0', '--json']), \
                     mock.patch.object(m, 'git_cochange', side_effect=AssertionError('git ran')), \
                     mock.patch('builtins.print'), mock.patch.dict(os.environ, self.env):
                    m.main()


if __name__ == '__main__':
    unittest.main()
