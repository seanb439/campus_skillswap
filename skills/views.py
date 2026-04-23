from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ReviewForm, SessionRequestForm, SkillForm, UserRegistrationForm
from .models import Review, SessionRequest, Skill


def register_view(request):
	if request.user.is_authenticated:
		return redirect('skill_list')

	if request.method == 'POST':
		form = UserRegistrationForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			messages.success(request, 'Welcome! Your account was created successfully.')
			return redirect('dashboard')
	else:
		form = UserRegistrationForm()

	return render(request, 'registration/register.html', {'form': form})


def skill_list(request):
	skills = Skill.objects.select_related('owner').all()
	query = request.GET.get('q', '').strip()
	selected_category = request.GET.get('category', '').strip()

	if query:
		skills = skills.filter(title__icontains=query) | skills.filter(description__icontains=query)

	if selected_category:
		skills = skills.filter(category__iexact=selected_category)

	skills = skills.distinct()
	paginator = Paginator(skills, 9)
	page_obj = paginator.get_page(request.GET.get('page'))
	page_numbers = list(paginator.page_range)

	# Show available categories for filter dropdown.
	raw_categories = Skill.objects.values_list('category', flat=True)
	normalized_map = {}
	for raw_category in raw_categories:
		normalized = Skill.normalize_category_value(raw_category)
		if normalized:
			normalized_map[normalized.lower()] = normalized
	categories = []
	for category_name in sorted(normalized_map.values()):
		categories.append(
			{
				'name': category_name,
				'is_selected': category_name.lower() == selected_category.lower(),
			}
		)

	query_params = request.GET.copy()
	query_params.pop('page', None)

	context = {
		'skills': page_obj.object_list,
		'page_obj': page_obj,
		'page_numbers': page_numbers,
		'query': query,
		'selected_category': selected_category,
		'categories': categories,
		'query_string': query_params.urlencode(),
	}
	return render(request, 'skills/skill_list.html', context)


def skill_detail(request, pk):
	skill = get_object_or_404(Skill.objects.select_related('owner'), pk=pk)
	reviews = skill.reviews.select_related('reviewer').all()
	session_requests = skill.session_requests.select_related('requester').all()
	average_rating = reviews.aggregate(average=Avg('rating'))['average']
	user_review = None
	review_form = None
	session_request_form = None
	can_review = False
	can_request_session = request.user.is_authenticated and request.user != skill.owner
	has_completed_session = False

	if request.user.is_authenticated:
		user_review = reviews.filter(reviewer=request.user).first()
		has_completed_session = SessionRequest.objects.filter(
			skill=skill,
			requester=request.user,
			status='completed',
		).exists()
		can_review = request.user != skill.owner and has_completed_session and user_review is None

	if request.method == 'POST':
		if request.user == skill.owner:
			messages.error(request, 'You cannot review your own skill.')
			return redirect('skill_detail', pk=skill.pk)

		if user_review is not None:
			messages.error(request, 'You have already reviewed this skill.')
			return redirect('skill_detail', pk=skill.pk)

		if not has_completed_session:
			messages.error(request, 'You can leave a review only after completing a session for this skill.')
			return redirect('skill_detail', pk=skill.pk)

		review_form = ReviewForm(request.POST)
		if review_form.is_valid():
			review = review_form.save(commit=False)
			review.skill = skill
			review.reviewer = request.user
			review.save()
			messages.success(request, 'Your review has been saved.')
			return redirect('skill_detail', pk=skill.pk)
	else:
		if can_review:
			review_form = ReviewForm(instance=user_review)
		if can_request_session:
			session_request_form = SessionRequestForm()

	context = {
		'skill': skill,
		'reviews': reviews,
		'session_requests': session_requests,
		'average_rating': average_rating,
		'review_count': reviews.count(),
		'review_form': review_form,
		'session_request_form': session_request_form,
		'can_review': can_review,
		'can_request_session': can_request_session,
		'has_completed_session': has_completed_session,
		'user_review': user_review,
	}
	return render(request, 'skills/skill_detail.html', context)


