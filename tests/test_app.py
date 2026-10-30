"""Contract tests use isolated provider fixtures; the running app has no fixtures."""
import os
import unittest
from unittest.mock import Mock, patch

import requests
from app import app, FIELDS, QualificationError, validate_result


def contract_result(score=70):
    return dict.fromkeys(FIELDS, None) | {
        "category": "sales inquiry", "intent": "request information", "score": score,
        "priority": "low" if score < 40 else "medium" if score < 70 else "high",
        "summary": "A request for information.", "suggested_reply": "Could you share your requirements?",
    }


class AppTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_home_is_customer_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'id="lead-message"', response.data)
        self.assertIn(b'Welcome to a clearer', response.data)
        self.assertEqual(response.mimetype, "text/html")

    def test_bad_input_never_calls_provider(self):
        with patch("app.requests.post") as provider:
            for body in [{}, [], None, {"message": 12}, {"message": "  "}, {"message": "x" * 12001}]:
                with self.subTest(body_type=type(body).__name__):
                    response = self.client.post("/qualify", json=body)
                    self.assertIn(response.status_code, (400, 415))
                    self.assertIn("error", response.json)
            self.assertEqual(self.client.post("/qualify", data="message=test").status_code, 415)
            self.assertEqual(self.client.post("/qualify", data="{bad", content_type="application/json").status_code, 400)
            self.assertEqual(self.client.post("/qualify", data="x" * 70000, content_type="application/json").status_code, 413)
            provider.assert_not_called()

    def test_missing_key_has_clear_error(self):
        with patch.dict(os.environ, {"COHERE_API_KEY": ""}), patch("app.requests.post") as provider:
            response = self.client.post("/qualify", json={"message": "Could you send information?"})
            self.assertEqual(response.status_code, 503)
            self.assertIn("COHERE_API_KEY", response.json["error"])
            provider.assert_not_called()

    def test_score_boundaries_and_exact_contract(self):
        for score in [0, 39, 40, 69, 70, 100]:
            self.assertEqual(set(validate_result(contract_result(score))), set(FIELDS))
        for value in [-1, 101, 50.0, True, "70", None]:
            with self.assertRaises(QualificationError):
                validate_result(contract_result() | {"score": value})
        for update in [{"priority": "medium"}, {"name": ""}, {"summary": None}, {"extra": "no"}]:
            with self.assertRaises(QualificationError):
                validate_result(contract_result() | update)
        with self.assertRaises(QualificationError):
            validate_result({})

    def test_upstream_errors_are_sanitized(self):
        with patch.dict(os.environ, {"COHERE_API_KEY": "unit-test-only-sentinel"}):
            for status, expected in [(401, 502), (403, 502), (429, 429), (500, 502)]:
                provider_response = Mock(status_code=status, ok=False, text="private upstream body")
                with patch("app.requests.post", return_value=provider_response):
                    response = self.client.post("/qualify", json={"message": "Help us please"})
                    self.assertEqual(response.status_code, expected)
                    self.assertNotIn("private upstream body", response.get_data(as_text=True))
                    self.assertNotIn("unit-test-only-sentinel", response.get_data(as_text=True))
            for exception, expected in [(requests.Timeout(), 504), (requests.ConnectionError(), 502)]:
                with patch("app.requests.post", side_effect=exception):
                    self.assertEqual(self.client.post("/qualify", json={"message": "Help us please"}).status_code, expected)

    def test_provider_json_is_validated_and_request_uses_cohere(self):
        import json
        provider_response = Mock(ok=True, status_code=200)
        provider_response.json.return_value = {"finish_reason": "COMPLETE", "message": {"content": [{"type": "text", "text": json.dumps(contract_result())}]}}
        with patch.dict(os.environ, {"COHERE_API_KEY": "unit-test-only-sentinel"}), patch("app.requests.post", return_value=provider_response) as provider:
            response = self.client.post("/qualify", json={"message": "Help us please"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json, contract_result())
            self.assertEqual(provider.call_args.args[0], "https://api.cohere.com/v2/chat")
            self.assertEqual(provider.call_args.kwargs["json"]["messages"][-1]["content"], "Help us please")
            for text in ['{"score": 99}', 'not JSON', json.dumps(contract_result() | {"score": 99, "priority": "low"})]:
                provider_response.json.return_value["message"]["content"][0]["text"] = text
                self.assertEqual(self.client.post("/qualify", json={"message": "Help us please"}).status_code, 502)
            provider_response.json.return_value["finish_reason"] = "MAX_TOKENS"
            self.assertEqual(self.client.post("/qualify", json={"message": "Help us please"}).status_code, 502)


if __name__ == "__main__":
    unittest.main()
