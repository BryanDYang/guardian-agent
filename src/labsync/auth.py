"""Verifies Supabase Auth access tokens (Accounts & Voice Identity spec, FR-AUTH-5).

Supabase signs tokens with an asymmetric key (ES256 or RS256) published at the
project's JWKS endpoint, or with a shared HS256 secret on projects that still use
the legacy key. Both are accepted; HS256 only when the secret is configured.
"""

import jwt

AUDIENCE = "authenticated"
ASYMMETRIC = ("ES256", "RS256")


class InvalidToken(Exception):
    """The token is malformed, expired, or not issued by this Supabase project."""


class TokenVerifier:
    def __init__(self, supabase_url: str, jwt_secret: str | None = None):
        self.issuer = supabase_url.rstrip("/") + "/auth/v1"
        # Keys are fetched once and cached; an unknown key id triggers a refetch,
        # so key rotation in Supabase needs no restart.
        self._jwks = jwt.PyJWKClient(
            self.issuer + "/.well-known/jwks.json", cache_keys=True, lifespan=600
        )
        self._secret = jwt_secret

    def verify(self, token: str) -> dict:
        """Return the token's claims, or raise InvalidToken."""
        try:
            algorithm = jwt.get_unverified_header(token).get("alg")
            if algorithm in ASYMMETRIC:
                key = self._jwks.get_signing_key_from_jwt(token).key
            elif algorithm == "HS256" and self._secret:
                key = self._secret
            else:
                raise InvalidToken(f"Unsupported signing algorithm: {algorithm}")
            return jwt.decode(
                token,
                key,
                algorithms=[algorithm],
                audience=AUDIENCE,
                issuer=self.issuer,
                options={"require": ["exp", "iss", "aud", "sub"]},
            )
        except (jwt.PyJWTError, jwt.PyJWKClientError) as exc:
            raise InvalidToken(str(exc)) from exc
