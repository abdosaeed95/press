import unittest

from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request, Response

from press.mcp_transport import after_request


class TestMCPTransport(unittest.TestCase):
	def response_for(self, path, method, status):
		request = Request(EnvironBuilder(path=path, method=method).get_environ())
		response = Response(b"{}", status=status, content_type="application/json")
		response.headers["X-Verification"] = "preserved"
		after_request(request, response)
		return response

	def test_notification_has_zero_byte_body(self):
		response = self.response_for("/api/method/fodista_cloud_mcp", "POST", 202)
		self.assertEqual(response.status_code, 202)
		self.assertEqual(response.get_data(), b"")
		self.assertEqual(response.content_length, 0)
		self.assertEqual(response.headers["X-Verification"], "preserved")

	def test_unrelated_responses_are_preserved(self):
		cases = [("/api/method/other", "POST", 202), ("/api/method/fodista_cloud_mcp", "GET", 202)]
		cases += [
			("/api/method/fodista_cloud_mcp", "POST", status) for status in (200, 400, 401, 403, 405, 500)
		]
		for path, method, status in cases:
			with self.subTest(path=path, method=method, status=status):
				response = self.response_for(path, method, status)
				self.assertEqual(response.status_code, status)
				self.assertEqual(response.get_data(), b"{}")


if __name__ == "__main__":
	unittest.main()
