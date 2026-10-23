import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=json.loads((ROOT/"profile.json").read_text())
def evaluate(j):
 title=j.get("title",""); loc=j.get("location",""); desc=j.get("description","")
 if not title or not j.get("url") or any(x in title.lower() for x in ["senior","staff","principal","director"]): return 0,"Missing link/title or likely senior role",False
 fresh=any(x in (title+" "+desc).lower() for x in ["fresher","fresh graduate","new grad","graduate","entry-level","entry level","junior","associate","trainee","early career"])
 india=any(x in (loc+" "+desc[:1000]).lower() for x in ["india","bengaluru","bangalore","hyderabad","chennai","pune","gurugram","gurgaon","noida","mumbai","delhi","remote"])
 skills=[s for s in P["skills"] if s.lower() in (title+" "+desc).lower()]
 score=min(35,len(skills)*7)+(35 if fresh else 5)+(20 if india else 0)+(10 if any(x in title.lower() for x in ["software engineer","software developer","backend","python","qa engineer","test engineer","graduate engineer"]) else 0)
 return min(100,score),("entry-level wording found" if fresh else "fresher eligibility not confirmed")+"; "+("India/remote keyword found" if india else "location eligibility not confirmed")+"; skills: "+", ".join(skills[:8]),fresh
def drafts(j,out):
 out.mkdir(parents=True,exist_ok=True); a=P["personal"]; e=P["education"]
 slug=re.sub("[^a-z0-9]+","-",(j.get("company","company")+"-"+j.get("title","role")).lower()).strip("-")[:65]
 desc=j.get("description","").lower(); skills=sorted(P["skills"],key=lambda s:s.lower() not in desc)
 resume=[f"# {a['full_name']}",f"{a['location']} | {a['email']} | {a['phone']}",f"LinkedIn: {a['linkedin']} | GitHub: {a['github']}","","## Summary",P["summary"],"","## Skills",", ".join(skills),"","## Projects"]
 for x in P["projects"]: resume += [f"### {x['name']}",x["description"]]
 resume += ["","## Education",f"{e['degree']} — {e['college']}",f"Graduation: {e['graduation_year']} | CGPA: {e.get('cgpa','')}","","## Certifications"]+["- "+x for x in P.get("certifications",[])]
 cover=f"Dear Hiring Team,\n\nI am applying for {j.get('title')} at {j.get('company')}. I am a 2026 B.Tech CSE graduate with project experience in Python, APIs and AI-enabled applications. My projects include LectureLens, ContractGuard, MedScript AI and DuoAudit. I would welcome the opportunity to contribute and learn.\n\nPlease review my resume draft. I will verify the role requirements and all details before submitting.\n\nRegards,\n{a['full_name']}\n"
 rp=out/(slug+"-resume.md"); cp=out/(slug+"-cover-letter.txt"); rp.write_text("\n".join(resume)); cp.write_text(cover)
 return str(rp),str(cp)
