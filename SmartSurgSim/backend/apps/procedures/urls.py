from django.urls import path
from .views import ProcedureListView, ProcedureDetailView

urlpatterns = [
    path('procedures', ProcedureListView.as_view(), name='procedure_list'),
    path('procedures/<int:pk>', ProcedureDetailView.as_view(), name='procedure_detail'),
]
