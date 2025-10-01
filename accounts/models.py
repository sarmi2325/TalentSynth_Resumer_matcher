from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
import json


class UserProfile(models.Model):
    """Extended user profile with resume data"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Personal Information
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Education (JSONField for multiple entries)
    education = models.JSONField(default=list, blank=True)
    
    # Experience (JSONField for multiple entries)
    work_experience_years = models.IntegerField(default=0)
    work_experience_months = models.IntegerField(default=0)
    research_experience_years = models.IntegerField(default=0)
    research_experience_months = models.IntegerField(default=0)
    
    # Skills and Activities
    skills = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)
    hackathons = models.JSONField(default=list, blank=True)
    publications = models.JSONField(default=list, blank=True)
    interests = models.JSONField(default=list, blank=True)
    
    # Projects
    projects = models.JSONField(default=list, blank=True)
    
    # Resume Data
    resume_file = models.FileField(
        upload_to='resumes/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])],
        blank=True,
        null=True
    )
    parsed_resume_data = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def get_full_name(self):
        """Get full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.user.username
    
    def get_total_experience(self):
        """Get total experience in years"""
        total_months = (self.work_experience_years * 12 + self.work_experience_months + 
                       self.research_experience_years * 12 + self.research_experience_months)
        return total_months / 12


class ResumeAnalysis(models.Model):
    """Resume analysis results"""
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='analyses')
    
    # Analysis Results (structured data)
    skill_matches = models.JSONField(default=list, blank=True)
    summary = models.JSONField(default=dict, blank=True)
    detailed_analysis = models.JSONField(default=dict, blank=True)
    match_score = models.FloatField(default=0.0)
    
    # Legacy fields (for backward compatibility)
    relevant_points = models.JSONField(default=list, blank=True)
    improvement_needed = models.JSONField(default=list, blank=True)
    
    # Job Description
    job_description = models.TextField(blank=True, null=True)
    job_title = models.CharField(max_length=200, blank=True, null=True)
    job_company = models.CharField(max_length=200, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Analysis for {self.user_profile.user.username} - {self.job_title}"
    
    def get_overall_fit_percentage(self):
        """Get overall fit percentage from summary data"""
        return self.summary.get('overall_fit_percentage', 0)
    
    def get_overall_recommendation(self):
        """Get overall recommendation from detailed analysis"""
        return self.detailed_analysis.get('overall_recommendation', 'Unknown')
    
    def get_skill_matches_count(self):
        """Get total number of skill matches"""
        return len(self.skill_matches)
