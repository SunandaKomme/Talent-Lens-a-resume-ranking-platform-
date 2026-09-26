from sentence_transformers import SentenceTransformer, util
from skills_list import SKILLS

print("Loading NLP model... (this happens once when the server starts)")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("NLP model loaded successfully!")


def extract_skills(text):
    text = text.lower()
    found_skills = []
    for skill in SKILLS:
        if skill in text:
            found_skills.append(skill)
    return found_skills


def semantic_similarity(text1, text2):
    embeddings = model.encode([text1, text2])
    similarity = util.cos_sim(embeddings[0], embeddings[1])
    return float(similarity[0][0])


def match_resume_to_job(job_text, resume_text):
    job_skills = extract_skills(job_text)
    resume_skills = extract_skills(resume_text)

    matched = [skill for skill in job_skills if skill in resume_skills]
    missing = [skill for skill in job_skills if skill not in resume_skills]

    keyword_score = 0
    if len(job_skills) > 0:
        keyword_score = len(matched) / len(job_skills)

    semantic_score = semantic_similarity(job_text, resume_text)
    semantic_score = max(0, semantic_score)

    final_score = round((keyword_score * 0.6 + semantic_score * 0.4) * 100)

    return {
        "score": final_score,
        "matched_skills": matched,
        "missing_skills": missing
    }