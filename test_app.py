import unittest
import json
from app import app, link_service


class ShortenerTestCase(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        link_service.clear()

    def test_create_short_link_success(self):
        payload = {"url": "https://example.com/item/123"}
        response = self.client.post("/api/links", json=payload)

        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertIn("code", data)
        self.assertEqual(len(data["code"]), 6)
        self.assertEqual(data["url"], "https://example.com/item/123")
        self.assertEqual(data["clicks"], 0)

    def test_duplicate_submission_is_idempotent(self):
        payload = {"url": "https://example.com/idempotent-test"}
        res1 = self.client.post("/api/links", json=payload)
        res2 = self.client.post("/api/links", json=payload)

        self.assertEqual(res1.status_code, 201)
        self.assertEqual(res2.status_code, 201)

        code1 = res1.get_json()["code"]
        code2 = res2.get_json()["code"]
        self.assertEqual(code1, code2)

    def test_malformed_url_rejected_with_400(self):
        bad_urls = [
            "invalid-url-without-protocol",
            "ftp://example.com",
            "http://",
            "   ",
            ""
        ]
        for url in bad_urls:
            response = self.client.post("/api/links", json={"url": url})
            self.assertEqual(response.status_code, 400)
            data = response.get_json()
            self.assertEqual(data.get("field"), "url")
            self.assertIn("error", data)

    def test_malformed_json_rejected_with_400(self):
        response = self.client.post(
            "/api/links",
            data="{invalid json payload",
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("field", data)

    def test_follow_redirect_302_and_increments_clicks(self):
        # 1. Create short link
        create_res = self.client.post("/api/links", json={"url": "https://example.com/target-page"})
        code = create_res.get_json()["code"]

        # 2. Follow short link -> 302 Found
        redirect_res = self.client.get(f"/{code}")
        self.assertEqual(redirect_res.status_code, 302)
        self.assertEqual(redirect_res.headers.get("Location"), "https://example.com/target-page")

        # 3. Check stats -> clicks = 1
        stats_res = self.client.get(f"/api/links/{code}")
        self.assertEqual(stats_res.status_code, 200)
        self.assertEqual(stats_res.get_json()["clicks"], 1)

    def test_unknown_code_returns_404(self):
        # Stats lookup for non-existent code
        stats_res = self.client.get("/api/links/nonexistent999")
        self.assertEqual(stats_res.status_code, 404)
        self.assertEqual(stats_res.get_json().get("field"), "code")

        # Follow non-existent code
        redirect_res = self.client.get("/nonexistent999")
        self.assertEqual(redirect_res.status_code, 404)
        self.assertEqual(redirect_res.get_json().get("field"), "code")


if __name__ == "__main__":
    unittest.main()