@login_required
def request_session(request, pk):
	skill = get_object_or_404(Skill, pk=pk)

	if skill.owner == request.user:
		messages.error(request, 'You cannot request a session for your own skill.')
		return redirect('skill_detail', pk=skill.pk)

	if request.method == 'POST':
		form = SessionRequestForm(request.POST)
		if form.is_valid():
			session_request = form.save(commit=False)
			session_request.skill = skill
			session_request.requester = request.user
			session_request.save()
			messages.success(request, 'Your session request has been sent.')
			return redirect('skill_detail', pk=skill.pk)
	else:
		form = SessionRequestForm()

	return render(request, 'skills/session_request_form.html', {'form': form, 'skill': skill})


@login_required
def dashboard(request):
	# Show only the logged-in user's posts.
	user_skills = Skill.objects.filter(owner=request.user)
	incoming_requests = (
		SessionRequest.objects.select_related('skill', 'requester')
		.filter(skill__owner=request.user)
		.order_by('-created_at')
	)
	completed_sessions = (
		SessionRequest.objects.select_related('skill', 'skill__owner')
		.filter(requester=request.user, status='completed')
		.order_by('-updated_at')
	)
	return render(
		request,
		'skills/dashboard.html',
		{
			'skills': user_skills,
			'incoming_requests': incoming_requests,
			'completed_sessions': completed_sessions,
		},
	)


@login_required
def accept_session_request(request, pk):
	session_request = get_object_or_404(SessionRequest, pk=pk, skill__owner=request.user)

	if request.method != 'POST':
		return redirect('dashboard')

	if session_request.status == 'accepted':
		messages.info(request, 'This request has already been accepted.')
		return redirect('dashboard')

	session_request.status = 'accepted'
	session_request.save(update_fields=['status', 'updated_at'])
	messages.success(request, 'Session request accepted.')
	return redirect('dashboard')


@login_required
def complete_session_request(request, pk):
	session_request = get_object_or_404(SessionRequest, pk=pk, skill__owner=request.user)

	if request.method != 'POST':
		return redirect('dashboard')

	if session_request.status == 'completed':
		messages.info(request, 'This request has already been marked as completed.')
		return redirect('dashboard')

	if session_request.status != 'accepted':
		messages.error(request, 'Only accepted requests can be marked as completed.')
		return redirect('dashboard')

	session_request.status = 'completed'
	session_request.save(update_fields=['status', 'updated_at'])
	messages.success(request, 'Session request marked as completed.')
	return redirect('dashboard')


@login_required
def decline_session_request(request, pk):
	session_request = get_object_or_404(SessionRequest, pk=pk, skill__owner=request.user)

	if request.method != 'POST':
		return redirect('dashboard')

	if session_request.status == 'declined':
		messages.info(request, 'This request has already been declined.')
		return redirect('dashboard')

	session_request.status = 'declined'
	session_request.save(update_fields=['status', 'updated_at'])
	messages.success(request, 'Session request declined.')
	return redirect('dashboard')


@login_required
def skill_create(request):
	if request.method == 'POST':
		form = SkillForm(request.POST)
		if form.is_valid():
			skill = form.save(commit=False)
			skill.owner = request.user
			skill.save()
			messages.success(request, 'Skill post created.')
			return redirect('dashboard')
	else:
		form = SkillForm()

	return render(request, 'skills/skill_form.html', {'form': form, 'page_title': 'Create Skill'})


@login_required
def skill_update(request, pk):
	skill = get_object_or_404(Skill, pk=pk, owner=request.user)

	if request.method == 'POST':
		form = SkillForm(request.POST, instance=skill)
		if form.is_valid():
			form.save()
			messages.success(request, 'Skill post updated.')
			return redirect('dashboard')
	else:
		form = SkillForm(instance=skill)

	return render(request, 'skills/skill_form.html', {'form': form, 'page_title': 'Edit Skill'})


@login_required
def skill_delete(request, pk):
	skill = get_object_or_404(Skill, pk=pk, owner=request.user)

	if request.method == 'POST':
		skill.delete()
		messages.success(request, 'Skill post deleted.')
		return redirect('dashboard')

	return render(request, 'skills/skill_confirm_delete.html', {'skill': skill})
