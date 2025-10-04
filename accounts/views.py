from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import FileSystemStorage
import json
import logging
from .forms import ResumeUploadForm, JobDescUploadForm, UserProfileForm
from .models import UserProfile, ResumeAnalysis
from .resume_parser import parse_resume_with_llama, extract_resume_fields, calculate_experience, compare_resume_with_jobdesc, extract_job_info

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@login_required
def home(request):
    """
    Home redirect: First-time users go to profile, others go to dashboard
    """
    logger.debug(f"Home view accessed by user: {request.user.username}")
    try:
        user_profile = request.user.profile
        logger.debug(f"User profile found: {user_profile}")
        # If user has no resume data, they're a first-time user
        if not user_profile.parsed_resume_data and not request.session.get('parsed_resume'):
            logger.debug("User is first-time user, redirecting to profile")
            return redirect('profile')
        else:
            logger.debug("User has resume data, redirecting to dashboard")
            return redirect('dashboard')
    except UserProfile.DoesNotExist:
        logger.debug("No profile exists, user is first-time user, redirecting to profile")
        # No profile exists, definitely first-time user
    return redirect('profile')

@login_required
def profile(request):
    """
    Profile page: Upload resume, parse it once, store JSON in user session and database.
    """
    logger.debug(f"Profile view accessed by user: {request.user.username}")
    logger.debug(f"Request method: {request.method}")
    
    # Get or create user profile
    try:
        user_profile = request.user.profile
        logger.debug(f"User profile found: {user_profile}")
    except UserProfile.DoesNotExist:
        logger.debug("No user profile found, creating new one")
        user_profile = UserProfile.objects.create(user=request.user)
        logger.debug(f"Created new user profile: {user_profile}")
    
    # Get parsed resume from session or database
    parsed_resume = request.session.get('parsed_resume', None)
    logger.debug(f"Parsed resume from session: {parsed_resume is not None}")
    if not parsed_resume and user_profile.parsed_resume_data:
        parsed_resume = user_profile.parsed_resume_data
        logger.debug(f"Using parsed resume from database: {parsed_resume is not None}")

    if request.method == "POST":
        logger.debug("POST request received")
        
        # Clear any existing session data to ensure fresh upload
        if 'parsed_resume' in request.session:
            del request.session['parsed_resume']
            logger.debug("Cleared existing session data")
        
        form = ResumeUploadForm(request.POST, request.FILES)
        logger.debug(f"Form is valid: {form.is_valid()}")
        if form.is_valid():
            resume_file = form.cleaned_data['resume']
            logger.debug(f"Resume file received: {resume_file.name}, size: {resume_file.size}")
            
            # Save file to storage
            fs = FileSystemStorage()
            filename = fs.save(resume_file.name, resume_file)
            file_path = fs.path(filename)
            logger.debug(f"File saved to: {file_path}")

            try:
            # Parse resume text with LlamaParse
                logger.debug("Starting LlamaParse extraction...")
                resume_text = parse_resume_with_llama(file_path)
                logger.debug(f"LlamaParse completed. Text length: {len(resume_text)}")

            # Extract fields with Gemini
                logger.debug("Starting Gemini extraction...")
                parsed_json = extract_resume_fields(resume_text)
                logger.debug(f"Gemini extraction completed. JSON keys: {list(parsed_json.keys())}")

            # Calculate experience
                logger.debug("Calculating experience...")
                logger.debug(f"Experience data before calculation: {parsed_json.get('experience', [])}")
                exp_totals = calculate_experience(parsed_json)
                parsed_json.update(exp_totals)
                logger.debug(f"Experience calculated: {exp_totals}")
                logger.debug(f"Final parsed_json keys: {list(parsed_json.keys())}")

                # Save JSON in session and database
                logger.debug("Saving parsed data to session...")
                request.session['parsed_resume'] = parsed_json
                logger.debug("Session saved successfully")
                
                # Update user profile with parsed data
                logger.debug("Updating user profile with parsed data...")
                user_profile.resume_file = resume_file
                user_profile.parsed_resume_data = parsed_json
                
                # Update profile fields
                logger.debug(f"Updating profile fields with new data:")
                logger.debug(f"  - first_name: {parsed_json.get('first_name', '')}")
                logger.debug(f"  - last_name: {parsed_json.get('last_name', '')}")
                logger.debug(f"  - email: {parsed_json.get('email', '')}")
                logger.debug(f"  - phone: {parsed_json.get('phone', '')}")
                
                user_profile.first_name = parsed_json.get('first_name', '')
                user_profile.last_name = parsed_json.get('last_name', '')
                user_profile.email = parsed_json.get('email', '')
                user_profile.phone = parsed_json.get('phone', '')
                
                # Education (store as JSON array)
                user_profile.education = parsed_json.get('education', [])
                
                # Experience (store as JSON array)
                user_profile.experience = parsed_json.get('experience', [])
                
                # Update experience totals
                work_exp = parsed_json.get('work_experience', {})
                user_profile.work_experience_years = work_exp.get('years', 0)
                user_profile.work_experience_months = work_exp.get('months', 0)
                
                research_exp = parsed_json.get('research_experience', {})
                user_profile.research_experience_years = research_exp.get('years', 0)
                user_profile.research_experience_months = research_exp.get('months', 0)
                
                logger.debug(f"Updated experience totals:")
                logger.debug(f"  - Work: {user_profile.work_experience_years} years, {user_profile.work_experience_months} months")
                logger.debug(f"  - Research: {user_profile.research_experience_years} years, {user_profile.research_experience_months} months")
                
                # Lists
                user_profile.skills = parsed_json.get('skills', [])
                user_profile.certifications = parsed_json.get('certifications', [])
                user_profile.hackathons = parsed_json.get('hackathons', [])
                user_profile.publications = parsed_json.get('publications', [])
                user_profile.interests = parsed_json.get('interests', [])
                user_profile.projects = parsed_json.get('projects', [])
                
                user_profile.save()
                
                # Verify the data was saved
                logger.debug(f"Profile saved. Verifying data:")
                logger.debug(f"  - Saved first_name: {user_profile.first_name}")
                logger.debug(f"  - Saved last_name: {user_profile.last_name}")
                logger.debug(f"  - Saved email: {user_profile.email}")
                logger.debug(f"  - Saved phone: {user_profile.phone}")
                
                # Clear old session data and set new data
                if 'parsed_resume' in request.session:
                    del request.session['parsed_resume']
                request.session['parsed_resume'] = parsed_json
                logger.debug("Session data updated with new resume data")
                
                messages.success(request, "✅ Resume uploaded and parsed successfully!")
                return redirect('profile')
                
            except Exception as e:
                logger.error(f"CRITICAL ERROR in resume parsing: {str(e)}")
                logger.error(f"Error type: {type(e).__name__}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
                messages.error(request, f"❌ Error parsing resume: {str(e)}")
                return redirect('profile')
    else:
        form = ResumeUploadForm()

    # Debug logging
    logger.debug(f"Rendering profile template with:")
    logger.debug(f"  - parsed_resume: {parsed_resume is not None}")
    logger.debug(f"  - user_profile.parsed_resume_data: {user_profile.parsed_resume_data is not None}")
    logger.debug(f"  - user_profile.first_name: {user_profile.first_name}")
    logger.debug(f"  - user_profile.last_name: {user_profile.last_name}")
    
    # Force refresh the user profile from database
    user_profile.refresh_from_db()
    logger.debug(f"After refresh - first_name: {user_profile.first_name}, last_name: {user_profile.last_name}")
    
    return render(request, 'account/profile.html', {
        'resume_form': form,
        'parsed_resume': parsed_resume,
        'user_profile': user_profile
    })


@login_required
def debug_profile(request):
    """Debug endpoint to check current profile data"""
    try:
        user_profile = request.user.profile
        return JsonResponse({
            'user': request.user.username,
            'first_name': user_profile.first_name,
            'last_name': user_profile.last_name,
            'email': user_profile.email,
            'phone': user_profile.phone,
            'work_experience_years': user_profile.work_experience_years,
            'work_experience_months': user_profile.work_experience_months,
            'research_experience_years': user_profile.research_experience_years,
            'research_experience_months': user_profile.research_experience_months,
            'experience_data': user_profile.experience,
            'has_parsed_data': bool(user_profile.parsed_resume_data),
            'parsed_data_keys': list(user_profile.parsed_resume_data.keys()) if user_profile.parsed_resume_data else [],
            'session_data': bool(request.session.get('parsed_resume')),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)})

