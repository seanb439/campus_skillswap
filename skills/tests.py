from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import SessionRequest, Skill


class SkillModelTests(TestCase):
	def test_category_is_normalized_on_save(self):
		owner = User.objects.create_user(username='modelowner', password='Pass12345!')
		skill = Skill.objects.create(
			owner=owner,
			title='Physics Help',
			description='I can help with first-year physics.',
			category='  math   tutoring  ',
			is_free=True,
			contact_preference='email',
			availability_status='available',
		)

		self.assertEqual(skill.category, 'Math Tutoring')

	def test_paid_skill_requires_positive_price(self):
		skill = Skill(
			owner=User.objects.create_user(username='paidowner', password='Pass12345!'),
			title='Programming Mentor',
			description='Mentoring session.',
			category='Coding',
			is_free=False,
			price=None,
			contact_preference='email',
			availability_status='available',
		)

		with self.assertRaises(ValidationError):
			skill.full_clean()


class SkillPermissionViewTests(TestCase):
	def setUp(self):
		self.owner = User.objects.create_user(username='owner', password='Pass12345!')
		self.other_user = User.objects.create_user(username='other', password='Pass12345!')
		self.skill = Skill.objects.create(
			owner=self.owner,
			title='Chemistry Tutor',
			description='Organic chemistry support.',
			category='Tutoring',
			is_free=False,
			price=25,
			contact_preference='email',
			availability_status='available',
		)

	def test_anonymous_user_cannot_create_skill(self):
		response = self.client.get(reverse('skill_create'))

		self.assertEqual(response.status_code, 302)
		self.assertIn('/accounts/login/', response.url)

	def test_logged_in_user_can_create_skill_and_becomes_owner(self):
		self.client.login(username='other', password='Pass12345!')
		payload = {
			'title': 'Piano Lessons',
			'description': 'Beginner piano coaching.',
			'category': 'music',
			'is_free': 'on',
			'price': '',
			'contact_preference': 'email',
			'availability_status': 'available',
		}

		response = self.client.post(reverse('skill_create'), payload)

		self.assertEqual(response.status_code, 302)
		new_skill = Skill.objects.get(title='Piano Lessons')
		self.assertEqual(new_skill.owner, self.other_user)

	def test_owner_can_update_own_skill(self):
		self.client.login(username='owner', password='Pass12345!')
		payload = {
			'title': 'Chemistry Tutor Updated',
			'description': 'Updated description.',
			'category': 'Tutoring',
			'is_free': '',
			'price': '30.00',
			'contact_preference': 'email',
			'availability_status': 'busy',
		}

		response = self.client.post(reverse('skill_update', args=[self.skill.pk]), payload)

		self.assertEqual(response.status_code, 302)
		self.skill.refresh_from_db()
		self.assertEqual(self.skill.title, 'Chemistry Tutor Updated')
		self.assertEqual(self.skill.price, 30)

	def test_non_owner_cannot_update_someone_elses_skill(self):
		self.client.login(username='other', password='Pass12345!')
		payload = {
			'title': 'Malicious Update',
			'description': 'Trying to edit another user skill.',
			'category': 'Tutoring',
			'is_free': '',
			'price': '50.00',
			'contact_preference': 'email',
			'availability_status': 'available',
		}

		response = self.client.post(reverse('skill_update', args=[self.skill.pk]), payload)

		self.assertEqual(response.status_code, 404)
		self.skill.refresh_from_db()
		self.assertEqual(self.skill.title, 'Chemistry Tutor')

	def test_owner_can_delete_own_skill(self):
		self.client.login(username='owner', password='Pass12345!')
		response = self.client.post(reverse('skill_delete', args=[self.skill.pk]))

		self.assertEqual(response.status_code, 302)
		self.assertFalse(Skill.objects.filter(pk=self.skill.pk).exists())

	def test_non_owner_cannot_delete_someone_elses_skill(self):
		self.client.login(username='other', password='Pass12345!')
		response = self.client.post(reverse('skill_delete', args=[self.skill.pk]))

		self.assertEqual(response.status_code, 404)
		self.assertTrue(Skill.objects.filter(pk=self.skill.pk).exists())

	def test_contact_details_hidden_from_anonymous_users(self):
		response = self.client.get(reverse('skill_detail', args=[self.skill.pk]))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Login to view contact details.')
		self.assertNotContains(response, 'Contact Preference:</strong> Email')

	def test_contact_details_visible_to_logged_in_users(self):
		self.client.login(username='other', password='Pass12345!')
		response = self.client.get(reverse('skill_detail', args=[self.skill.pk]))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Contact Preference:</strong> Email')
		self.assertNotContains(response, 'Login to view contact details.')

	def test_logged_in_user_can_create_review(self):
		self.client.login(username='other', password='Pass12345!')
		payload = {
			'rating': 5,
			'review_text': 'Excellent help and very clear explanations.',
		}

		response = self.client.post(reverse('skill_detail', args=[self.skill.pk]), payload)

		self.assertEqual(response.status_code, 302)
		review = self.skill.reviews.get()
		self.assertEqual(review.reviewer, self.other_user)
		self.assertEqual(review.rating, 5)
		self.assertEqual(review.review_text, 'Excellent help and very clear explanations.')

	def test_owner_cannot_review_own_skill(self):
		self.client.login(username='owner', password='Pass12345!')
		payload = {
			'rating': 4,
			'review_text': 'Trying to review my own skill.',
		}

		response = self.client.post(reverse('skill_detail', args=[self.skill.pk]), payload)

		self.assertEqual(response.status_code, 302)
		self.assertFalse(self.skill.reviews.exists())

	def test_logged_in_user_can_request_session(self):
		self.client.login(username='other', password='Pass12345!')
		payload = {
			'requested_date': '2026-05-01',
			'requested_time': '14:30',
			'message': 'I would like a one-hour session.',
		}

		response = self.client.post(reverse('request_session', args=[self.skill.pk]), payload)

		self.assertEqual(response.status_code, 302)
		request_obj = SessionRequest.objects.get(skill=self.skill)
		self.assertEqual(request_obj.requester, self.other_user)
		self.assertEqual(str(request_obj.requested_date), '2026-05-01')
		self.assertEqual(str(request_obj.requested_time), '14:30:00')
		self.assertEqual(request_obj.message, 'I would like a one-hour session.')
		self.assertEqual(request_obj.status, 'pending')

	def test_owner_cannot_request_own_session(self):
		self.client.login(username='owner', password='Pass12345!')
		payload = {
			'requested_date': '2026-05-01',
			'requested_time': '14:30',
			'message': 'I should not be able to request my own skill.',
		}

		response = self.client.post(reverse('request_session', args=[self.skill.pk]), payload)

		self.assertEqual(response.status_code, 302)
		self.assertFalse(SessionRequest.objects.exists())

	def test_dashboard_shows_incoming_session_requests_for_owner(self):
		SessionRequest.objects.create(
			skill=self.skill,
			requester=self.other_user,
			requested_date='2026-05-01',
			requested_time='14:30',
			message='Please accept my request.',
		)
		self.client.login(username='owner', password='Pass12345!')

		response = self.client.get(reverse('dashboard'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Incoming Session Requests')
		self.assertContains(response, 'Please accept my request.')
		self.assertContains(response, 'other')

	def test_owner_can_accept_incoming_session_request(self):
		request_obj = SessionRequest.objects.create(
			skill=self.skill,
			requester=self.other_user,
			requested_date='2026-05-01',
			requested_time='14:30',
			message='Please accept my request.',
		)
		self.client.login(username='owner', password='Pass12345!')

		response = self.client.post(reverse('accept_session_request', args=[request_obj.pk]))

		self.assertEqual(response.status_code, 302)
		request_obj.refresh_from_db()
		self.assertEqual(request_obj.status, 'accepted')

	def test_non_owner_cannot_accept_incoming_session_request(self):
		request_obj = SessionRequest.objects.create(
			skill=self.skill,
			requester=self.other_user,
			requested_date='2026-05-01',
			requested_time='14:30',
			message='Please accept my request.',
		)
		self.client.login(username='other', password='Pass12345!')

		response = self.client.post(reverse('accept_session_request', args=[request_obj.pk]))

		self.assertEqual(response.status_code, 404)
		request_obj.refresh_from_db()
		self.assertEqual(request_obj.status, 'pending')

	def test_owner_can_decline_incoming_session_request(self):
		request_obj = SessionRequest.objects.create(
			skill=self.skill,
			requester=self.other_user,
			requested_date='2026-05-01',
			requested_time='14:30',
			message='Please decline or accept.',
		)
		self.client.login(username='owner', password='Pass12345!')

		response = self.client.post(reverse('decline_session_request', args=[request_obj.pk]))

		self.assertEqual(response.status_code, 302)
		request_obj.refresh_from_db()
		self.assertEqual(request_obj.status, 'declined')

	def test_non_owner_cannot_decline_incoming_session_request(self):
		request_obj = SessionRequest.objects.create(
			skill=self.skill,
			requester=self.other_user,
			requested_date='2026-05-01',
			requested_time='14:30',
			message='Please decline or accept.',
		)
		self.client.login(username='other', password='Pass12345!')

		response = self.client.post(reverse('decline_session_request', args=[request_obj.pk]))

		self.assertEqual(response.status_code, 404)
		request_obj.refresh_from_db()
		self.assertEqual(request_obj.status, 'pending')
