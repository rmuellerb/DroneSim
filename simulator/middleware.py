from allauth.socialaccount.models import SocialAccount

class EnsureRolesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.session.get("roles_synced", False):
            try:
                sa = SocialAccount.objects.get(user=request.user, provider="openid_connect")
                extra = sa.extra_data or {}
                groups = (extra.get("userinfo", {}) or {}).get("groups") or (extra.get("id_token", {}) or {}).get("groups") or []
                is_admin = "dronesim-admins" in groups

                if request.user.is_superuser != is_admin or request.user.is_staff != is_admin:
                    request.user.is_superuser = is_admin
                    request.user.is_staff = is_admin
                    request.user.save(update_fields=["is_superuser", "is_staff"])
            except SocialAccount.DoesNotExist:
                pass

            request.session["roles_synced"] = True

        return self.get_response(request)