@login_required
def update_profile(request):
    """Update user profile with manual edits"""
    print("update_profile view called with method:", request.method)
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user)
    
    if request.method == "POST":
        # Update profile fields from form data
        user_profile.first_name = request.POST.get('first_name', '')
        user_profile.last_name = request.POST.get('last_name', '')
        user_profile.email = request.POST.get('email', '')
        user_profile.phone = request.POST.get('phone', '')
        
        # Education - handle dynamic education entries
        education = []
        i = 0
        while f'education_institute_{i}' in request.POST:
            institute = request.POST.get(f'education_institute_{i}', '')
            degree = request.POST.get(f'education_degree_{i}', '')
            cgpa = request.POST.get(f'education_cgpa_{i}', '')
            start_year = request.POST.get(f'education_start_{i}', '')
            end_year = request.POST.get(f'education_end_{i}', '')
            if institute or degree:
                education.append({
                    'institute': institute,
                    'degree': degree,
                    'cgpa': float(cgpa) if cgpa else None,
                    'start_year': start_year,
                    'end_year': end_year
                })
            i += 1
        user_profile.education = education
        
        # Skills - handle dynamic skill entries
        skills = []
        i = 0
        while f'skill_{i}' in request.POST:
            skill = request.POST.get(f'skill_{i}', '').strip()
            if skill:
                skills.append(skill)
            i += 1
        user_profile.skills = skills
        
        # Projects - handle dynamic project entries
        projects = []
        i = 0
        while f'project_name_{i}' in request.POST:
            name = request.POST.get(f'project_name_{i}', '')
            description = request.POST.get(f'project_desc_{i}', '')
            if name or description:
                projects.append({'name': name, 'description': description})
            i += 1
        user_profile.projects = projects
        
        # Certifications - handle dynamic certification entries
        certifications = []
        i = 0
        while f'cert_name_{i}' in request.POST:
            name = request.POST.get(f'cert_name_{i}', '')
            issuer = request.POST.get(f'cert_issuer_{i}', '')
            if name or issuer:
                certifications.append({'name': name, 'issuer': issuer})
            i += 1
        user_profile.certifications = certifications
        
        # Publications - handle dynamic publication entries
        publications = []
        i = 0
        while f'pub_name_{i}' in request.POST:
            name = request.POST.get(f'pub_name_{i}', '')
            publisher = request.POST.get(f'pub_publisher_{i}', '')
            if name or publisher:
                publications.append({'name': name, 'publisher': publisher})
            i += 1
        user_profile.publications = publications
        
        # Hackathons - handle dynamic hackathon entries
        hackathons = []
        i = 0
        while f'hackathon_{i}' in request.POST:
            hackathon = request.POST.get(f'hackathon_{i}', '').strip()
            if hackathon:
                hackathons.append(hackathon)
            i += 1
        user_profile.hackathons = hackathons
        
        # Interests - handle dynamic interest entries
        interests = []
        i = 0
        while f'interest_{i}' in request.POST:
            interest = request.POST.get(f'interest_{i}', '').strip()
            if interest:
                interests.append(interest)
            i += 1
        user_profile.interests = interests
        
        # Update the parsed_resume_data JSON to reflect manual changes
        if user_profile.parsed_resume_data:
            user_profile.parsed_resume_data.update({
                'first_name': user_profile.first_name,
                'last_name': user_profile.last_name,
                'email': user_profile.email,
                'phone': user_profile.phone,
                'education': user_profile.education,
                'work_experience': {
                    'years': user_profile.work_experience_years,
                    'months': user_profile.work_experience_months
                },
                'research_experience': {
                    'years': user_profile.research_experience_years,
                    'months': user_profile.research_experience_months
                },
                'skills': user_profile.skills,
                'certifications': user_profile.certifications,
                'hackathons': user_profile.hackathons,
                'publications': user_profile.publications,
                'interests': user_profile.interests,
                'projects': user_profile.projects
            })
        
        user_profile.save()
        print("Updated parsed resume JSON after manual update:")
        print(json.dumps(user_profile.parsed_resume_data, indent=2))
        messages.success(request, "✅ Profile updated successfully!")
    
    return redirect('profile')


