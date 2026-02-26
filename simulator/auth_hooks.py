import logging
from django.dispatch import receiver
from allauth.socialaccount.signals import social_account_added, social_account_updated

logger = logging.getLogger("auth_hooks")

def extract_groups(extra_data: dict):
    if not extra_data:
        return []

    if "userinfo" in extra_data and "groups" in extra_data["userinfo"]:
        return extra_data["userinfo"]["groups"]

    if "id_token" in extra_data and "groups" in extra_data["id_token"]:
        return extra_data["id_token"]["groups"]

    return []


def apply(user, extra_data):
    groups = extract_groups(extra_data)
    logger.warning("FIRE: user=%s groups=%s", user.username, groups)

    is_admin = "dronesim-admins" in groups

    if user.is_superuser != is_admin or user.is_staff != is_admin:
        user.is_superuser = is_admin
        user.is_staff = is_admin
        user.save(update_fields=["is_superuser", "is_staff"])
        logger.warning("UPDATED: superuser=%s", is_admin)


@receiver(social_account_added)
def on_added(sender, request, sociallogin, **kwargs):
    apply(sociallogin.user, sociallogin.account.extra_data)


@receiver(social_account_updated)
def on_updated(sender, request, sociallogin, **kwargs):
    apply(sociallogin.user, sociallogin.account.extra_data)
