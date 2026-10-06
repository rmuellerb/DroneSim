# simulator/auth_hooks.py
import logging
import os

from django.contrib.auth.models import Group
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from allauth.socialaccount.models import SocialAccount

logger = logging.getLogger("auth_hooks")

PROVIDER_ID = os.environ.get("OIDC_PROVIDER_ID", "authentik")
ADMIN_GROUP = os.environ.get("OIDC_ADMIN_GROUP", "dronesim-admins")
DEFAULT_GROUP = os.environ.get("OIDC_DEFAULT_GROUP", "dronesim-users")
GROUP_PREFIXES = [p.strip() for p in os.environ.get("OIDC_GROUP_PREFIXES", "dronesim-").split(",") if p.strip()]

def extract_groups(extra_data: dict) -> list[str]:
    if not extra_data:
        return []

    if "userinfo" in extra_data and isinstance(extra_data["userinfo"], dict):
        groups = extra_data["userinfo"].get("groups")
        if isinstance(groups, list):
            return groups

    if "id_token" in extra_data and isinstance(extra_data["id_token"], dict):
        groups = extra_data["id_token"].get("groups")
        if isinstance(groups, list):
            return groups

    return []

def filter_relevant_groups(groups: list[str]) -> set[str]:
    if not groups:
        return set()
    if not GROUP_PREFIXES:
        return set(groups)
    return {g for g in groups if any(g.startswith(pref) for pref in GROUP_PREFIXES)}

def apply_user_roles(user, extra_data: dict) -> None:
    raw_groups = extract_groups(extra_data)
    wanted = filter_relevant_groups(raw_groups)

    if not wanted:
        wanted = {DEFAULT_GROUP}

    group_objs = []
    for gname in sorted(wanted):
        grp, _ = Group.objects.get_or_create(name=gname)
        group_objs.append(grp)

    user.groups.set(group_objs)

    is_admin = ADMIN_GROUP in wanted
    changed = False
    if user.is_staff != is_admin:
        user.is_staff = is_admin
        changed = True
    if user.is_superuser != is_admin:
        user.is_superuser = is_admin
        changed = True
    if changed:
        user.save(update_fields=["is_staff", "is_superuser"])

    logger.warning("OIDC roles synced: user=%s admin=%s groups=%s", user.username, is_admin, sorted(wanted))

@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    # allauth speichert bei OIDC die provider_id (z.B. "authentik"),
    # nicht "openid_connect" - daher hier PROVIDER_ID.
    sa = SocialAccount.objects.filter(user=user, provider=PROVIDER_ID).first()
    if sa is None:
        return  # z.B. lokaler Login ueber /admin/ oder /api-auth/
    apply_user_roles(user, sa.extra_data or {})
