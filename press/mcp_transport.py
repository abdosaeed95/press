def after_request(request, response):
	# MCP notifications require HTTP 202 with no response body.
	if (
		request.path == "/api/method/fodista_cloud_mcp"
		and request.method == "POST"
		and response.status_code == 202
	):
		response.set_data(b"")
