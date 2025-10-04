from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from .models import UserProfile
import uuid

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_auto_signup_allowed(self, request, sociallogin):
        # Always allow auto-signup for Google OAuth
        return True
    
    def populate_user(self, request, sociallogin, data):
        """
        Populates user information from social provider info.
        This is where we handle username generation properly.
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Generate a unique username if needed
        if not user.username:
            # Use email prefix or generate unique username
            email_prefix = user.email.split('@')[0] if user.email else 'user'
            base_username = email_prefix
            
            # Ensure username is unique
            username = base_username
            counter = 1
            from django.contrib.auth.models import User
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user.username = username
        
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save user and automatically create UserProfile
        """
        user = super().save_user(request, sociallogin, form)
        
        # Create UserProfile for Google OAuth users
        if not hasattr(user, 'profile'):
            UserProfile.objects.create(user=user)
        
        return user

class MyAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        """
        Save user with proper username handling
        """
        if not user.username:
            # Generate unique username from email
            email_prefix = user.email.split('@')[0] if user.email else 'user'
            base_username = email_prefix
            
            # Ensure username is unique
            username = base_username
            counter = 1
            from django.contrib.auth.models import User
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user.username = username
        
        return super().save_user(request, user, form, commit)