@login_required
@require_http_methods(["POST"])
def auto_fill_profile(request):
    """Auto-fill profile using parsed JSON data directly"""
    logger.debug("Auto-fill profile function called")
    try:
        data = json.loads(request.body)
        logger.debug(f"Received data: {data}")
        
        # Get user profile
        try:
            user_profile = request.user.profile
        except UserProfile.DoesNotExist:
            logger.debug("No user profile found, creating new one")
            user_profile = UserProfile.objects.create(user=request.user)
        
        # Get parsed resume data from session or database
        parsed_resume = request.session.get('parsed_resume', None)
        if not parsed_resume and user_profile.parsed_resume_data:
            parsed_resume = user_profile.parsed_resume_data
            logger.debug("Using parsed resume from database")
        
        if not parsed_resume:
            logger.debug("No parsed resume data found")
            return JsonResponse({
                'success': False,
                'error': 'No resume data found. Please upload and parse a resume first.'
            })
        
        logger.debug("Auto-filling profile with parsed data")
        
        # Update profile with parsed data
        user_profile.first_name = parsed_resume.get('first_name', '')
        user_profile.last_name = parsed_resume.get('last_name', '')
        user_profile.email = parsed_resume.get('email', '')
        user_profile.phone = parsed_resume.get('phone', '')
        user_profile.institute = parsed_resume.get('institute', '')
        user_profile.degree = parsed_resume.get('degree', '')
        user_profile.cgpa = parsed_resume.get('cgpa', '')
        
        # Update experience
        work_exp = parsed_resume.get('work_experience', {})
        user_profile.work_experience_years = work_exp.get('years', 0)
        user_profile.work_experience_months = work_exp.get('months', 0)
        
        research_exp = parsed_resume.get('research_experience', {})
        user_profile.research_experience_years = research_exp.get('years', 0)
        user_profile.research_experience_months = research_exp.get('months', 0)
        
        # Update lists
        user_profile.skills = parsed_resume.get('skills', [])
        user_profile.certifications = parsed_resume.get('certifications', [])
        user_profile.hackathons = parsed_resume.get('hackathons', [])
        user_profile.publications = parsed_resume.get('publications', [])
        user_profile.interests = parsed_resume.get('interests', [])
        user_profile.projects = parsed_resume.get('projects', [])
        
        # Update parsed resume data
        user_profile.parsed_resume_data = parsed_resume
        
        user_profile.save()
        
        logger.debug("Profile auto-filled and saved successfully")
        
        return JsonResponse({
            'success': True,
            'message': 'Profile auto-filled successfully with resume data!'
        })
        
    except Exception as e:
        logger.error(f"Error in auto-fill profile: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error auto-filling profile: {str(e)}'
    })


