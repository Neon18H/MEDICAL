from django.contrib import admin
from django.urls import path, include
from apps.accounts import views as account_views
from apps.simulation import views as simulation_views
from apps.analytics import views as analytics_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/', include('apps.procedures.urls')),
    path('api/', include('apps.simulation.urls')),
    path('api/admin/', include('apps.analytics.urls')),
    path('', account_views.landing, name='landing'),
    path('app/student/dashboard', simulation_views.student_dashboard, name='student_dashboard'),
    path('app/student/procedures/<int:procedure_id>/simulate', simulation_views.simulator_view, name='simulate'),
    path('app/student/attempts/<int:attempt_id>', simulation_views.attempt_report, name='attempt_report'),
    path('app/instructor/dashboard', analytics_views.instructor_dashboard, name='instructor_dashboard'),
    path('app/instructor/procedures', analytics_views.instructor_procedures, name='instructor_procedures'),
    path('app/instructor/procedures/<int:procedure_id>/edit', analytics_views.instructor_procedure_edit, name='instructor_procedure_edit'),
    path('app/instructor/analytics', analytics_views.instructor_analytics, name='instructor_analytics'),
]
