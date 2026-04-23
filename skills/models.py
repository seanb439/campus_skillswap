from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Skill(models.Model):
	# Clear options keep dropdowns beginner-friendly.
	CONTACT_CHOICES = [
		('email', 'Email'),
		('phone', 'Phone'),
		('in_app', 'In-App Message'),
	]

	AVAILABILITY_CHOICES = [
		('available', 'Available'),
		('busy', 'Busy'),
		('unavailable', 'Unavailable'),
	]

	owner = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='skills',
	)
	title = models.CharField(max_length=120)
	description = models.TextField()
	category = models.CharField(max_length=80)
	is_free = models.BooleanField(default=False)
	price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
	contact_preference = models.CharField(max_length=20, choices=CONTACT_CHOICES)
	availability_status = models.CharField(
		max_length=20,
		choices=AVAILABILITY_CHOICES,
		default='available',
	)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f'{self.title} ({self.owner.username})'

	@staticmethod
	def normalize_category_value(value):
		# Keep a consistent display style like "Math Tutoring".
		if not value:
			return ''
		return ' '.join(value.split()).title()

	def clean(self):
		self.category = self.normalize_category_value(self.category)

		# Enforce either free OR paid with a positive amount.
		if self.is_free:
			self.price = None
		elif self.price is None or self.price <= 0:
			raise ValidationError({'price': 'Enter a positive price or mark this skill as free.'})

	def save(self, *args, **kwargs):
		# Normalize category even when saving outside Django forms.
		self.category = self.normalize_category_value(self.category)
		super().save(*args, **kwargs)


class Review(models.Model):
	RATING_CHOICES = [
		(1, '1'),
		(2, '2'),
		(3, '3'),
		(4, '4'),
		(5, '5'),
	]

	skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='reviews')
	reviewer = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='skill_reviews',
	)
	rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
	review_text = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']
		constraints = [
			models.UniqueConstraint(fields=['skill', 'reviewer'], name='unique_review_per_user_per_skill'),
		]

	def __str__(self):
		return f'{self.reviewer.username} reviewed {self.skill.title}'


class SessionRequest(models.Model):
	STATUS_CHOICES = [
		('pending', 'Pending'),
		('accepted', 'Accepted'),
		('completed', 'Completed'),
		('declined', 'Declined'),
	]

	skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='session_requests')
	requester = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='skill_session_requests',
	)
	requested_date = models.DateField()
	requested_time = models.TimeField()
	message = models.TextField()
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f'{self.requester.username} requested {self.skill.title}'
