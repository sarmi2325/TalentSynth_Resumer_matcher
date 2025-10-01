import json
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from llama_parse import LlamaParse
# Gemini LLM (v2.5)
from llama_index.llms.gemini import Gemini
from llama_index.core import Settings
from dotenv import load_dotenv
load_dotenv()

LLAMA_API_KEY=os.getenv("LLAMA_API_KEY")
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY")


# LlamaParse setup
parser = LlamaParse(api_key=LLAMA_API_KEY, result_type="markdown")

# LLM setup
Settings.llm = Gemini(api_key=GEMINI_API_KEY, model_name="models/gemini-2.5-flash")

def parse_resume_with_llama(resume_file):
    """Return the full text extracted from resume using LlamaParse."""
    documents = parser.load_data(resume_file)
    return "\n".join([doc.text for doc in documents])

def extract_resume_fields(resume_text):
    """Send text to Gemini and get structured JSON."""
    try:
        prompt = f"""
You are an expert resume parser. Extract EXACT values only in JSON:

{{
"first_name": string|null,
"last_name": string|null,
"email": string|null,
"phone": string|null,
"education": [
    {{
        "institute": string|null,
        "degree": string|null,
        "cgpa": float|null,
        "start_year": string|null,
        "end_year": string|null
    }}
],
"experience": [
    {{
        "type": "work"|"research",
        "designation": string|null,
        "start": string|null,
        "end": string|null|"CURRENT"
       
    }}
],
"skills": [string],
"certifications": [
    {{
        "name": string|null,
        "issuer": string|null
    }}
],
"hackathons": [string],
"publications": [
    {{
        "name": string|null,
        "publisher": string|null
    }}
],
"interests": [string],
"projects": [
    {{
        "name": string|null,
        "description": string|null
    }}
]
}}

Text:
```{resume_text}```


Classify experiences as follows:
- "work" = full-time, part-time, internships
- "research" = research projects, lab work, thesis
STRICTLY FOLLOW:
- If research is after graduation and designation  contain keywords like "Research" or "Research Assistant", include as BOTH work + research.
- If research is during graduation, include ONLY as research.

Dates:
- Use MM-YYYY if available, else YYYY.
- Use "CURRENT" if ongoing.
Output STRICT valid JSON only.
"""
        print(f"DEBUG: Calling Gemini API with prompt length: {len(prompt)}")
        llm = Gemini(api_key=GEMINI_API_KEY, model_name="models/gemini-2.5-flash")
        response = llm.complete(prompt)
        print(f"DEBUG: Gemini response received: {response.text[:200]}...")
        
        text = response.text.strip()
        # clean triple backticks if present
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        first, last = text.find("{"), text.rfind("}")
        if first == -1 or last == -1:
            raise ValueError("No JSON object found in response")
        text = text[first:last+1]
        print(f"DEBUG: Extracted JSON text: {text[:200]}...")
        
        result = json.loads(text)
        print(f"DEBUG: Successfully parsed JSON with keys: {list(result.keys())}")
        return result
        
    except Exception as e:
        print(f"ERROR in extract_resume_fields: {str(e)}")
        print(f"ERROR type: {type(e).__name__}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        raise e

def parse_date(date_str, today=None, is_start=False):
    today = today or datetime.today()
    if not date_str or str(date_str).lower() in ("current", "present", "null"):
        return today if not is_start else None
    try:
        dt = datetime.strptime(date_str, "%m-%Y")
        return dt.replace(day=1 if is_start else 28)
    except:
        try:
            return datetime(int(date_str), 1, 1) if is_start else datetime(int(date_str), 12, 31)
        except:
            return None

def merge_and_sum(experiences):
    intervals = []
    today = datetime.today()
    for exp in experiences:
        start = parse_date(exp.get("start"), today, is_start=True)
        end = parse_date(exp.get("end"), today, is_start=False)
        if start and end:
            intervals.append((start, end))
    if not intervals:
        return 0
    intervals.sort(key=lambda x: x[0])
    merged = []
    cur_start, cur_end = intervals[0]
    for s, e in intervals[1:]:
        if s <= cur_end:
            cur_end = max(cur_end, e)
        else:
            merged.append((cur_start, cur_end))
            cur_start, cur_end = s, e
    merged.append((cur_start, cur_end))
    total_months = sum((relativedelta(e, s).years*12 + relativedelta(e, s).months + 1) for s, e in merged)
    return total_months

def calculate_experience(data):
    """Add total work and research months/years."""
    print(f"DEBUG: Calculating experience from data: {data.get('experience', [])}")
    
    work = []
    research = []
    
    for exp in data.get("experience", []):
        exp_type = exp.get("type", "").lower()
        print(f"DEBUG: Processing experience: {exp}, type: {exp_type}")
        
        if exp_type == "work":
            work.append(exp)
        elif exp_type == "research":
            research.append(exp)
        else:
            # If no type specified, try to infer from designation
            designation = exp.get("designation", "").lower()
            if any(keyword in designation for keyword in ["research", "assistant", "fellow", "intern"]):
                research.append(exp)
            else:
                work.append(exp)
    
    print(f"DEBUG: Work experiences: {work}")
    print(f"DEBUG: Research experiences: {research}")
    
    work_months = merge_and_sum(work)
    research_months = merge_and_sum(research)
    
    result = {
        "work_experience": {"years": work_months//12, "months": work_months%12},
        "research_experience": {"years": research_months//12, "months": research_months%12}
    }
    
    print(f"DEBUG: Calculated experience totals: {result}")
    return result
def extract_job_info(job_desc_text):
    """Extract job title and company from job description using Gemini."""
    try:
        prompt = f"""
Extract the job title and company name from this job description. Return ONLY a JSON object with these fields:

{{
    "title": "exact job title",
    "company": "company name"
}}

Job Description:
```{job_desc_text}```

Instructions:
1. Extract the most specific job title mentioned (e.g., "Senior Software Engineer", "Data Scientist")
2. Extract the company/organization name
3. If not found, use "Unknown" for missing fields
4. Return ONLY valid JSON, no other text
"""
        print(f"DEBUG: Extracting job info from job description (length: {len(job_desc_text)})")
        llm = Gemini(api_key=GEMINI_API_KEY, model_name="models/gemini-2.5-flash")
        response = llm.complete(prompt)
        print(f"DEBUG: Job info response: {response.text}")
        
        text = response.text.strip()
        # Clean up response
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        
        first, last = text.find("{"), text.rfind("}")
        if first == -1 or last == -1:
            raise ValueError("No JSON object found in job info response")
        
        text = text[first:last+1]
        result = json.loads(text)
        print(f"DEBUG: Extracted job info: {result}")
        return result
        
    except Exception as e:
        print(f"ERROR in extract_job_info: {str(e)}")
        print(f"ERROR type: {type(e).__name__}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        # Return fallback values
        return {"title": "Job Analysis", "company": "Unknown Company"}

def compare_resume_with_jobdesc(resume_json, job_desc_text):
    """
    Compare the candidate's parsed resume JSON with the job description
    and return structured evaluation data.
    """
    try:
        prompt = f"""
You are an expert recruiter and technical evaluator.  
Evaluate the candidate's resume against the job description using a strict rubric system.  

Resume JSON:
{resume_json}

Job Description:
{job_desc_text}

Return ONLY a JSON object with this exact structure:
{{
    "skill_matches": [
        {{
            "skill": "skill name",
            "requirement": "what the job requires",
            "resume_evidence": "evidence from resume",
            "score": 0-2,
            "category": "technical|soft|experience|education"
        }}
    ],
    "summary": {{
        "total_score": 0,
        "max_possible_score": 0,
        "overall_fit_percentage": 0,
        "relevant_strengths": ["strength1", "strength2"],
        "areas_of_improvement": ["area1", "area2"],
        "suggested_learning_path": ["suggestion1", "suggestion2"]
    }},
    "detailed_analysis": {{
        "technical_skills_score": 0,
        "soft_skills_score": 0,
        "experience_score": 0,
        "education_score": 0,
        "overall_recommendation": "Strong Match|Good Match|Moderate Match|Weak Match"
    }}
}}

Scoring Rubric:
- 0 = Not Mentioned  
- 1 = Mentioned but weak evidence (just listed, no projects/impact)  
- 2 = Strong evidence (projects, experience, measurable outcomes)  

Return ONLY valid JSON, no other text.
"""
        print(f"DEBUG: Starting resume comparison analysis")
        llm = Gemini(api_key=GEMINI_API_KEY, model_name="models/gemini-2.5-flash")
        response = llm.complete(prompt)
        print(f"DEBUG: Comparison response received: {response.text[:200]}...")
        
        text = response.text.strip()
        # Clean up response
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        
        first, last = text.find("{"), text.rfind("}")
        if first == -1 or last == -1:
            raise ValueError("No JSON object found in comparison response")
        
        text = text[first:last+1]
        result = json.loads(text)
        print(f"DEBUG: Successfully parsed comparison result with {len(result.get('skill_matches', []))} skill matches")
        return result
        
    except Exception as e:
        print(f"ERROR in compare_resume_with_jobdesc: {str(e)}")
        print(f"ERROR type: {type(e).__name__}")
        import traceback
        print(f"ERROR traceback: {traceback.format_exc()}")
        # Return fallback structured data
        return {
            "skill_matches": [],
            "summary": {
                "total_score": 0,
                "max_possible_score": 0,
                "overall_fit_percentage": 0,
                "relevant_strengths": [],
                "areas_of_improvement": ["Error occurred during analysis"],
                "suggested_learning_path": []
            },
            "detailed_analysis": {
                "technical_skills_score": 0,
                "soft_skills_score": 0,
                "experience_score": 0,
                "education_score": 0,
                "overall_recommendation": "Analysis Error"
            }
        }
