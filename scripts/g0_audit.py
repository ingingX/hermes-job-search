#!/usr/bin/env python3
"""Local G0 evidence checks. Never prints or stores credential contents."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / ".runtime" / "hermes"
PRIVATE = ROOT / "work"
HOST_HERMES = Path.home() / ".hermes"
IMAGE = "hermes-job-search:local"
BASE = "nousresearch/hermes-agent@sha256:99641e57ec762c59e54cb44aa6746b7fc68c18b3c5ddb088af54234c613d9294"
BUN = "oven/bun@sha256:923bedb355f7746666659f71e724998159a5c8c54bd1cb1030e1975a0698415b"


def command(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True)


def check(condition, message):
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def static_check():
    service = json.loads(command("docker", "compose", "config", "--format", "json"))["services"]["hermes"]
    mounts = {(v["source"], v["target"]) for v in service.get("volumes", [])}
    expected = {(str(DATA), "/opt/data"), (str(PRIVATE), "/workspace")}
    check(mounts == expected, f"unexpected Compose mounts: {mounts}")
    check(all(v.get("type") == "bind" and not v.get("bind", {}).get("create_host_path", True)
              for v in service["volumes"]), "mount type or host-path creation")
    check(service.get("image") == IMAGE, "image name changed")
    check(service.get("build", {}).get("context") == str(ROOT), "build context changed")
    dockerfile = (ROOT / "Dockerfile").read_text()
    check(BASE in dockerfile and BUN in dockerfile, "base image digest changed")
    modes = {v["target"]: v.get("read_only", False) for v in service["volumes"]}
    check(modes.get("/workspace") is False, "private workspace is read-only")
    check(service.get("privileged") is not True, "privileged container")
    check("no-new-privileges:true" in service.get("security_opt", []), "missing no-new-privileges")
    check(not service.get("ports") and not service.get("network_mode"), "published ports or host network")
    check(service.get("restart") == "no", "restart policy")
    env = service.get("environment", {})
    check(env.get("HERMES_HOME") == "/opt/data" and env.get("CODEX_HOME") == "/opt/data/codex",
          "state directories")
    check(env.get("HERMES_WRITE_SAFE_ROOT") == "/opt/data:/workspace",
          "write-safe roots")
    check(DATA.is_dir() and (PRIVATE / ".hermes-workspace").is_file(),
          "missing initialized private workspace")
    print("PASS: Compose static isolation checks")


def inspect(container):
    info = json.loads(command("docker", "inspect", container))[0]
    mounts = {(m["Source"], m["Destination"]) for m in info.get("Mounts", [])}
    expected = {(str(DATA), "/opt/data"), (str(PRIVATE), "/workspace")}
    check(mounts == expected, f"unexpected live mounts: {mounts}")
    modes = {m["Destination"]: m.get("RW") for m in info.get("Mounts", [])}
    check(modes.get("/workspace") is True, "live private workspace is read-only")
    host = info["HostConfig"]
    check(host.get("Privileged") is False, "privileged live container")
    check("no-new-privileges:true" in host.get("SecurityOpt", []), "missing live no-new-privileges")
    check(not host.get("PortBindings"), "published live ports")
    check(host.get("RestartPolicy", {}).get("Name") in ("", "no"), "live restart policy")
    print("PASS: live container mount and security checks")


def file_fingerprint(path):
    if path.is_symlink():
        return {"type": "symlink", "target_hash": hashlib.sha256(str(path.readlink()).encode()).hexdigest()}
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"type": "file", "sha256": digest.hexdigest()}


def snapshot(output):
    check(HOST_HERMES.is_dir(), "host Hermes directory not found")
    selected = [HOST_HERMES / name for name in ("config.yaml", ".env", "auth.json", "SOUL.md")]
    for name in ("skills", "memories", "sessions"):
        folder = HOST_HERMES / name
        if folder.is_dir():
            selected.extend(path for path in folder.rglob("*") if path.is_file() or path.is_symlink())
    fingerprints = {str(path.relative_to(HOST_HERMES)): file_fingerprint(path)
                    for path in selected if path.is_file() or path.is_symlink()}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(fingerprints, indent=2, sort_keys=True) + "\n")
    output.chmod(0o600)
    print(f"Snapshot saved: {len(fingerprints)} host Hermes files; hashes only")


def compare(before, after):
    old = json.loads(before.read_text())
    new = json.loads(after.read_text())
    changes = sorted(key for key in old.keys() | new.keys() if old.get(key) != new.get(key))
    print(f"Host Hermes changed files: {len(changes)}")
    if changes:
        print("Review changes against concurrent host Hermes activity:")
        for key in changes:
            print(key)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("static")
    sub.add_parser("inspect").add_argument("container")
    sub.add_parser("snapshot").add_argument("output", type=Path)
    pair = sub.add_parser("compare")
    pair.add_argument("before", type=Path)
    pair.add_argument("after", type=Path)
    args = parser.parse_args()
    if args.action == "static":
        static_check()
    elif args.action == "inspect":
        inspect(args.container)
    elif args.action == "snapshot":
        snapshot(args.output)
    else:
        compare(args.before, args.after)


if __name__ == "__main__":
    main()
