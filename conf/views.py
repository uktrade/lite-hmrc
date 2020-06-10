import datetime

from background_task.models import Task
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.status import HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR
from rest_framework.views import APIView

from mail.tasks import TASK_QUEUE


class HealthCheck(APIView):
    def get(self, request):
        task = Task.objects.get(queue=TASK_QUEUE)
        if task.run_at + datetime.timedelta(seconds=task.repeat) < timezone.now():
            return JsonResponse(data={"status": f"{TASK_QUEUE} is unavailable"}, status=HTTP_500_INTERNAL_SERVER_ERROR)

        return JsonResponse(data={"status": "available"}, status=HTTP_200_OK)
