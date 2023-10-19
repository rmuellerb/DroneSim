"""
URL configuration for dronesim project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import routers, permissions
from simulator import views
from rest_framework.urlpatterns import format_suffix_patterns
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Drone Simulator API",
        default_version='v1',
        description="API Documentation for the DroneSim simulator",
        terms_of_service="",
        contact=openapi.Contact(email="robin.mueller-bady@fb2.fra-uas.de"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

router = routers.DefaultRouter()
router.register(r'drones', views.DroneViewSet)
router.register(r'dronedynamics', views.DroneDynamicsViewSet)
router.register(r'dronetypes', views.DroneTypeViewSet)

urlpatterns = [
        path('', views.index, name="index"),
        path('simulator/', include('simulator.urls')),
        path('admin/', admin.site.urls),
        path('api/', include(router.urls)),
        path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
        path('accounts/', include('django.contrib.auth.urls')),
        re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
        path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

#urlpatterns = format_suffix_patterns(urlpatterns)
