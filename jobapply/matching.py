import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))
PREF = json.loads((ROOT / "preferences.json").read_text(encoding="utf-8"))

GRAD_YEAR = int(PREF.get("target_graduation_year", 2026))
MAX_MIN_EXP = int(PREF.get("max_required_min_experience_years", 0))
CITIES = [c.lower() for c in PREF.get("allowed_non_remote_cities", ["hyderabad", "bengaluru", "bangalore"])]
TARGETS = [x.lower() for x in PREF.get("target_job_families", [])]
EXCL_FAMILIES = [x.lower() for x in PREF.get("excluded_job_families", [])]
EXCL_TITLE = [x.strip().lower() for x in PREF.get("excluded_title_keywords", [])]
EXCL_TYPES = [x.strip().lower() for x in PREF.get("excluded_employment_types", [])]
PRODUCT = [x.lower() for x in PREF.get("product_companies", [])]

NON_INDIA = ["us", "usa", "u.s.", "united states", "canada", "uk", "united kingdom", "europe", "emea",
             "latam", "latin america", "australia", "germany", "ireland", "singapore", "mexico", "brazil"]
INDIA_PHRASES = ["remote in india", "india remote", "remote - india", "remote, india", "based in india",
                 "within india", "anywhere in india", "candidates in india", "located in india",
                 "india-based", "india based", "open to india", "eligible to work in india"]
FRESH_WORDS = ["fresher", "fresh graduate", "new grad", "new graduate", "graduate", "entry-level",
               "entry level", "junior", "associate", "trainee", "early career", "0-1 year",
               "0-2 years", "no experience"]


def has(words, text):
    return any(re.search(r"(?<![a-z0-9])" + re.escape(w) + r"(?![a-z0-9])", text) for w in words if w)


def min_experience(text):
    found = []
    for m in re.finditer(r"(\d{1,2})\s*\+?\s*(?:(?:-|–|to)\s*\d{1,2}\s*\+?\s*)?years?", text):
        ctx = text[max(0, m.start() - 60): m.end() + 60]
        if "experience" in ctx:
            found.append(int(m.group(1)))
    return min(found) if found else 0


def grad_years(text):
    ys = set(int(y) for y in re.findall(r"\b(20[2-3]\d)\s*(?:batch|graduates?|graduating|passouts?|pass-outs?)", text))
    ys |= set(int(y) for y in re.findall(r"graduat\w*\s+(?:in|by|before|between)\s+(20[2-3]\d)", text))
    return ys


def evaluate(j):
    title = (j.get("title") or "").strip()
    loc = (j.get("location") or "").strip()
    desc = (j.get("description") or "").strip()
    wp = (j.get("workplace") or "").strip()
    emp = (j.get("employment_type") or j.get("commitment") or "").strip()
    company = (j.get("company") or "").strip()
    t, l, d, w, e = (x.lower() for x in (title, loc, desc, wp, emp))

    if not title or not j.get("url"):
        return 0, "Excluded: missing title/link", False
    if has(EXCL_TITLE, t):
        return 0, "Excluded: internship/senior/managerial title", False
    if has(EXCL_TYPES, e):
        return 0, "Excluded: not a full-time permanent role", False
    if has(EXCL_FAMILIES, t):
        return 0, "Excluded: unrelated job family", False
    if not has(TARGETS, t):
        return 0, "Excluded: not a target technical job family", False

    remote = has(["remote", "distributed", "work from home", "wfh"], l + " " + w)
    city = next((c for c in CITIES if c in l), None)
    if remote:
        if "india" in l or city:
            pass
        elif has(NON_INDIA, l):
            return 0, "Excluded: remote role not open to India", False
        elif not any(p in d for p in INDIA_PHRASES):
            return 0, "Excluded: remote India eligibility not confirmed", False
    elif not city:
        return 0, "Excluded: location not Hyderabad/Bengaluru or India-eligible remote", False

    mexp = min_experience(d)
    if mexp > MAX_MIN_EXP:
        return 0, f"Excluded: requires {mexp}+ years experience", False

    gy = grad_years(d)
    if gy and GRAD_YEAR not in gy:
        return 0, "Excluded: targets other graduation batches", False

    fresh = has(FRESH_WORDS, t + " " + d)
    skills = [s for s in P.get("skills", []) if has([s.lower()], t + " " + d)]
    product = any(p in company.lower() for p in PRODUCT) if company else False

    if remote:
        loc_pts, loc_note = 30, "India-eligible remote (top priority)"
    elif city == "hyderabad":
        loc_pts, loc_note = 27, "Hyderabad"
    else:
        loc_pts, loc_note = 24, "Bengaluru"

    score = min(30, len(skills) * 6) + (30 if fresh else 0) + loc_pts + (10 if product else 0)
    notes = [loc_note,
             "Product company (from your list)" if product else "Company type not confirmed",
             "Fresher wording found" if fresh else "Fresher eligibility not confirmed"]
    if skills:
        notes.append("Profile skill overlap: " + ", ".join(skills[:8]))
    notes.append("Verify graduation year, experience, vacancy status and official page")
    return min(100, score), "; ".join(notes), fresh


def drafts(j, out):
    out.mkdir(parents=True, exist_ok=True)
    a = P["personal"]
    e = P["education"]
    company = j.get("company") or "company"
    title = j.get("title") or "role"
    slug = re.sub(r"[^a-z0-9]+", "-", (company + "-" + title).lower()).strip("-")[:65]
    desc = (j.get("description") or "").lower()
    skills = sorted(P.get("skills", []), key=lambda s: not has([s.lower()], desc))
    resume = [f"# {a['full_name']}",
              f"{a['location']} | {a.get('email', '')} | {a.get('phone', '')}",
              f"LinkedIn: {a.get('linkedin', '')} | GitHub: {a.get('github', '')}",
              "", "## Summary", P.get("summary", ""),
              "", "## Skills", ", ".join(skills), "", "## Projects"]
    for x in P.get("projects", []):
        resume += [f"### {x['name']}", x["description"]]
    resume += ["", "## Education", f"{e['degree']} — {e['college']}",
               f"Graduation: {e['graduation_year']} | CGPA: {e.get('cgpa', '')}",
               "", "## Certifications"]
    resume += ["- " + x for x in P.get("certifications", [])]

    projs = ", ".join(x["name"] for x in P.get("projects", [])[:4])
    top = ", ".join(skills[:4])
    cover = (f"Dear Hiring Team,\n\nI am applying for the {title} role at {company}. "
             f"I am a {e['graduation_year']} {e['degree']} graduate"
             + (f" with hands-on skills in {top}" if top else "")
             + (f". My projects include {projs}" if projs else "")
             + ". I would welcome the opportunity to contribute and learn.\n\n"
             f"Regards,\n{a['full_name']}\n")
    rp = out / (slug + "-resume.md")
    cp = out / (slug + "-cover-letter.txt")
    rp.write_text("\n".join(resume), encoding="utf-8")
    cp.write_text(cover, encoding="utf-8")
    return str(rp), str(cp)
