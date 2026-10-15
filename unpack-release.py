"""Verify the complete distribution before publishing it to GitHub Pages."""
import hashlib
import io
import json
import pathlib
import zipfile

root = pathlib.Path(__file__).resolve().parent
manifest = json.loads((root / "_release" / "manifest.json").read_text())
digest = lambda data: hashlib.sha256(data).hexdigest()
parts = []
for item in manifest["parts"]:
    data = (root / "_release" / item["name"]).read_bytes()
    assert len(data) == item["bytes"], "Part size mismatch"
    assert digest(data) == item["sha256"], "Part checksum mismatch"
    parts.append(data)
archive = b"".join(parts)
assert digest(archive) == manifest["sha256"], "Release checksum mismatch"
expected = {entry["path"]: entry["sha256"] for entry in manifest["files"]}
with zipfile.ZipFile(io.BytesIO(archive)) as package:
    assert package.testzip() is None, "Invalid ZIP"
    names = package.namelist()
    assert len(names) == len(set(names)) == manifest["file_count"]
    assert set(names) == set(expected), "Unexpected distribution files"
    verified = []
    for name in names:
        path = pathlib.PurePosixPath(name)
        assert not path.is_absolute() and ".." not in path.parts
        data = package.read(name)
        assert digest(data) == expected[name], "File checksum mismatch: " + name
        verified.append((name, data))
    for name, data in verified:
        destination = root / "_site" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
print("Verified Azure Covenant", manifest["version"], "-", len(expected), "game files")
