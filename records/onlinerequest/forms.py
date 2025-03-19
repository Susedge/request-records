from django import forms
from .models import User, Record, Profile
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError


class UserRegistrationForm(forms.ModelForm):
    student_number = forms.CharField(
        max_length=64,
        required=False,  # Make it optional
        error_messages={
            'unique': 'This student number is already in use.',
        },
        help_text="Optional. Leave blank to auto-generate an ID."
    )

    email = forms.CharField(
        max_length=64,
        error_messages={
            'required': 'Please enter your email.',
            'unique': 'Invalid student email.'
        }
    )
 
    user_type = forms.IntegerField(
        error_messages={
            'required': 'Please enter your user type.',
        }
    )

    verification_code = forms.CharField(max_length=6)

    def clean_student_number(self):
        student_number = self.cleaned_data.get('student_number')
        # Only validate if a value is provided
        if student_number:
            if User.objects.filter(student_number=student_number).exists():
                raise forms.ValidationError('This student number is already in use.')
        return student_number

    class Meta:
        model = User
        fields = ['email', 'student_number', 'password', 'user_type']

    def save(self, commit = True):
        user = super().save(commit = False)
        user.set_password(self.cleaned_data["password"])

        if commit == True:
            user.save()
        return user# For modifying user form
class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ('email', 'password', 'student_number', 'is_active')

    def clean_password(self):
        return self.initial["password"]

class ProfileForm(forms.ModelForm):
    contact_no = forms.IntegerField()

    class Meta:
        model = Profile
        fields = '__all__'

    def clean_contact_no(self):
        contact_no = self.data.get('contact_no')

        if contact_no:
            # Convert contact_no to a string for slicing
            contact_no_str = str(contact_no)
            first_two_digits = contact_no_str[:2]

            if first_two_digits != "09":
                raise forms.ValidationError("Please enter a valid contact number starting with 09.")
        
        return str(contact_no)



