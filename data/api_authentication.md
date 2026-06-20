# API Authentication Reference

All API requests must include a bearer token in the authorization header.

Required format:

`Authorization: Bearer <token>`

If a request fails with 401, confirm that the token is active, correctly scoped, and sent to the intended environment.