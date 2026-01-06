from django.urls import path
from .views import AttemptStartView, AttemptEventView, AttemptFinishView, AttemptListView, AttemptDetailView

urlpatterns = [
    path('attempts/start', AttemptStartView.as_view(), name='attempt_start'),
    path('attempts/<int:attempt_id>/event', AttemptEventView.as_view(), name='attempt_event'),
    path('attempts/<int:attempt_id>/finish', AttemptFinishView.as_view(), name='attempt_finish'),
    path('attempts/me', AttemptListView.as_view(), name='attempt_list'),
    path('attempts/<int:pk>', AttemptDetailView.as_view(), name='attempt_detail'),
]
