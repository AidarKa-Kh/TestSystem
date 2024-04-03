from django import forms
from .models import Test, Question, Answer, TestActivationSettings


class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ['name', 'description', 'subject', 'group']


class QuestionForm(forms.ModelForm):
    answers = forms.ModelMultipleChoiceField(queryset=Answer.objects.none(), widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = Question
        fields = ['text', 'image', 'answer_type', 'points']


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text', 'is_correct']


class TestActivationSettingsForm(forms.ModelForm):
    class Meta:
        model = TestActivationSettings
        fields = ['num_attempts', 'shuffle_questions', 'shuffle_answers', 'time_limit', 'activation_datetime', 'expiration_datetime']
        widgets = {
            'activation_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'expiration_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
