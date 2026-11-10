import unittest
from run_benchmark import percentile,stream,summarize

class MeasurementContract(unittest.TestCase):
    def test_small_sample_tail_is_explicit_maximum(self):
        self.assertEqual(percentile(list(range(1,32)),.99),31)
        self.assertEqual(percentile(list(range(1,32)),.5),16)
    def test_invalid_clocks_are_not_zero_measurements(self):
        for bad in [[],[0],[True],[1.5],[-1]]:
            with self.subTest(bad=bad),self.assertRaises(ValueError):percentile(bad,.5)
    def test_dataset_count_sequence_and_reproducibility(self):
        rows=stream(1000,42);self.assertEqual(rows,stream(1000,42));self.assertEqual(len(rows),1000)
        self.assertEqual(rows[0],'S 1 100 5 200 5');self.assertTrue(rows[-1].startswith('U 1000 '))
    def test_null_memory_retains_unknown_and_units(self):
        row={'event_count':1000,'batch_ns':[1000,2000,3000],'peak_resident_bytes':None}
        result=summarize(row,1000,3);self.assertIsNone(result['peak_resident_bytes'])
        self.assertEqual(result['batch_p50_amortized_ns_per_event'],2)
    def test_invalid_memory_and_missing_samples_fail(self):
        for memory in [0,True,-1,1.5]:
            with self.subTest(memory=memory),self.assertRaises(ValueError):summarize({'event_count':1000,'batch_ns':[1,2,3],'peak_resident_bytes':memory},1000,3)
        with self.assertRaises(ValueError):summarize({'event_count':1000,'batch_ns':[1,2],'peak_resident_bytes':None},1000,3)

class SourcePackageCIContracts(unittest.TestCase):
    """Exact-source inventory checks, not a performance benchmark."""

    def setUp(self):
        import importlib.util
        import os
        from pathlib import Path
        import shutil
        import tempfile

        self.origin = Path(__file__).resolve().parents[1]
        scratch = self.origin / ".build"
        scratch.mkdir(exist_ok=True)
        self.base = Path(tempfile.mkdtemp(prefix="source-policy-contract-", dir=scratch))
        self.repo = self.base / "source"
        self.repo.mkdir()
        spec = importlib.util.spec_from_file_location("book_source_package_fixture", self.origin / "scripts/source_package.py")
        self.package = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.package)
        for name in self.package.ALLOWED:
            target = self.repo / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.origin / name, target)
        self.package.ROOT = self.repo
        self.environment = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
        self.git("init", "-q", "-b", "fixture")
        self.git("config", "user.name", "Synthetic source policy fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "core.autocrlf", "false")
        self.git("config", "core.symlinks", "false")
        self.git("add", ".")
        self.git("commit", "-qm", "Synthetic source fixture")
        self.commit = self.git("rev-parse", "HEAD").decode().strip()

    def git(self, *args, data=None):
        import subprocess
        return subprocess.check_output(["git", "-C", str(self.repo), *args], input=data,
                                       stderr=subprocess.PIPE, env=self.environment)

    def reject_before_output(self):
        output = self.base / "rejected-output"
        with self.assertRaises(ValueError):
            self.package.build(output, self.commit)
        self.assertFalse(output.exists())

    def test_ci_policy_members_are_exact_git_bytes_and_deterministic(self):
        import shutil
        import zipfile
        additions = {".github/ci/policy.py", ".github/ci/test_policy.py", "docs/CI-POLICY.md"}
        missing = [name for name in additions if not (self.repo / name).exists()]
        for name in missing:
            target = self.repo / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.origin / name, target)
        if missing:
            self.git("add", "--", *missing)
            self.git("commit", "-qm", "Synthetic exact policy additions")
            self.commit = self.git("rev-parse", "HEAD").decode().strip()
        first, second = self.base / "first", self.base / "second"
        a = self.package.build(first, self.commit)
        b = self.package.build(second, self.commit)
        self.assertEqual(a, b)
        self.assertEqual((first / a["archive"]).read_bytes(), (second / b["archive"]).read_bytes())
        with zipfile.ZipFile(first / a["archive"]) as zipped:
            self.assertTrue(additions.issubset(zipped.namelist()))
            for name in additions:
                self.assertEqual(zipped.read(name), self.git("show", self.commit + ":" + name))
        self.assertTrue(self.package.check(first, self.commit, self.repo)["gitByteComparison"])

    def test_missing_required_ci_policy_member_rejected(self):
        self.git("rm", "--", "docs/CI-POLICY.md")
        self.git("commit", "-qm", "Synthetic missing required policy document")
        self.commit = self.git("rev-parse", "HEAD").decode().strip()
        self.reject_before_output()

    def add_forbidden(self, name):
        target = self.repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"SYNTHETIC-NOT-A-SECRET\n")
        self.git("add", "--force", "--", name)
        self.git("commit", "-qm", "Synthetic forbidden source member")
        self.commit = self.git("rev-parse", "HEAD").decode().strip()
        self.reject_before_output()

    def test_unknown_ci_policy_neighbor_rejected(self):
        self.add_forbidden(".github/ci/not-reviewed.py")

    def test_generated_member_rejected(self):
        self.add_forbidden("bin/not-a-real-executable.dll")

    def test_untracked_private_member_rejected(self):
        (self.repo / ".env").write_bytes(b"SYNTHETIC-NOT-A-SECRET\n")
        self.reject_before_output()

    def test_dirty_tracked_member_rejected(self):
        with (self.repo / "README.md").open("ab") as output:
            output.write(b"\nSynthetic dirty source\n")
        self.reject_before_output()

    def test_git_symlink_mode_rejected_without_os_symlink_privilege(self):
        target = b"outside-synthetic-target"
        (self.repo / "README.md").write_bytes(target)
        blob = self.git("hash-object", "-w", "--stdin", data=target).decode().strip()
        self.git("update-index", "--cacheinfo", "120000," + blob + ",README.md")
        self.git("commit", "-qm", "Synthetic symlink index member")
        self.commit = self.git("rev-parse", "HEAD").decode().strip()
        self.assertEqual(self.git("status", "--porcelain"), b"")
        self.reject_before_output()

if __name__=='__main__':unittest.main()
