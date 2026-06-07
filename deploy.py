#!/usr/bin/env python3
"""
Netlify へ静的サイトをデプロイする（Node 不要・標準ライブラリのみ）。
初回は新しいサイトを自動作成し、設定を .netlify-deploy.json に保存する。
2回目以降は同じサイトへ再デプロイ（毎朝のタスクがこれを実行）。

使い方:
  1) 環境変数 NETLIFY_AUTH_TOKEN にトークンを入れて初回実行（サイト作成＋デプロイ）
       NETLIFY_AUTH_TOKEN=xxxxx python3 deploy.py
  2) 以降はトークンも .netlify-deploy.json に保存されるので
       python3 deploy.py
     だけで再デプロイ。
"""
import io, json, os, sys, zipfile, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(ROOT, ".netlify-deploy.json")
FILES = ["index.html", "style.css", "data.js", "robots.txt"]
API = "https://api.netlify.com/api/v1"


def load_config():
    if os.path.exists(CONFIG):
        with open(CONFIG) as f:
            return json.load(f)
    return {}


def save_config(cfg):
    with open(CONFIG, "w") as f:
        json.dump(cfg, f, indent=2)
    os.chmod(CONFIG, 0o600)


def api(method, path, token, data=None, ctype="application/json"):
    url = path if path.startswith("http") else API + path
    headers = {"Authorization": "Bearer " + token}
    body = None
    if data is not None:
        if ctype == "application/json":
            body = json.dumps(data).encode()
            headers["Content-Type"] = "application/json"
        else:
            body = data
            headers["Content-Type"] = ctype
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        sys.stderr.write("Netlify API エラー %s: %s\n" % (e.code, e.read().decode("utf-8", "ignore")))
        raise


def make_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name in FILES:
            p = os.path.join(ROOT, name)
            if os.path.exists(p):
                z.write(p, name)
    return buf.getvalue()


def main():
    cfg = load_config()
    token = os.environ.get("NETLIFY_AUTH_TOKEN") or cfg.get("token")
    if not token:
        sys.stderr.write("トークンがありません。NETLIFY_AUTH_TOKEN を設定して初回実行してください。\n")
        sys.exit(1)
    cfg["token"] = token

    if not cfg.get("site_id"):
        site = api("POST", "/sites", token, data={})  # ランダム名のサイトを作成
        cfg["site_id"] = site["id"]
        cfg["url"] = site.get("ssl_url") or site.get("url")
        save_config(cfg)
        print("新しいサイトを作成しました: " + cfg["url"])

    zip_bytes = make_zip()
    dep = api("POST", "/sites/%s/deploys" % cfg["site_id"], token,
              data=zip_bytes, ctype="application/zip")
    save_config(cfg)
    url = cfg.get("url") or dep.get("ssl_url") or dep.get("url")
    print("デプロイ完了: " + str(url))
    print("（状態: %s）" % dep.get("state", "?"))


if __name__ == "__main__":
    main()
