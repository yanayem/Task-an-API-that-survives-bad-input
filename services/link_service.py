import random
import string
from threading import Lock
from urllib.parse import urlparse
from datetime import datetime, timezone


class ValidationException(Exception):
    def __init__(self, field: str, message: str):
        super().__init__(message)
        self.field = field
        self.message = message


class ShortLink:
    def __init__(self, code: str, target_url: str):
        self.code = code
        self.target_url = target_url
        self.clicks = 0
        self.created_at = datetime.now(timezone.utc).isoformat()

    def increment_clicks(self) -> int:
        self.clicks += 1
        return self.clicks

    def to_dict(self, base_url: str) -> dict:
        short_url = f"{base_url.rstrip('/')}/{self.code}"
        return {
            "code": self.code,
            "url": self.target_url,
            "short_url": short_url,
            "clicks": self.clicks,
            "created_at": self.created_at
        }


class LinkService:
    ALPHABET = string.ascii_letters + string.digits
    CODE_LENGTH = 6

    def __init__(self):
        self._code_to_link = {}
        self._url_to_code = {}
        self._lock = Lock()

    def create_or_get_short_link(self, raw_url: str) -> ShortLink:
        """
        Validates raw_url first. If valid, creates a new short code or returns
        an existing one if identical URL was previously submitted (idempotent).
        """
        validated_url = self.validate_and_normalize_url(raw_url)

        with self._lock:
            if validated_url in self._url_to_code:
                code = self._url_to_code[validated_url]
                return self._code_to_link[code]

            code = self._generate_unique_code()
            short_link = ShortLink(code, validated_url)
            self._url_to_code[validated_url] = code
            self._code_to_link[code] = short_link
            return short_link

    def get_and_follow_link(self, code: str) -> ShortLink:
        """
        Look up a short link by code, increment click count, and return it.
        Returns None if code is unknown.
        """
        if not code:
            return None
        with self._lock:
            link = self._code_to_link.get(code)
            if link:
                link.increment_clicks()
                return link
            return None

    def get_link_stats(self, code: str) -> ShortLink:
        """
        Look up a short link by code without incrementing click count.
        Returns None if code is unknown.
        """
        if not code:
            return None
        with self._lock:
            return self._code_to_link.get(code)

    def validate_and_normalize_url(self, raw_url: str) -> str:
        """
        Validates URL at boundary before storage.
        Raises ValidationException(field="url", message=...) if invalid.
        """
        if not raw_url or not isinstance(raw_url, str) or not raw_url.strip():
            raise ValidationException("url", "The 'url' field is required and cannot be empty.")

        trimmed_url = raw_url.strip()

        try:
            parsed = urlparse(trimmed_url)
        except Exception as e:
            raise ValidationException("url", f"Invalid URL syntax: {str(e)}")

        if not parsed.scheme or not parsed.netloc:
            raise ValidationException(
                "url",
                "URL must be an absolute URL including protocol scheme (http or https) and a valid host name."
            )

        if parsed.scheme.lower() not in ("http", "https"):
            raise ValidationException("url", "URL scheme must be 'http' or 'https'.")

        return trimmed_url

    def _generate_unique_code(self) -> str:
        while True:
            code = ''.join(random.choices(self.ALPHABET, k=self.CODE_LENGTH))
            if code not in self._code_to_link:
                return code

    def clear(self):
        with self._lock:
            self._code_to_link.clear()
            self._url_to_code.clear()
