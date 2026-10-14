#!/usr/bin/env python3
"""Build the fixed landscape.3 source archive with explicit local inputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import zipfile

SOURCE_SHA256 = "9e1c718833d99734b5d3d2fa2a341d248e33ee5f2989c9a440507393f7b753dc"
TASKS = {
    "debug": ":mobile:assembleDebug",
    "standalone-debug": ":mobile:assembleStandaloneDebug",
    "standalone-release": ":mobile:assembleStandaloneRelease",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path,
                        default=Path(__file__).parent / "DiPlay-CN-landscape.3-corresponding-source.zip")
    parser.add_argument("--destination", type=Path, default=Path("build-landscape3"))
    parser.add_argument("--java-home", type=Path, required=True)
    parser.add_argument("--android-sdk", type=Path, required=True)
    parser.add_argument("--task", choices=TASKS, default="debug")
    parser.add_argument("--auth-assets", type=Path)
    parser.add_argument("--keystore", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    destination = args.destination.resolve()
    source = destination / "DiPlay-CN-Landscape"
    wrapper = "gradlew.bat" if os.name == "nt" else "./gradlew"
    command = [wrapper, "--console=plain", "--max-workers=2", TASKS[args.task]]
    if args.dry_run:
        print(json.dumps({"plan_only": True, "source_zip": str(args.source_zip.resolve()),
                          "destination": str(destination), "cwd_after_extraction": str(source),
                          "command": command, "task": args.task}, indent=2))
        return 0
    if destination.exists():
        parser.error("Destination already exists; choose a new --destination to preserve existing work")
    if not args.java_home.is_dir() or not args.android_sdk.is_dir():
        parser.error("JDK and Android SDK directories must exist")
    if args.task != "debug":
        if args.auth_assets is None or not all(
            (args.auth_assets / "offline-mfi" / name).is_file()
            for name in ("identity.pk8", "certificate.p7b")
        ):
            parser.error("Standalone builds require explicit --auth-assets with both runtime files")
    if args.task == "standalone-release":
        if args.keystore is None or not args.keystore.is_file():
            parser.error("Standalone release requires --keystore")
        if not all(os.environ.get(name) for name in (
            "ANDROID_KEYSTORE_PASSWORD", "ANDROID_KEY_ALIAS", "ANDROID_KEY_PASSWORD"
        )):
            parser.error("Set all three signing environment variables documented in BUILDING.md")
    with args.source_zip.open("rb") as stream:
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != SOURCE_SHA256:
        parser.error("Source archive SHA-256 does not match the published landscape.3 snapshot")
    with zipfile.ZipFile(args.source_zip) as archive:
        for entry in archive.infolist():
            target = (destination / entry.filename).resolve()
            if destination not in target.parents or stat.S_ISLNK(entry.external_attr >> 16):
                parser.error("Unsafe source archive entry")
        destination.mkdir(parents=True)
        archive.extractall(destination)
    (source / "gradlew").chmod(0o755)
    sdk_path = str(args.android_sdk.resolve()).replace("\\", "\\\\")
    (source / "local.properties").write_text("sdk.dir=" + sdk_path + "\n", encoding="utf-8")
    env = os.environ.copy()
    env.update(JAVA_HOME=str(args.java_home.resolve()), ANDROID_HOME=str(args.android_sdk.resolve()))
    if args.auth_assets:
        env["DIPLAY_AUTH_ASSETS_DIR"] = str(args.auth_assets.resolve())
    if args.keystore:
        env["ANDROID_KEYSTORE_PATH"] = str(args.keystore.resolve())
    return subprocess.run(command, cwd=source, env=env).returncode


if __name__ == "__main__":
    raise SystemExit(main())
