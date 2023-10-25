from dataclasses import dataclass

from fastapi_sso.sso.github import GithubSSO
from fastapi_sso.sso.google import GoogleSSO
from fastapi_sso.sso.microsoft import MicrosoftSSO


@dataclass(frozen=True)
class SSOHolder:
    google: GoogleSSO
    microsoft: MicrosoftSSO
    github: GithubSSO

    @classmethod
    def create(
        cls,
        *,
        google_client_id: str,
        google_client_secret: str,
        google_redirect_uri: str,
        github_client_id: str,
        github_client_secret: str,
        github_redirect_uri: str,
        microsoft_client_id: str,
        microsoft_client_secret: str,
        microsoft_tenant: str,
        microsoft_redirect_uri: str,
    ) -> "SSOHolder":
        return SSOHolder(
            google=GoogleSSO(
                client_id=google_client_id, client_secret=google_client_secret, redirect_uri=google_redirect_uri
            ),
            github=GithubSSO(
                client_id=github_client_id, client_secret=github_client_secret, redirect_uri=github_redirect_uri
            ),
            microsoft=MicrosoftSSO(
                client_id=microsoft_client_id,
                client_secret=microsoft_client_secret,
                redirect_uri=microsoft_redirect_uri,
                tenant=microsoft_tenant,
            ),
        )
