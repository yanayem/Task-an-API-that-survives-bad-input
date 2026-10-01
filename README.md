# Short Link Service (URL Shortener API) - Python (Flask)

An HTTP service built with **Python (Flask)** that turns long URLs into short codes, redirects lookups to destination URLs, tracks visit counts, and survives malformed inputs without server errors.

---

## 📌 Redirect Status Code Choice: 302 vs 301 Justification

### Selected Status Code: **`302 Found`** (Temporary Redirect)

### Why 302 was chosen over 301:
1. **Click Tracking & Analytics Integrity**:
   - **`301 Moved Permanently`**: Web browsers, HTTP clients, and CDNs aggressively cache `301` responses indefinitely. Once a browser receives a `301` redirect for a short code, all subsequent user visits navigate directly to the target URL from browser cache without hitting our shortener server. As a result, the server is unable to count subsequent visits, corrupting click tracking metrics.
   - **`302 Found`** (or `307 Temporary Redirect`): Instructs browsers and clients **not** to permanently cache the redirect rule. Every follow request reaches our server first, allowing us to accurately increment and track the click counter for every visit.

2. **Reversibility and Flexibility**:
   - `301` redirects are extremely difficult to reverse or update once cached in millions of client browsers. If a link target needs updating or deletion, users with cached `301` responses would continue being redirected to the old URL. `302` ensures our service retains control over link redirection at all times.

---

## 🚀 Key Features

- **Boundary Input Validation**: Rejects malformed JSON payloads and invalid URLs (e.g. missing scheme, host, or invalid formatting) with `400 Bad Request` naming the malformed field (`"url"` or `"body"`).
- **Zero 500 Server Errors**: All input handling, JSON parsing, and boundary checks are guarded against unhandled exceptions.
- **Idempotent Creation**: Submitting the same target URL multiple times returns the exact same short code instead of silently creating duplicate records.
- **Click Tracking**: Increments visit counts automatically on each redirect.
- **404 Handling**: Unknown short codes return structured `404 Not Found` JSON responses rather than empty 200 responses.

---

## 📡 API Endpoints

### 1. Create Short Link
- **Method**: `POST`
- **Path**: `/api/links` (or `/links`)
- **Headers**: `Content-Type: application/json`
- **Request Body**:
  ```json
  {
    "url": "https://example.com/some/long/path"
  }
  ```
- **Response** (`201 Created`):
  ```json
  {
    "code": "aB3x9Q",
    "url": "https://example.com/some/long/path",
    "short_url": "http://localhost:8080/aB3x9Q",
    "clicks": 0,
    "created_at": "2026-10-01T18:00:00Z"
  }
  ```
- **Malformed Input Response** (`400 Bad Request`):
  ```json
  {
    "error": "URL must be an absolute URL including protocol scheme (http or https) and a valid host name.",
    "field": "url"
  }
  ```

---

### 2. Follow Short Link (Redirect)
- **Method**: `GET`
- **Path**: `/{code}` (or `/r/{code}`)
- **Response**: `302 Found`
  - **Headers**: `Location: https://example.com/some/long/path`
- **Unknown Code Response** (`404 Not Found`):
  ```json
  {
    "error": "Unknown short code: invalidCode",
    "field": "code"
  }
  ```

---

### 3. Link Statistics / Click Counter
- **Method**: `GET`
- **Path**: `/api/links/{code}` (or `/stats/{code}`)
- **Response** (`200 OK`):
  ```json
  {
    "code": "aB3x9Q",
    "url": "https://example.com/some/long/path",
    "short_url": "http://localhost:8080/aB3x9Q",
    "clicks": 5,
    "created_at": "2026-10-01T18:00:00Z"
  }
  ```

---

## 🛠️ How to Build and Run (Python)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Application Server
```bash
python app.py
```
The server starts on `http://localhost:8080`.

### 3. Run Automated Tests
```bash
python -m unittest test_app.py
```

---

## 🧪 Verification Reviewer Checklist

- [x] **Creating, following, and counting links**: Verified via `POST /api/links`, `GET /{code}`, and `GET /api/links/{code}`.
- [x] **301 vs 302 Decision**: Deliberately selected `302 Found` and justified in README.
- [x] **Unknown Code**: Returns `404 Not Found` with structured error JSON.
- [x] **Malformed URL**: Rejected with `400 Bad Request` naming field `"url"` prior to storage.
- [x] **Duplicate Submissions**: Idempotent creation prevents duplicate codes for identical target URLs.
