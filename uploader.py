#!/usr/bin/env python3
"""Download a file from a direct link and upload it to Files.ir (my.files.ir) via API token."""
from __future__ import annotations
import argparse, asyncio, os, re, sys, pathlib, urllib.parse
import httpx
from filesir import FilesIrClient
from filesir.exceptions import FilesIrError

BASE_URL = os.getenv("FILESIR_BASE_URL", "https://my.files.ir/api/v1")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"

def human(n: float) -> str:
    for u in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024: return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} PB"

def filename_from(resp: httpx.Response, url: str) -> str:
    cd = resp.headers.get("content-disposition", "")
    m = re.search(r"filename\*=(?:UTF-8'')?([^;]+)", cd) or re.search(r'filename="?([^";]+)', cd)
    name = m.group(1) if m else os.path.basename(urllib.parse.urlparse(str(resp.url)).path)
    name = urllib.parse.unquote(name).strip().strip('"') or "file.bin"
    return re.sub(r'[\\/:*?"<>|]', "_", name)

async def download(url: str, outdir: str = "downloads", name: str | None = None) -> pathlib.Path:
    pathlib.Path(outdir).mkdir(exist_ok=True)
    async with httpx.AsyncClient(follow_redirects=True, timeout=httpx.Timeout(60, read=None),
                                 headers={"User-Agent": UA}) as c:
        async with c.stream("GET", url) as r:
            r.raise_for_status()
            path = pathlib.Path(outdir) / (name or filename_from(r, url))
            total = int(r.headers.get("content-length") or 0)
            done, last = 0, -1
            with open(path, "wb") as f:
                async for chunk in r.aiter_bytes(1024 * 1024):
                    f.write(chunk); done += len(chunk)
                    pct = int(done * 100 / total) if total else -1
                    if pct != last and pct % 5 == 0:
                        last = pct; print(f"  download {pct}% ({human(done)}/{human(total)})", flush=True)
    print(f"Downloaded: {path.name} ({human(done)})")
    return path

async def upload(path: pathlib.Path, token: str, parent_id: int | None) -> list[str]:
    async with FilesIrClient(access_token=token, base_url=BASE_URL) as client:
        last = -1
        def progress(done: int, total: int) -> None:
            nonlocal last
            pct = int(done * 100 / total) if total else 100
            if pct != last and pct % 5 == 0:
                last = pct; print(f"  upload {pct}% ({human(done)}/{human(total)})", flush=True)
        entry = await client.uploads.upload_file(str(path), parent_id=parent_id, progress=progress)
        print(f"Uploaded: id={entry.id} name={entry.name}")
        links = []
        try:
            link = await client.links.create(entry.id, allow_download=True)
            if link.hash:
                links.append(f"https://files.ir/drive/s/{link.hash}")
        except FilesIrError as e:
            print(f"Could not create public link: {e}")
        return links

def write_summary(lines: list[str]) -> None:
    p = os.getenv("GITHUB_STEP_SUMMARY")
    if p:
        with open(p, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

async def main() -> int:
    ap = argparse.ArgumentParser(description="URL -> Files.ir")
    ap.add_argument("url", help="direct download link")
    ap.add_argument("--name", default=os.getenv("FILE_NAME") or None, help="override file name")
    ap.add_argument("--parent-id", type=int,
                    default=int(os.getenv("PARENT_ID")) if os.getenv("PARENT_ID") else None,
                    help="target folder id on Files.ir (default: root)")
    ap.add_argument("--keep", action="store_true", help="keep downloaded file")
    a = ap.parse_args()

    token = os.getenv("FILESIR_TOKEN", "").strip()
    if not token:
        print("FILESIR_TOKEN is not set (Files.ir > account settings > developers)", file=sys.stderr)
        return 1
    try:
        path = await download(a.url, name=a.name)
        links = await upload(path, token, a.parent_id)
    except (httpx.HTTPError, FilesIrError) as e:
        print(f"Failed: {e}", file=sys.stderr)
        write_summary(["## ❌ Failed", f"`{e}`"])
        return 2
    finally:
        if not a.keep and "path" in locals() and path.exists():
            path.unlink()

    print("\n=== Files.ir link ===")
    print("\n".join(links) or "(uploaded, but no public link; check your drive)")
    write_summary(["## ✅ Uploaded to Files.ir", f"**{path.name}**", *[f"- {l}" for l in links]])
    return 0

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
