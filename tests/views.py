from django.contrib import messages
from django.db.models import Max
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from .models import Test, Question, Answer, Subject, StudGroup, TestActivationSettings, TestAttempt
from .forms import TestForm, TestActivationSettingsForm


@user_passes_test(lambda u: u.is_superuser or u.is_teacher, login_url='accounts:login_view')
def create_subject(request):
    if request.method == 'POST':
        subject_name = request.POST.get('subject_name')
        author_name = request.user
        try:
            subject = Subject.objects.create(name=subject_name, author=author_name)
            messages.success(request, 'Предмет успешно добавлен.')
        except Exception as e:
            messages.error(request, 'Ошибка добавления предмета: {}'.format(str(e)))

        return redirect('accounts:teacher_home')  # Перенаправляем на нужную страницу после сохранения предмета

    return render(request, 'tests/create_subject.html')


@user_passes_test(lambda u: u.is_superuser or u.is_teacher, login_url='accounts:login_view')
def create_test(request):
    subjects = Subject.objects.all()
    groups = StudGroup.objects.all()

    if request.method == 'POST':
        # Получаем данные из формы
        test_name = request.POST.get('test_name')
        description = request.POST.get('description')
        subject_id = request.POST.get('subject')
        group_id = request.POST.get('group')
        author = request.user

        # Создаем тест
        test = Test.objects.create(name=test_name, description=description, subject_id=subject_id, group_id=group_id, author=author)

        # Получаем данные о вопросах и ответах
        questions = request.POST.getlist('question[]')
        answer_types = request.POST.getlist('answer_type[]')
        points = request.POST.getlist('points[]')
        images = request.FILES.getlist('image[]')

        # Создаем вопросы и ответы
        for i in range(len(questions)):
            question = Question.objects.create(text=questions[i], answer_type=answer_types[i], test=test, points=points[i])

            # Получаем данные о ответах
            answer_texts = request.POST.getlist(f'answer[{i+1}][]')
            correct_answers = request.POST.getlist(f'correct_answer[{i+1}][]')

            # Создаем ответы
            for j, answer_text in enumerate(answer_texts):
                is_correct = str(j) in correct_answers
                Answer.objects.create(text=answer_text, is_correct=is_correct, question=question)

    return render(request, 'tests/create_test.html', {'subjects': subjects, 'groups': groups})


@login_required
def view_tests(request):
    tests = Test.objects.all()
    activation_settings = TestActivationSettings.objects.filter(test__in=tests)
    now = timezone.now()

    for test in tests:
        test.activation = None
        for activation in activation_settings:
            if activation.test == test:
                test.activation = activation
                break

    return render(request, 'tests/test_list.html', {'tests': tests, 'now': now})


