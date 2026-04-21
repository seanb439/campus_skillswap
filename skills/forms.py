from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Review, SessionRequest, Skill


class UserRegistrationForm(UserCreationForm):
    # Email is optional in Django by default, so we make it required.
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = [
            'title',
            'description',
            'category',
            'is_free',
            'price',
            'contact_preference',
            'availability_status',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == 'is_free':
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        is_free = cleaned_data.get('is_free')
        price = cleaned_data.get('price')

        # Keep form feedback simple and immediate for beginners.
        if not is_free and (price is None or price <= 0):
            self.add_error('price', 'Please enter a positive price or mark this skill as free.')

        if is_free:
            cleaned_data['price'] = None

        return cleaned_data


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'review_text']
        widgets = {
            'review_text': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == 'rating':
                field.widget.attrs.update({'class': 'form-select'})
            else:
                field.widget.attrs.update({'class': 'form-control'})


class SessionRequestForm(forms.ModelForm):
    class Meta:
        model = SessionRequest
        fields = ['requested_date', 'requested_time', 'message']
        widgets = {
            'requested_date': forms.DateInput(attrs={'type': 'date'}),
            'requested_time': forms.TimeInput(attrs={'type': 'time'}),
            'message': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in {'requested_date', 'requested_time'}:
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs.update({'class': 'form-control'})