@login_required
@require_http_methods(["DELETE"])
def delete_analysis(request, analysis_id):
    """Delete a resume analysis"""
    try:
        analysis = get_object_or_404(ResumeAnalysis, id=analysis_id, user_profile__user=request.user)
        analysis.delete()
        return JsonResponse({'status': 'success', 'message': 'Analysis deleted successfully'})
    except Exception as e:
        logger.error(f"Error deleting analysis {analysis_id}: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Failed to delete analysis'}, status=500)


@login_required
def get_analysis_details(request, analysis_id):
    """Get detailed analysis data for modal view"""
    try:
        analysis = get_object_or_404(ResumeAnalysis, id=analysis_id, user_profile__user=request.user)
        return JsonResponse({
            'id': analysis.id,
            'job_title': analysis.job_title,
            'job_company': analysis.job_company,
            'created_at': analysis.created_at.isoformat(),
            'skill_matches': analysis.skill_matches,
            'summary': analysis.summary,
            'detailed_analysis': analysis.detailed_analysis,
            'match_score': analysis.match_score,
            'overall_fit_percentage': analysis.get_overall_fit_percentage(),
            'overall_recommendation': analysis.get_overall_recommendation(),
            'skill_matches_count': analysis.get_skill_matches_count()
        })
    except Exception as e:
        logger.error(f"Error getting analysis details {analysis_id}: {str(e)}")
        return JsonResponse({'error': 'Failed to get analysis details'}, status=500)

@login_required
def dashboard(request):
    """
    Dashboard: Upload job description and compare with parsed resume JSON.
    """
    logger.debug(f"Dashboard view accessed by user: {request.user.username}")
    
    # Get user profile and parsed resume data
    try:
        user_profile = request.user.profile
        logger.debug(f"User profile found: {user_profile}")
    except UserProfile.DoesNotExist:
        logger.debug("No user profile found, redirecting to profile")
        return redirect('profile')
    
    # Get parsed resume from session or database
    parsed_resume = request.session.get('parsed_resume', None)
    logger.debug(f"Parsed resume from session: {parsed_resume is not None}")
    if not parsed_resume and user_profile.parsed_resume_data:
        parsed_resume = user_profile.parsed_resume_data
        logger.debug(f"Using parsed resume from database: {parsed_resume is not None}")
    
    logger.debug(f"Final parsed_resume status: {parsed_resume is not None}")
    logger.debug(f"User profile parsed_resume_data: {user_profile.parsed_resume_data is not None}")
    
    comparison_result = None

    if not parsed_resume:
        return redirect('profile')  # ensure resume is uploaded first

    if request.method == "POST":
        form = JobDescUploadForm(request.POST, request.FILES)
        if form.is_valid():
            job_text = ""
            
            # Handle file upload
            if form.cleaned_data.get('job_desc'):
                job_file = form.cleaned_data['job_desc']
                logger.debug(f"Job file received: {job_file.name}, size: {job_file.size}")
                
                # Save file to storage
                fs = FileSystemStorage()
                filename = fs.save(job_file.name, job_file)
                file_path = fs.path(filename)
                logger.debug(f"Job file saved to: {file_path}")
                
                try:
                    # Use LlamaParse to extract text from job description file
                    logger.debug("Starting LlamaParse extraction for job description...")
                    job_text = parse_resume_with_llama(file_path)
                    logger.debug(f"Job description text extracted, length: {len(job_text)}")
                    logger.debug(f"Job description preview: {job_text[:200]}...")
                    
                    # Clean up the temporary file
                    import os
                    try:
                        os.remove(file_path)
                        logger.debug(f"Temporary file cleaned up: {file_path}")
                    except Exception as cleanup_error:
                        logger.warning(f"Could not clean up temporary file: {cleanup_error}")
                        
                except Exception as e:
                    logger.error(f"CRITICAL ERROR parsing job description file: {str(e)}")
                    logger.error(f"Error type: {type(e).__name__}")
                    import traceback
                    logger.error(f"Full traceback: {traceback.format_exc()}")
                    messages.error(request, f"❌ Error parsing job description file: {str(e)}")
                    return redirect('dashboard')
            
            # Handle text input
            elif form.cleaned_data.get('job_text'):
                job_text = form.cleaned_data['job_text']
                logger.debug(f"Job description text received, length: {len(job_text)}")
            
            if job_text:
                try:
                    # Compare resume vs job description via Gemini
                    logger.debug("Starting resume vs job description comparison...")
                    logger.debug(f"Resume data keys: {list(parsed_resume.keys())}")
                    logger.debug(f"Job description length: {len(job_text)}")
                    
                    comparison_result = compare_resume_with_jobdesc(parsed_resume, job_text)
                    logger.debug("Comparison completed successfully")
                    
                    # Save analysis to database
                    try:
                        # Extract job title and company using Gemini for better accuracy
                        logger.debug("Extracting job title and company from job description...")
                        job_info = extract_job_info(job_text)
                        job_title = job_info.get('title', 'Job Analysis')
                        job_company = job_info.get('company', 'Unknown Company')
                        logger.debug(f"Extracted job info: Title='{job_title}', Company='{job_company}'")
                        
                        # Save structured analysis data
                        analysis = ResumeAnalysis.objects.create(
                            user_profile=user_profile,
                            job_description=job_text,
                            job_title=job_title,
                            job_company=job_company,
                            skill_matches=comparison_result.get('skill_matches', []),
                            summary=comparison_result.get('summary', {}),
                            detailed_analysis=comparison_result.get('detailed_analysis', {}),
                            match_score=comparison_result.get('summary', {}).get('overall_fit_percentage', 0.0),
                            # Legacy fields for backward compatibility
                            relevant_points=comparison_result.get('summary', {}).get('relevant_strengths', []),
                            improvement_needed=comparison_result.get('summary', {}).get('areas_of_improvement', [])
                        )
                        logger.debug(f"Analysis saved with ID: {analysis.id}")
                    except Exception as e:
                        print(f"Error saving analysis: {e}")  # Don't fail if database save fails
                        
                except Exception as e:
                    logger.error(f"CRITICAL ERROR in job description analysis: {str(e)}")
                    logger.error(f"Error type: {type(e).__name__}")
                    import traceback
                    logger.error(f"Full traceback: {traceback.format_exc()}")
                    messages.error(request, f"❌ Error analyzing job description: {str(e)}")
    else:
        form = JobDescUploadForm()

    # Get analysis history
    analysis_history = ResumeAnalysis.objects.filter(user_profile=user_profile).order_by('-created_at')[:10]
    logger.debug(f"Found {analysis_history.count()} analysis records")
    
    return render(request, 'account/dashboard.html', {
        'job_form': form,
        'comparison_result': comparison_result,
        'parsed_resume': parsed_resume,
        'user_profile': user_profile,
        'analysis_history': analysis_history
    })