@user_passes_test(lambda u: u.is_superuser or u.is_teacher, login_url='accounts:login_view')
def edit_test(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    if request.method == 'POST':
        form = TestForm(request.POST, instance=test)
        if form.is_valid():
            form.save()

            deleted_questions = []
            for key in request.POST:
                if key.startswith('deleted_question_'):
                    question_id = key.split('_')[-1]
                    deleted_questions.append(question_id)

            Question.objects.filter(id__in=deleted_questions).delete()

            # Обновляем вопросы и ответы
            questions = test.get_questions()
            for question in questions:
                question_text = request.POST.get(f'question_{question.id}')
                answer_type = request.POST.get(f'answer_type_{question.id}')
                points = request.POST.get(f'points_{question.id}')
                image = request.FILES.get(f'image_{question.id}')

                question.text = question_text
                question.answer_type = answer_type
                question.points = points
                if image:
                    question.image = image
                question.save()

                answers = question.get_answers()
                for answer in answers:
                    answer_text = request.POST.get(f'answer_{question.id}_{answer.id}')
                    is_correct = request.POST.get(f'correct_{question.id}_{answer.id}') == 'on'

                    answer.text = answer_text
                    answer.is_correct = is_correct
                    answer.save()

            return redirect('tests:test_list')
    else:
        form = TestForm(instance=test)
    return render(request, 'tests/edit_test.html', {'form': form, 'test': test})


@user_passes_test(lambda u: u.is_superuser or u.is_teacher, login_url='accounts:login_view')
def delete_test(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    test.delete()
    return redirect('tests:test_list')


@user_passes_test(lambda u: u.is_superuser or u.is_teacher, login_url='accounts:login_view')
def activate_test(request, test_id):
    test = Test.objects.get(id=test_id)

    if request.method == 'POST':
        activation_form = TestActivationSettingsForm(request.POST)
        if activation_form.is_valid():
            activation_settings = activation_form.save(commit=False)
            activation_settings.test = test
            activation_settings.save()
            return redirect('tests:test_list')
    else:
        activation_form = TestActivationSettingsForm()

    context = {
        'test': test,
        'activation_form': activation_form
    }

    return render(request, 'tests/test_activation.html', context)


@login_required
def take_test(request, test_id):
    test_activation = TestActivationSettings.objects.filter(test_id=test_id).first()

    if not test_activation or not test_activation.is_active():
        messages.error(request, 'Тест в данный момент недоступен.')
        return redirect('tests:test_list')

    if test_activation.num_attempts <= TestAttempt.objects.filter(test=test_activation.test, user=request.user).count():
        messages.error(request, 'Превышено максимальное количество попыток для прохождения теста.')
        return redirect('tests:test_list')

    if test_activation.has_time_limit():
        current_time = timezone.now()
        if current_time > test_activation.expiration_datetime:
            messages.error(request, 'Время для прохождения теста истекло.')
            return redirect('tests:test_list')

    test = test_activation.test
    questions = test.get_questions()

    if test_activation.shuffle_questions:
        questions = list(questions.order_by('?'))

    if request.method == 'POST':
        # Обработка отправленных ответов студента
        score = 0  # Инициализация счетчика баллов
        right_q_count = 0  # Инициализация счетчика правильных ответов на вопрос

        for question in questions:
            # Получение отправленного ответа студента
            answer_key = f'answer_{question.id}'
            submitted_answers = request.POST.getlist(answer_key)

            if submitted_answers:
                # Проверка верности ответа
                if question.answer_type == 'Письменный':
                    correct_answer = question.get_answers().filter(is_correct=True).first()
                    submitted_answer = submitted_answers[0]

                    if submitted_answer == correct_answer.text:
                        score += question.points
                        right_q_count += 1
                else:
                    # Получение верных ответов на вопрос
                    correct_answers = question.get_answers().filter(is_correct=True)

                    if question.answer_type == 'Единственный верный':
                        # Проверка ответа на вопрос с единственным верным вариантом
                        submitted_answer = submitted_answers[0]
                        if submitted_answer == str(correct_answers.first().id):
                            score += question.points
                            right_q_count += 1
                    elif question.answer_type == 'Несколько верных':
                        # Проверка ответа на вопрос с несколькими верными вариантами
                        submitted_answer_ids = set(submitted_answers)
                        correct_answer_ids = set(str(answer.id) for answer in correct_answers)

                        if submitted_answer_ids == correct_answer_ids:
                            score += question.points
                            right_q_count += 1

        # Создание и сохранение результатов попытки
        test_attempt = TestAttempt(user=request.user, test=test, score=score, correct_answers=right_q_count)
        test_attempt.save()

        # Перенаправление на страницу с результатами
        return redirect('tests:test_results', attempt_id=test_attempt.id)

    return render(request, 'tests/take_test.html', {'test': test, 'questions': questions, 'test_activation': test_activation})


@login_required
def test_results(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id)
    num = TestAttempt.objects.filter(test=attempt.test, user=request.user).count()
    procent = attempt.correct_answers / attempt.test.get_questions().count() * 100
    return render(request, 'tests/test_results.html',
                  {
                      'attempt': attempt,
                      'num': num,
                      'procent': procent,
                  })


@login_required
def all_results(request):
    # Получение лучшей попытки каждого теста с максимальным количеством баллов
    best_attempts = TestAttempt.objects.filter(user=request.user).values('test').annotate(
        max_score=Max('score')
    )

    test_attempts = []
    for attempt in best_attempts:
        best_attempt = TestAttempt.objects.filter(
            user=request.user, test=attempt['test'], score=attempt['max_score']
        ).latest('timestamp')
        test_attempts.append(best_attempt)

    return render(request, 'tests/all_results.html', {'test_attempts': test_attempts})


@user_passes_test(lambda u: u.is_superuser or u.is_teacher, login_url='accounts:login_view')
def view_statistics(request):
    subjects = None
    tests = None

    if request.user.is_superuser:
        subjects = Subject.objects.all()
        tests = Test.objects.all()
    if request.user.is_teacher:
        subjects = Subject.objects.filter(author=request.user)
        tests = Test.objects.filter(author=request.user)
    group = StudGroup.objects.all()
    student_results = None

    if request.method == 'POST':
        subject_id = request.POST.get('subject_id')
        test_id = request.POST.get('test_id')
        group_id = request.POST.get('group_id')

        if group_id:
            group = StudGroup.objects.get(id=group_id)
            test_attempts = TestAttempt.objects.filter(test__group=group)

            if subject_id and test_id:
                test_attempts = test_attempts.filter(test__id=test_id)

            student_results = {}
            for attempt in test_attempts:
                if attempt.user.id not in student_results or attempt.score > student_results[attempt.user.id]['best_score']:
                    student_results[attempt.user.id] = {
                        'user': attempt.user,
                        'best_score': attempt.score,
                    }

        if subject_id:
            subject = Subject.objects.get(id=subject_id)
            tests = Test.objects.filter(subject=subject)

    context = {
        'subjects': subjects,
        'tests': tests,
        'groups': StudGroup.objects.all(),
        'group': group,
        'student_results': student_results.values() if student_results else None,
    }

    return render(request, 'tests/statistics.html', context)
