"""URL configuration for SmartSurgSim."""
from django.contrib import admin
from django.urls import include, path

from simulator import views as simulator_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("simulator.urls")),
    path("", simulator_views.landing, name="landing"),
    path("dashboard/", simulator_views.dashboard, name="dashboard"),
    path("simulator/<int:procedure_id>/", simulator_views.simulator_view, name="simulator"),
    path("reports/<int:attempt_id>/", simulator_views.report_view, name="report"),
    path("instructor/", simulator_views.instructor_panel, name="instructor_panel"),
    path("admin-panel/", simulator_views.admin_panel, name="admin_panel"),
]
