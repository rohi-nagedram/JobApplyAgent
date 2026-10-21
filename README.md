# JobApplyAgent — free starter

Python standard library + GitHub Actions. Targets 2026 B.Tech CSE fresher roles in India.

## Included
- Public Greenhouse and Lever job-board fetchers (configurable list in `boards.json`)
- Duplicate removal, keyword score and basic entry-level/location flags
- CSV/JSON reports and source-error log
- Tailored Markdown resume and cover-letter drafts for the top 20 matches based on `profile.json`
- Approval queue explicitly marked `REVIEW_REQUIRED` and `NOT_SUBMITTED`
- Daily scheduled run and manual trigger

## Honest limitations
- Does not search literally every company; add verified board tokens/site slugs to `boards.json`.
- Keyword scores do not prove vacancy status or fresher eligibility. Verify each official job page.
- Drafts are Markdown, not PDF. Review every line, especially profile fields marked `EDIT_ME`.
- It does not fill or submit application forms. Many ATS application endpoints require employer-side credentials; candidate approval alone does not grant API access. This version never submits applications.
- No portal passwords, OTPs, paid APIs, or paid hosting are needed.

## Android setup
1. Download and extract the ZIP.
2. Create a GitHub repo named `job-apply-agent`.
3. Upload all files preserving `.github/workflows/daily.yml`.
4. Edit `profile.json`: replace `EDIT_ME`, verify every skill/project/experience statement, and remove anything inaccurate.
5. Open Actions, enable workflows, then run **Daily Job Search and Resume Drafts** manually.
6. Download the artifact from the completed run. Check `jobs.csv`, `source-errors.txt`, `approval_queue.json`, and `data/prepared/`.

Scheduled time: 02:30 UTC, approximately 08:00 IST; GitHub may delay it. Free usage is subject to GitHub's current plan limits.

## Local run (optional)
Python 3.10+: `python run.py`. Internet access is required.
