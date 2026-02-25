import os
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.providers.openid_connect.provider import OpenIDConnectProvider

class Command(BaseCommand):
    help = "Bootstrap django-allauth OIDC SocialApp + Site from environment variables (idempotent)."

    def handle(self, *args, **options):
        domain = os.environ.get("PUBLIC_DOMAIN", "dronesim.facets-labs.com")
        site_name = os.environ.get("PUBLIC_SITE_NAME", "DroneSim")

        provider_id = os.environ["OIDC_PROVIDER_ID"]
        name = os.environ.get("OIDC_NAME", "Authentik")
        client_id = os.environ["OIDC_CLIENT_ID"]
        secret = os.environ["OIDC_CLIENT_SECRET"]
        server_url = os.environ["OIDC_SERVER_URL"]

        site, _ = Site.objects.get_or_create(id=1, defaults={
            "domain": domain,
            "name": site_name
        })

        if site.domain != domain or site.name != site_name:
            site.domain = domain
            site.name = site_name
            site.save()

        app, created = SocialApp.objects.get_or_create(
            provider=OpenIDConnectProvider.id,  # "openid_connect"
            provider_id=provider_id,
            defaults={
                "name": name,
                "client_id": client_id,
                "secret": secret,
                "settings": {"server_url": server_url},
            },
        )

        if not created:
            changed = False
            if app.name != name:
                app.name = name
                changed = True
            if app.client_id != client_id:
                app.client_id = client_id
                changed = True
            if app.secret != secret:
                app.secret = secret
                changed = True
            if (app.settings or {}).get("server_url") != server_url:
                app.settings = {"server_url": server_url}
                changed = True
            if changed:
                app.save()

        app.sites.add(site)

        self.stdout.write(self.style.SUCCESS(
            f"OIDC bootstrap complete.\n"
            f"Callback URL:\n"
            f"https://{domain}/accounts/oidc/{provider_id}/login/callback/\n"
            f"SocialApp count now: {SocialApp.objects.count()}"
        ))
