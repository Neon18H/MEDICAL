from django.urls import path
from .views import AdminProcedureView, AnalyticsView, ExportCsvView

urlpatterns = [
    path('procedures', AdminProcedureView.as_view(), name='admin_procedures'),
    path('analytics', AnalyticsView.as_view(), name='admin_analytics'),
    path('export/csv', ExportCsvView.as_view(), name='admin_export_csv'),
]
