import json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
P = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))
PREF = json.loads((ROOT / "preferences.json").read_text(encoding="utf-8"))

def evaluate(j):
    title=(j.get("title") or "").strip()
    loc=(j.get("location") or "").strip()
    desc=(j.get("description") or "").strip()
    workplace=(j.get("workplace") or "").strip()
    title_low=title.lower(); loc_low=loc.lower(); desc_low=desc.lower()
    if not title or not j.get("url"): return 0,"Excluded: missing title/link",False
    if any(x in title_low for x in ["senior","staff ","principal","director","manager","architect"]):
        return 0,"Excluded: senior/managerial title",False
    if any(x in title_low for x in PREF["excluded_job_families"]):
        return 0,"Excluded: unrelated job family",False
    if not any(x in title_low for x in PREF["target_job_families"]):
        return 0,"Excluded: not a target technical job family",False
    remote=any(x in (loc_low+" "+workplace.lower()) for x in ["remote","distributed","work from home"])
    city=any(x in loc_low for x in ["hyderabad","bengaluru","bangalore"])
    india=any(x in (loc_low+" "+desc_low[:3500]) for x in ["india","indian candidates","based in india","within india","hyderabad","bengaluru","bangalore"])
    if remote and not india:
        return 0,"Excluded: remote India eligibility not confirmed",False
    if not remote and not city:
        return 0,"Excluded: location not Hyderabad/Bengaluru or India-eligible remote",False
    fresh=any(x in (title_low+" "+desc_low) for x in ["fresher","fresh graduate","new grad","new graduate","graduate","entry-level","entry level","junior","associate","trainee","early career","0-1 year","0-2 years","no experience"])
    exp=re.search(r"\b([3-9]|\d{2,})\+?\s+years?\s+(?:of\s+)?(?:professional\s+)?(?:software\s+)?experience\b",desc,re.I)
    if exp: return 0,"Excluded: likely requires 3+ years experience",False
    skills=[s for s in P.get("skills",[]) if s.lower() in (title_low+" "+desc_low)]
    score=min(30,len(skills)*6)+(30 if fresh else 0)+(25 if city else 20)+15+10
    notes=["Product/technology ATS board priority; verify company type",
           "Hyderabad/Bengaluru priority" if city else "India-eligible remote keyword found",
           "Fresher wording found" if fresh else "Fresher eligibility not confirmed"]
    if skills: notes.append("Profile skill overlap: "+", ".join(skills[:8]))
    notes.append("Verify graduation year, experience, vacancy status and official page")
    return min(100,score),"; ".join(notes),fresh

def drafts(j,out):
    out.mkdir(parents=True,exist_ok=True)
    a=P["personal"]; e=P["education"]
    slug=re.sub(r"[^a-z0-9]+","-",(j.get("company","company")+"-"+j.get("title","role")).lower()).strip("-")[:65]
    desc=(j.get("description") or "").lower()
    skills=sorted(P.get("skills",[]),key=lambda s:s.lower() not in desc)
    resume=[f"# {a['full_name']}",f"{a['location']} | {a.get('email','')} | {a.get('phone','')}",
            f"LinkedIn: {a.get('linkedin','')} | GitHub: {a.get('github','')}","","## Summary",P.get("summary",""),
            "","## Skills",", ".join(skills),"","## Projects"]
    for x in P.get("projects",[]): resume += [f"### {x['name']}",x["description"]]
    resume += ["","## Education",f"{e['degree']} — {e['college']}",f"Graduation: {e['graduation_year']} | CGPA: {e.get('cgpa','')}","","## Certifications"]
    resume += ["- "+x for x in P.get("certifications",[])]
    cover=f"Dear Hiring Team,\n\nI am applying for {j.get('title')} at {j.get('company')}. I am a 2026 B.Tech CSE graduate with project experience in Python, APIs and AI-enabled applications. My projects include LectureLens, ContractGuard, MedScript AI and DuoAudit. I would welcome the opportunity to contribute and learn.\n\nPlease review my resume draft. I will verify role requirements and all details before submitting.\n\nRegards,\n{a['full_name']}\n"
    rp=out/(slug+"-resume.md"); cp=out/(slug+"-cover-letter.txt")
    rp.write_text("\n".join(resume),encoding="utf-8"); cp.write_text(cover,encoding="utf-8")
    return str(rp),str(cp)
