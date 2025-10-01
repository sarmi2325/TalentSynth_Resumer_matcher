from django import forms
from .models import UserProfile


class ResumeUploadForm(forms.Form):
    """Resume upload form"""
    resume = forms.FileField(
        label='Upload Resume',
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx',
            'id': 'id_resume'
        }),
        help_text='Upload your resume in PDF, DOC, or DOCX format'
    )


class JobDescUploadForm(forms.Form):
    """Job description upload form"""
    job_desc = forms.FileField(
        label='Upload Job Description',
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.txt,.pdf,.doc,.docx',
            'id': 'id_job_desc'
        }),
        required=False,
        help_text='Upload job description file (optional)'
    )
    job_text = forms.CharField(
        label='Or Paste Job Description',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 8,
            'placeholder': 'Paste the job description here...'
        }),
        required=False,
        help_text='Alternatively, paste the job description text directly'
    )


class UserProfileForm(forms.ModelForm):
    """User profile form for manual editing"""
    
    class Meta:
        model = UserProfile
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'education',
            'work_experience_years', 'work_experience_months',
            'research_experience_years', 'research_experience_months',
            'skills', 'certifications', 'hackathons', 'publications', 'interests', 'projects'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'education': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Enter education details in JSON format'}),
            'work_experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'work_experience_months': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '11'}),
            'research_experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'research_experience_months': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '11'}),
            'skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter skills separated by commas'}),
            'certifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter certifications separated by commas'}),
            'hackathons': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter hackathons separated by commas'}),
            'publications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter publications separated by commas'}),
            'interests': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter interests separated by commas'}),
            'projects': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Enter projects in JSON format or as text'}),
        }
    
    def clean_skills(self):
        """Convert comma-separated skills to list"""
        skills = self.cleaned_data.get('skills', '')
        if isinstance(skills, str):
            return [skill.strip() for skill in skills.split(',') if skill.strip()]
        return skills
    
    def clean_certifications(self):
        """Convert comma-separated certifications to list"""
        certs = self.cleaned_data.get('certifications', '')
        if isinstance(certs, str):
            return [cert.strip() for cert in certs.split(',') if cert.strip()]
        return certs
    
    def clean_hackathons(self):
        """Convert comma-separated hackathons to list"""
        hackathons = self.cleaned_data.get('hackathons', '')
        if isinstance(hackathons, str):
            return [hack.strip() for hack in hackathons.split(',') if hack.strip()]
        return hackathons
    
    def clean_publications(self):
        """Convert comma-separated publications to list"""
        pubs = self.cleaned_data.get('publications', '')
        if isinstance(pubs, str):
            return [pub.strip() for pub in pubs.split(',') if pub.strip()]
        return pubs
    
    def clean_interests(self):
        """Convert comma-separated interests to list"""
        interests = self.cleaned_data.get('interests', '')
        if isinstance(interests, str):
            return [interest.strip() for interest in interests.split(',') if interest.strip()]
        return interests
