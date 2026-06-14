"""Authentication: PBKDF2 password hashing, HS256 JWTs, and Google OAuth.

Implemented with the Python standard library only (hashlib + hmac + base64) so
there are no native-build dependencies — JWT email/password auth works out of
the box. Set GOOGLE_CLIENT_ID/SECRET to additionally enable Google OAuth.
"""
