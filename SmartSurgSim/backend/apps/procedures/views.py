from rest_framework import generics, permissions
from .models import Procedure
from .serializers import ProcedureSerializer


class ProcedureListView(generics.ListAPIView):
    queryset = Procedure.objects.all()
    serializer_class = ProcedureSerializer
    permission_classes = [permissions.IsAuthenticated]


class ProcedureDetailView(generics.RetrieveAPIView):
    queryset = Procedure.objects.all()
    serializer_class = ProcedureSerializer
    permission_classes = [permissions.IsAuthenticated]
