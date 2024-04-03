from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from OnlineTestingSys import settings


class Subject(models.Model):
    name = models.CharField('Название предмета', max_length=255)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'Предметы'

    def __str__(self):
        return self.name


class StudGroup(models.Model):
    number = models.CharField('Номер группы', max_length=255)

    class Meta:
        ordering = ('number',)
        verbose_name_plural = 'Группы'

    def __str__(self):
        return self.number


class Test(models.Model):
    name = models.CharField('Название теста', max_length=255)
    description = models.TextField('Описание теста')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    group = models.ForeignKey(StudGroup, on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def get_questions(self):
        return self.question_set.all()

    class Meta:
        ordering = ('name',)
        verbose_name_plural = 'Тесты'

    def __str__(self):
        return self.name


class Question(models.Model):
    TEXT = 'Письменный'
    SINGLE_CHOICE = 'Единственный верный'
    MULTIPLE_CHOICE = 'Несколько верных'
    ANSWER_TYPE_CHOICES = [
        (TEXT, 'Письменный'),
        (SINGLE_CHOICE, 'Единственный верный'),
        (MULTIPLE_CHOICE, 'Несколько верных'),
    ]

    text = models.TextField('Вопрос')
    image = models.ImageField(upload_to='question_images', null=True, blank=True)
    answer_type = models.CharField(max_length=20, choices=ANSWER_TYPE_CHOICES, default=TEXT)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    points = models.PositiveIntegerField(default=1)

    def get_answers(self):
        return self.answer_set.all()

    class Meta:
        order_with_respect_to = 'test'
        verbose_name_plural = 'Вопросы'

    def __str__(self):
        return self.text


class Answer(models.Model):
    text = models.TextField('Ответ')
    is_correct = models.BooleanField('Верный', default=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    class Meta:
        order_with_respect_to = 'question'
        verbose_name_plural = 'Ответы'

    def __str__(self):
        return self.text


class TestActivationSettings(models.Model):
    test = models.OneToOneField(Test, on_delete=models.CASCADE)
    num_attempts = models.PositiveIntegerField('Количество попыток')
    shuffle_questions = models.BooleanField('Перемешивать вопросы')
    shuffle_answers = models.BooleanField('Перемешивать ответы')
    time_limit = models.PositiveIntegerField('Ограничение по времени (в минутах)', null=True, blank=True,
                                             validators=[MinValueValidator(1)])
    activation_datetime = models.DateTimeField('Дата и время активации', null=True, blank=True)
    expiration_datetime = models.DateTimeField('Дата и время окончания', null=True, blank=True)

    def is_active(self):
        # Проверка, активирован ли тест в данный момент
        now = timezone.now().astimezone(timezone.utc)
        activation_datetime = self.activation_datetime.astimezone(timezone.utc)
        expiration_datetime = self.expiration_datetime.astimezone(timezone.utc)
        return activation_datetime <= now <= expiration_datetime

    def has_time_limit(self):
        return self.time_limit is not None

    class Meta:
        verbose_name_plural = 'Доступ к тесту'

    def __str__(self):
        return self.test.name


class TestAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    score = models.IntegerField('Баллы', default=0)
    timestamp = models.DateTimeField('Время попытки', auto_now_add=True)
    time_taken = models.IntegerField('Использованное время (в минутах)', default=0)
    correct_answers = models.PositiveIntegerField('Количество правильных ответов')

    class Meta:
        verbose_name_plural = 'Попытки тестов'

    def __str__(self):
        return f'{self.user.get_username() if hasattr(self.user, "get_username") else self.user.username} - {self.test.name}'
