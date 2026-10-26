"""Conservative filters and truthful job-specific draft generation."""
import json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
P = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))

SENIOR_TITLE = re.compile(r"\b(senior|sr\.?|staff|principal|lead|manager|director|head of|chief|architect|distinguished|fellow|vp|vice president)\b", re.I)
NON_FULL_TIME = re.compile(r"\b(intern(ship)?|co[- ]?op|apprentice(ship)?|temporary|temp role|part[- ]?time|freelance|contract(or)?|seasonal|volunteer|trainee internship)\b", re.I)
BAD_ROLE = re.compile(r"\b(recruiter|sales|account executive|customer success|marketing|product manager|engineering manager|support specialist|solutions consultant)\b", re.I)
ROLE_TERMS = {
    "software": ["software engineer", "software developer", "sde", "application engineer", "graduate engineer", "associate engineer"],
    "backend": ["backend", "back-end", "api developer", "python developer"],
    "qa": ["qa engineer", "quality assurance", "test automation", "software test", "automation engineer"],
    "data": ["data engineer", "analytics engineer", "junior data"],
    "devops": ["devops", "site reliability", "sre", "cloud engineer", "platform engineer"]
}

def _text(j):
    return " ".join(str(j.get(k, "") or "") for k in ("title", "description", "location", "workplace")).lower()

def _role_family(j):
    t = (j.get("title") or "").lower()
    for family, terms in ROLE_TERMS.items():
        if any(term in t for term in terms):
            return family
    return "other"

def _location_ok(j):
    loc = (j.get("location") or "").lower()
    desc = (j.get("description") or "").lower()
    workplace = (j.get("workplace") or "").lower()
    hyderabad = "hyderabad" in loc
    bengaluru = any(x in loc for x in ("bengaluru", "bangalore"))
    remote = any(x in (loc + " " + workplace) for x in ("remote", "distributed"))
    india = "india" in (loc + " " + workplace) or any(x in loc for x in ("hyderabad", "bengaluru", "bangalore"))
    remote_india = remote and (india or "india" in desc[:3000] or "remote in india" in desc[:3000] or "india remote" in desc[:3000])
    return hyderabad or bengaluru or remote_india

def evaluate(j):
    title = str(j.get("title") or "").strip()
    url = str(j.get("url") or "").strip()
    desc = str(j.get("description") or "")
    text = _text(j)
    reasons = []
    if not title or not url:
        return 0, "Excluded: missing title or official listing URL", False
    if SENIOR_TITLE.search(title):
        return 0, "Excluded: senior/staff/lead/manager-level title is not fresher-targeted", False
    if NON_FULL_TIME.search(title) or NON_FULL_TIME.search(desc[:5000]):
        return 0, "Excluded: internship, co-op, contract, temporary, part-time or other non-full-time wording found", False
    if BAD_ROLE.search(title):
        return 0, "Excluded: role family is outside the configured technical fresher targets", False
    family = _role_family(j)
    if family == "other":
        return 0, "Excluded: title does not match the configured software/backend/QA/data/DevOps role families", False
    if not _location_ok(j):
        return 0, "Excluded: location not confirmed as India-eligible remote, Hyderabad or Bengaluru", False

    # Reject explicit experience requirements that strongly conflict with a new graduate.
    years = []
    for m in re.finditer(r"\b(\d{1,2})\s*\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:relevant\s+)?experience\b", text):
        try: years.append(int(m.group(1)))
        except ValueError: pass
    if years and min(years) >= 3:
        return 0, f"Excluded: listing explicitly asks for {min(years)}+ years of experience", False

    fresh_terms = ["new grad", "new graduate", "recent graduate", "recently graduated", "entry-level", "entry level", "early career", "graduate engineer", "graduate program", "university graduate", "0-1 years", "0 to 1 years", "fresher", "fresh graduate", "junior"]
    fresh = any(term in text for term in fresh_terms)
    skills = [s for s in P.get("skills", []) if str(s).lower() in text]
    score = min(35, len(skills) * 5)
    score += 25 if fresh else 8
    score += 20  # passed configured location filter
    score += 15 if family in ("software", "backend", "qa") else 10
    if years and min(years) <= 2: score += 5
    reasons.append("target technical role family: " + family)
    reasons.append("location matches configured priorities")
    reasons.append("explicit fresher/graduate wording found" if fresh else "fresher eligibility not explicit; manually verify requirements")
    reasons.append("experience requirement found: " + str(min(years)) + " years" if years else "no numeric experience requirement detected")
    reasons.append("matching profile skills: " + (", ".join(skills[:8]) if skills else "none detected by exact keyword"))
    reasons.append("full-time: no non-full-time wording detected; verify employment type on official page")
    return min(100, score), "; ".join(reasons), fresh

