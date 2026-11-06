"""Build/check only the exact Git source release; no binaries or measurements."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.2.1-preview.1"
MANIFEST = "SOURCE-MANIFEST.json"
KEY = "SIGNING-PUBLIC-KEY.pub"
ALLOWED = frozenset({
    ".gitattributes", ".gitignore", ".github/workflows/verify.yml",
    "BENCHMARKS.md", "CHANGELOG.md", "CONTRIBUTING.md", "FLAT_DEPTH.md",
    "LICENSE", "README.md", "REPLAY_CONTRACT.md", KEY,
    "benchmark.cpp", "benchmark.py", "book.hpp", "book_replay.cpp", "book_replay.py",
    "demo_recovery.py", "fixtures.json", "flat_depth.hpp", "flat_depth_benchmark.cpp",
    "run_benchmark.py", "run_flat_benchmark.py", "validation.json", "verify.py",
    "verify_flat.cpp", "verify_flat.py", "scripts/source_package.py",
    "tests/test_benchmark.py", "tests/test_flat_benchmark.py", "results/README.md",
    "results/windows-flat-depth-20261102.json.gz", "results/windows-flat-depth-20261102.meta.json",
    "results/windows-gcc13-python312.json",
})

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE)

def snapshot(root, commit):
    if not re.fullmatch("[0-9a-f]{40}", commit) or git(root, "rev-parse", "HEAD").decode().strip() != commit:
        raise ValueError("Exact full HEAD commit required")
    if git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all"):
        raise ValueError("Use a clean checkout; preserve dirty/untracked source")
    files = {}
    for row in git(root, "ls-tree", "-rz", commit).split(b"\0"):
        if not row:
            continue
        header, raw_name = row.split(b"\t", 1)
        mode, kind, _ = header.split()
        name = raw_name.decode("utf-8")
        if name not in ALLOWED or mode != b"100644" or kind != b"blob":
            raise ValueError("Unexpected source or symlink: " + name)
        files[name] = git(root, "show", commit + ":" + name)
    if set(files) != ALLOWED:
        raise ValueError("Source member allowlist differs")
    return files, git(root, "rev-parse", commit + "^{tree}").decode().strip()

def description(files, commit, tree):
    return {"schema": "book-replay-source-v1", "version": VERSION,
            "sourceCommit": commit, "sourceTree": tree,
            "files": [{"path": name, "bytes": len(raw), "sha256": sha(raw)}
                      for name, raw in sorted(files.items())]}

def build(directory, commit):
    files, tree = snapshot(ROOT, commit)
    metadata = (json.dumps(description(files, commit, tree), indent=2) + "\n").encode()
    directory.mkdir(parents=True, exist_ok=False)
    name = "book-replay-lab-v" + VERSION + ".zip"
    with zipfile.ZipFile(directory / name, "x", compression=zipfile.ZIP_STORED) as zipped:
        for path, raw in sorted({**files, MANIFEST: metadata}.items()):
            info = zipfile.ZipInfo(path, date_time=(2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_STORED
            zipped.writestr(info, raw)
    products = {name: (directory / name).read_bytes(), MANIFEST: metadata, KEY: files[KEY]}
    for path in [MANIFEST, KEY]:
        (directory / path).write_bytes(products[path])
    snapshot(ROOT, commit)  # Refuse publication receipt if the source changed.
    (directory / "SHA256SUMS.txt").write_bytes("".join(sha(raw) + "  " + path + "\n" for path, raw in sorted(products.items())).encode("ascii"))
    return {"commit": commit, "tree": tree, "sourceFiles": len(files),
            "archive": name, "archiveBytes": len(products[name]), "archiveSha256": sha(products[name])}

def check(directory, commit, repository=None):
    expected = {"book-replay-lab-v" + VERSION + ".zip", MANIFEST, KEY}
    sums = {}
    for line in (directory / "SHA256SUMS.txt").read_bytes().decode("ascii").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([A-Za-z0-9._-]+)", line)
        if not match or match[2] in sums:
            raise ValueError("Invalid checksum entry")
        sums[match[2]] = match[1]
    if set(sums) != expected:
        raise ValueError("Wrong release product list")
    for name, digest in sums.items():
        path = directory / name
        if path.is_symlink() or path.stat().st_size > 4 * 1024 * 1024 or sha(path.read_bytes()) != digest:
            raise ValueError("Unsafe product or checksum mismatch")
    raw_manifest = (directory / MANIFEST).read_bytes()
    metadata = json.loads(raw_manifest)
    if set(metadata) != {"schema", "version", "sourceCommit", "sourceTree", "files"} or metadata["schema"] != "book-replay-source-v1" or metadata["version"] != VERSION:
        raise ValueError("Invalid source manifest")
    if metadata["sourceCommit"] != commit or not re.fullmatch("[0-9a-f]{40}", commit) or not re.fullmatch("[0-9a-f]{40}", metadata["sourceTree"]):
        raise ValueError("Wrong source identity")
    archive = directory / ("book-replay-lab-v" + VERSION + ".zip")
    with zipfile.ZipFile(archive) as zipped:
        members = zipped.infolist()
        if len(members) != len(ALLOWED) + 1 or {x.filename for x in members} != ALLOWED | {MANIFEST}:
            raise ValueError("Duplicate, unsafe or unexpected ZIP member")
        for item in members:
            if item.file_size > 4 * 1024 * 1024 or item.compress_type != zipfile.ZIP_STORED or item.create_system != 3 or item.external_attr != 0o100644 << 16 or item.date_time != (2026, 1, 1, 0, 0, 0):
                raise ValueError("Noncanonical ZIP member")
        if zipped.read(MANIFEST) != raw_manifest:
            raise ValueError("Inner and outer manifest differ")
        files = {name: zipped.read(name) for name in ALLOWED}
    if metadata != description(files, commit, metadata["sourceTree"]) or files[KEY] != (directory / KEY).read_bytes():
        raise ValueError("Source member inventory/key mismatch")
    if raw_manifest != (json.dumps(metadata, indent=2) + "\n").encode():
        raise ValueError("Noncanonical manifest bytes")
    if repository is not None:
        source, tree = snapshot(repository, commit)
        if source != files or metadata != description(source, commit, tree):
            raise ValueError("Actual source ZIP differs from exact Git")
    return {"passed": True, "commit": commit, "tree": metadata["sourceTree"], "sourceFiles": len(files),
            "gitByteComparison": repository is not None, "archiveSha256": sha(archive.read_bytes()),
            "manifestSha256": sha(raw_manifest)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["build", "check"])
    parser.add_argument("--commit", required=True)
    parser.add_argument("--directory", type=Path, default=ROOT / ".build" / ("release-v" + VERSION))
    parser.add_argument("--repository", type=Path, help="Optional clean Git checkout for exact member-byte comparison")
    args = parser.parse_args()
    result = build(args.directory.resolve(), args.commit) if args.action == "build" else check(args.directory.resolve(), args.commit, args.repository)
    print(json.dumps(result, sort_keys=True))
