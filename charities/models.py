from django.db import models
from django.utils.translation import gettext_lazy as _

from accounts.models import User
from .validators import reg_number_validator


class Benefactor(models.Model):
    experience_choice = (
        (0 , _('Beginner')),
        (1 , _('Intermediate')),
        (2 , _('Expert'))
    )
    user = models.OneToOneField(User , on_delete = models.CASCADE , verbose_name=_('user')) 
    experience = models.SmallIntegerField(choices = experience_choice , default = 0 , verbose_name=_('experience'))
    free_time_per_week = models.PositiveSmallIntegerField(default = 0 , verbose_name=_('free time per week'))

    class Meta:
        verbose_name = _('Benefactor')
        verbose_name_plural = _('Benefactors')

    def __str__(self):
        return self.user.username


class Charity(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE , verbose_name=_('user'))
    name = models.CharField(max_length=50 , verbose_name=_('name'))
    reg_number = models.CharField(max_length=10, validators=[reg_number_validator] , verbose_name=_('reg_number'))

    class Meta:
        verbose_name = _('Charity')
        verbose_name_plural = _('Charities')

    def __str__(self):
        return self.name


class TaskManager(models.Manager):
    def related_tasks_to_charity(self, user):
        if not user.is_charity:
            empty_queryset = Task.objects.none()
            return empty_queryset

        charity = user.charity
        return self.filter(charity=charity)

    def related_tasks_to_benefactor(self, user):
        if not user.is_benefactor:
            empty_queryset = Task.objects.none()
            return empty_queryset

        benefactor = user.benefactor
        return self.filter(assigned_benefactor=benefactor)

    def all_related_tasks_to_user(self, user):
        benefactor_tasks = self.related_tasks_to_benefactor(user)
        charity_tasks = self.related_tasks_to_charity(user)
        pending_tasks = self.filter(state=Task.TaskStatus.PENDING)
        return benefactor_tasks | charity_tasks | pending_tasks


class Task(models.Model):
    class TaskStatus(models.TextChoices):
        PENDING = 'P', _('Pending')
        WAITING = 'W', _('Waiting')
        ASSIGNED = 'A', _('Assigned')
        DONE = 'D', _('Done')

    title = models.CharField(max_length=60 , verbose_name=_('title'))
    state = models.CharField(max_length=1 , default=TaskStatus.PENDING , choices=TaskStatus.choices , verbose_name=_('state'))
    charity = models.ForeignKey(Charity, on_delete=models.CASCADE , verbose_name=_('charity'))
    description = models.TextField(blank=True , verbose_name=_('description'))
    assigned_benefactor = models.ForeignKey(Benefactor , on_delete=models.SET_NULL , null=True , verbose_name=_('assigned_benefactor'))
    date = models.DateField(null=True, blank=True , verbose_name=_('date'))
    age_limit_from = models.IntegerField(null=True, blank=True , verbose_name=_('age limit from'))
    age_limit_to = models.IntegerField(null=True, blank=True , verbose_name=_('age limit to'))
    gender_limit = models.CharField(max_length=2 , choices=User.Gender.choices , default=User.Gender.UNSET , verbose_name=_('gender'))
    objects = TaskManager()

    class Meta:
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')


    def __str__(self):
        return self.title

    filtering_lookups = [
        ('title__icontains', 'title',),
        ('charity__name__icontains', 'charity'),
        ('description__icontains', 'description'),
        ('gender_limit__icontains', 'gender'),
    ]

    excluding_lookups = [
        ('age_limit_from__gte', 'age'),  # Exclude greater ages
        ('age_limit_to__lte', 'age'),  # Exclude lower ages
    ]

    @classmethod
    def filter_related_tasks_to_charity_user(cls, user):
        is_charity = user.is_charity
        if not is_charity:
            return []

        return cls.objects.filter(charity=user.charity)

    @classmethod
    def filter_related_tasks_to_benefactor_user(cls, user):
        is_benefactor = user.is_benefactor
        if not is_benefactor:
            return []

        return cls.objects.filter(assigned_benefactor=user.benefactor)

    @classmethod
    def filter_related_tasks_to_user(cls, user):
        charity_tasks = cls.filter_related_tasks_to_charity_user(user)
        benefactor_tasks = cls.filter_related_tasks_to_benefactor_user(user)
        return charity_tasks.union(benefactor_tasks)

    def assign_to_benefactor(self, benefactor):
        self.state = Task.TaskStatus.WAITING
        self.assigned_benefactor = benefactor
        self.save()

    def response_to_benefactor_request(self, response):
        if response == 'A':
            self._accept_benefactor()
        else:
            self._reject_benefactor()

    def done(self):
        self.state = Task.TaskStatus.DONE
        self.save()

    def _accept_benefactor(self):
        self.state = Task.TaskStatus.ASSIGNED
        self.save()

    def _reject_benefactor(self):
        self.state = Task.TaskStatus.PENDING
        self.assigned_benefactor = None
        self.save()
