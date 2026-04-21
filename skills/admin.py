from django.contrib import admin

from .models import Review, SessionRequest, Skill


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
	list_display = ('title', 'owner', 'category', 'is_free', 'price', 'availability_status', 'created_at')
	search_fields = ('title', 'description', 'category', 'owner__username')
	list_filter = ('is_free', 'availability_status', 'category')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
	list_display = ('skill', 'reviewer', 'rating', 'created_at')
	search_fields = ('skill__title', 'reviewer__username', 'review_text')
	list_filter = ('rating', 'created_at')


@admin.register(SessionRequest)
class SessionRequestAdmin(admin.ModelAdmin):
	list_display = ('skill', 'requester', 'requested_date', 'requested_time', 'status', 'created_at')
	search_fields = ('skill__title', 'requester__username', 'message')
	list_filter = ('status', 'requested_date', 'created_at')
