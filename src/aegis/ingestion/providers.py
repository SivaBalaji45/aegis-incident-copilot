"""Registry of status-page sources Aegis polls.

Most providers run Atlassian Statuspage, which exposes a free, unauthenticated
`GET /api/v2/incidents.json` endpoint — no API key, no auth headers. AWS and GCP
run their own status feeds and are modeled separately (see `fetchers.py`).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FeedKind(str, Enum):
    STATUSPAGE = "statuspage"
    AWS_HEALTH = "aws_health"
    GCP_STATUS = "gcp_status"


@dataclass(frozen=True)
class Provider:
    slug: str
    display_name: str
    kind: FeedKind
    url: str


# Atlassian Statuspage feeds: {slug}.statuspage.io/api/v2/incidents.json
_STATUSPAGE_PROVIDERS: list[tuple[str, str, str]] = [
    ("github", "GitHub", "www.githubstatus.com"),
    ("cloudflare", "Cloudflare", "www.cloudflarestatus.com"),
    ("stripe", "Stripe", "status.stripe.com"),
    ("datadog", "Datadog", "status.datadoghq.com"),
    ("pagerduty", "PagerDuty", "status.pagerduty.com"),
    ("twilio", "Twilio", "status.twilio.com"),
    ("slack", "Slack", "slack-status.com"),
    ("zoom", "Zoom", "status.zoom.us"),
    ("okta", "Okta", "status.okta.com"),
    ("heroku", "Heroku", "status.heroku.com"),
    ("npm", "npm", "status.npmjs.org"),
    ("circleci", "CircleCI", "status.circleci.com"),
    ("auth0", "Auth0", "status.auth0.com"),
    ("segment", "Segment", "status.segment.com"),
    ("openai", "OpenAI", "status.openai.com"),
]

PROVIDERS: list[Provider] = [
    Provider(
        slug=slug,
        display_name=name,
        kind=FeedKind.STATUSPAGE,
        url=f"https://{host}/api/v2/incidents.json",
    )
    for slug, name, host in _STATUSPAGE_PROVIDERS
] + [
    Provider(
        slug="aws",
        display_name="AWS",
        kind=FeedKind.AWS_HEALTH,
        url="https://status.aws.amazon.com/rss/all.rss",
    ),
    Provider(
        slug="gcp",
        display_name="Google Cloud",
        kind=FeedKind.GCP_STATUS,
        url="https://status.cloud.google.com/incidents.json",
    ),
]


def get_provider(slug: str) -> Provider:
    for p in PROVIDERS:
        if p.slug == slug:
            return p
    raise KeyError(f"Unknown provider slug: {slug!r}")