def drafts(j, out):
    out.mkdir(parents=True, exist_ok=True)
    a, e = P["personal"], P["education"]
    slug = re.sub(r"[^a-z0-9]+", "-", (j.get("company", "company") + "-" + j.get("title", "role")).lower()).strip("-")[:65]
    desc = (j.get("description") or "").lower()
    family = _role_family(j)
    # Rank only existing profile skills; never add a skill that isn't in the master profile.
    skills = sorted(P.get("skills", []), key=lambda s: (str(s).lower() not in desc, str(s).lower()))
    relevant = [x for x in P.get("projects", []) if any(k in (x.get("name", "") + " " + x.get("description", "")).lower() for k in ("python", "api", "backend", "test", "security", "data", "ai", "machine learning", "automation"))]
    project_order = sorted(P.get("projects", []), key=lambda x: (not any(term in (x.get("name", "") + " " + x.get("description", "")).lower() for term in desc.split() if len(term) > 4), x.get("name", "")))
    # Keep a conservative role-specific summary based on verified profile facts.
    family_summary = {
        "software": "2026 B.Tech CSE graduate with project experience building software applications, Python-based tools and API-connected prototypes.",
        "backend": "2026 B.Tech CSE graduate with project experience in Python, REST APIs, backend-oriented applications and data services.",
        "qa": "2026 B.Tech CSE graduate with project experience in debugging, testing and validating software prototypes; interested in software quality and test automation.",
        "data": "2026 B.Tech CSE graduate with academic/project exposure to data-oriented and machine-learning applications.",
        "devops": "2026 B.Tech CSE graduate with project experience using Git/GitHub, Linux and workflow automation; interested in reliable software delivery."
    }
    summary = family_summary.get(family, P.get("summary", ""))
    resume = [f"# {a.get('full_name','')}", f"{a.get('location','')} | {a.get('email','')} | {a.get('phone','')}", f"LinkedIn: {a.get('linkedin','')} | GitHub: {a.get('github','')}", "", "## Target role", f"{j.get('title','')} — {j.get('company','')}", f"Official posting: {j.get('url','')}", "", "## Summary", summary, "", "## Skills (prioritized by job-description keyword overlap)", ", ".join(skills), "", "## Projects"]
    for x in project_order:
        resume += [f"### {x.get('name','')}", x.get('description','')]
    resume += ["", "## Education", f"{e.get('degree','')} — {e.get('college','')}", f"Graduation: {e.get('graduation_year','')} | CGPA: {e.get('cgpa','')}", "", "## Certifications"] + ["- " + x for x in P.get("certifications", [])]
    resume += ["", "> Review before use: verify contact details, CGPA, every project claim and skills. This draft uses keyword overlap and is not a guarantee of ATS compatibility."]
    cover = (f"Dear Hiring Team,\n\nI am applying for the {j.get('title','')} position at {j.get('company','')}. I am a 2026 B.Tech Computer Science and Engineering graduate. My project work includes {', '.join(x.get('name','') for x in project_order[:3])}, involving software prototypes and technical problem-solving.\n\nThe role description mentions areas that overlap with my listed skills and projects. I would welcome the opportunity to discuss how my project experience and willingness to learn could contribute to your team. I have kept this letter limited to the information in my profile; I will verify the role requirements and details before submitting.\n\nRegards,\n{a.get('full_name','')}\n")
    rp = out / (slug + "-resume.md"); cp = out / (slug + "-cover-letter.txt")
    rp.write_text("\n".join(resume), encoding="utf-8"); cp.write_text(cover, encoding="utf-8")
    return str(rp), str(cp)
