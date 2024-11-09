from rest_framework import status, generics
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsCharityOwner, IsBenefactor
from charities.models import Task
from charities.serializers import TaskSerializer, CharitySerializer, BenefactorSerializer
from .models import *


class BenefactorRegistration(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        benefactor_serializer = BenefactorSerializer(data=request.data)
        if benefactor_serializer.is_valid():
            benefactor_serializer.save(user=request.user)
            return Response(benefactor_serializer.data, status=status.HTTP_201_CREATED)

        return Response({'message': benefactor_serializer.errors})


class CharityRegistration(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        charity_serializer = CharitySerializer(data=request.data)
        if charity_serializer.is_valid():
            charity_serializer.save(user=request.user)
            return Response(charity_serializer.data, status=status.HTTP_201_CREATED)

        return Response({'message': charity_serializer.errors})


class Tasks(generics.ListCreateAPIView):
    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.all_related_tasks_to_user(self.request.user)

    def post(self, request, *args, **kwargs):
        data = {
            **request.data,
            "charity_id": request.user.charity.id
        }
        serializer = self.serializer_class(data = data)
        serializer.is_valid(raise_exception = True)
        serializer.save()
        return Response(serializer.data, status = status.HTTP_201_CREATED)

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            self.permission_classes = [IsAuthenticated, ]
        else:
            self.permission_classes = [IsCharityOwner, ]

        return [permission() for permission in self.permission_classes]

    def filter_queryset(self, queryset):
        filter_lookups = {}
        for name, value in Task.filtering_lookups:
            param = self.request.GET.get(value)
            if param:
                filter_lookups[name] = param
        exclude_lookups = {}
        for name, value in Task.excluding_lookups:
            param = self.request.GET.get(value)
            if param:
                exclude_lookups[name] = param

        return queryset.filter(**filter_lookups).exclude(**exclude_lookups)


class TaskRequest(APIView):
    permission_classes = [IsBenefactor]

    def get(self , request , task_id , *args, **kwargs):
        if not task_id:
            return Response(data = {}, status=status.HTTP_404_NOT_FOUND)

        task = get_object_or_404(Task, id = task_id)

        if task.state != Task.TaskStatus.PENDING:
            return Response({'detail': 'This task is not pending.'} , status = status.HTTP_404_NOT_FOUND)

        benefactor = get_object_or_404(Benefactor, user = request.user)
        if not benefactor:
            return Response(data = {}, status = status.HTTP_403_FORBIDDEN)
        else:
            task.assigned_benefactor = benefactor
            task.state = Task.TaskStatus.WAITING
            task.save()

        return Response({'detail': 'Request sent.'}, status=status.HTTP_200_OK)
    

class TaskResponse(APIView):
    permission_classes = [IsCharityOwner]
    
    def post(self , request , task_id , *args, **kwargs):
        response = request.data['response']
        task = get_object_or_404(Task , id = task_id)

        if response not in ['A' , 'R']:
            return Response({'detail': 'Required field ("A" for accepted / "R" for rejected)'} , status = status.HTTP_400_BAD_REQUEST )


        elif task.state != Task.TaskStatus.WAITING:
            return Response({'detail': 'This task is not waiting.'} , status = status.HTTP_404_NOT_FOUND)

        else:
            task.response_to_benefactor_request(response = response)
            return Response({'detail': 'Response sent.'} , status = status.HTTP_200_OK)


class DoneTask(APIView):
    permission_classes = [IsCharityOwner]

    def post(self , request , task_id , *args, **kwargs):
        if not task_id:
            return Response(data = {}, status=status.HTTP_404_NOT_FOUND)
        
        task = get_object_or_404(Task, id = task_id)

        if task.state != Task.TaskStatus.ASSIGNED:
            return Response({'detail': 'Task is not assigned yet.'} , status = status.HTTP_404_NOT_FOUND)

        else:
            task.state = Task.TaskStatus.DONE
            task.save()
            return Response({'detail': 'Task has been done successfully.'} , status = status.HTTP_200_OK)
        
