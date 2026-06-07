#!/usr/bin/env python3
"""GitHub Pages へ公開（git add/commit/push）。毎朝のタスクがこれを実行する。"""
import json, os, subprocess, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(os.path.join(ROOT, ".gh-deploy.json")))


def git(*args):
    return subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True)


def main():
    git("add", "-A")
    git("-c", "user.email=minominori2005@gmail.com", "-c", "user.name=Minori Hayashi",
        "commit", "-m", "update " + datetime.date.today().isoformat())  # 変更無しならno-op
    url = "https://x-access-token:%s@github.com/%s.git" % (cfg["token"], cfg["full_name"])
    git("remote", "set-url", "origin", url)
    p = git("push", "origin", "main")
    page = "https://%s.github.io/%s/" % (cfg["user"], cfg["repo"])
    if p.returncode == 0:
        print("デプロイ完了（GitHub Pages）: " + page)
    else:
        print("PUSH失敗: " + (p.stderr or "")[:300])
        print("URL: " + page)


if __name__ == "__main__":
    main()
