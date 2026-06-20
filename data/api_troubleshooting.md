# API Troubleshooting Guide

If an API request returns `401 Unauthorized`, verify the bearer token header format:

- Use `Authorization: Bearer <token>`.
- Confirm the token has not expired.
- Check that the correct environment is selected.
- Review server logs for request ID and timestamp.

Production access tokens expire every 90 days. If the token is valid but the request still fails, regenerate credentials and retry the request.