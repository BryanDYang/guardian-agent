"""Private Supabase Storage accessed only by the backend after membership checks."""

import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen


class StorageError(RuntimeError):
    pass


class SupabaseAudio:
    def __init__(self, url: str, key: str, bucket: str = "meeting-audio"):
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or not key:
            raise ValueError("Shared storage requires a Supabase URL and server key")
        self.base = url.rstrip("/") + "/storage/v1"
        self.key = key
        self.bucket = bucket

    def request(self, method, path, data=None, headers=None):
        request = Request(
            self.base + path,
            data=data,
            method=method,
            headers={"apikey": self.key, "Authorization": f"Bearer {self.key}"}
            | (headers or {}),
        )
        try:
            return urlopen(request, timeout=120)
        except HTTPError as exc:
            # Never expose response bodies, URLs, or privileged keys in app errors.
            raise StorageError(f"Audio storage returned HTTP {exc.code}") from None
        except OSError:
            raise StorageError("Audio storage is unavailable") from None

    def path(self, key):
        return f"/{quote(self.bucket, safe='')}/{quote(key, safe='/')}"

    def check(self):
        with self.request("GET", "/bucket/" + quote(self.bucket, safe="")) as response:
            bucket = json.load(response)
            if bucket.get("public") is not False:
                raise StorageError("Shared audio bucket must be private")

    def upload(self, key, path: Path):
        # File object streams the request; Content-Length prevents chunked uploads.
        with path.open("rb") as body:
            with self.request(
                "POST",
                "/object" + self.path(key),
                body,
                {
                    "Content-Type": "application/octet-stream",
                    "Content-Length": str(path.stat().st_size),
                    "x-upsert": "false",
                },
            ):
                pass

    def download(self, key, path: Path):
        with self.request("GET", "/object/authenticated" + self.path(key)) as response:
            with path.open("wb") as target:
                while chunk := response.read(1024 * 1024):
                    target.write(chunk)

    def delete(self, key):
        with self.request(
            "DELETE",
            "/object/" + quote(self.bucket, safe=""),
            json.dumps({"prefixes": [key]}).encode(),
            {"Content-Type": "application/json"},
        ):
            pass

    def signed_url(self, key):
        with self.request(
            "POST",
            "/object/sign" + self.path(key),
            b'{"expiresIn": 60}',
            {"Content-Type": "application/json"},
        ) as response:
            signed = json.load(response)["signedURL"]
        # Supabase returns a path relative to /storage/v1.
        if not signed.startswith("/object/sign/"):
            raise StorageError("Unexpected audio URL from storage")
        return self.base + signed
