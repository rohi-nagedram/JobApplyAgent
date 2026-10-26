JOBAPPLYAGENT CORRECTION PATCH

Replace these files in your existing repository, keeping the same folders:
- run.py -> repository root/run.py
- jobapply/matching.py -> repository root/jobapply/matching.py
- .github/workflows/daily.yml -> repository root/.github/workflows/daily.yml

Then commit the changes and run the GitHub Actions workflow manually. Download the artifact and inspect jobs.csv, excluded_jobs.csv, source-errors.txt, approval_queue.json and data/prepared/.

Important limitations:
- This patch corrects title/role/location filtering and improves draft organization. It does not add new source adapters; the existing Greenhouse/Lever board list remains in boards.json.
- Public board feeds often omit employment type. To avoid falsely claiming full-time is confirmed, retained jobs are marked VERIFY_ON_OFFICIAL_PAGE. The filter excludes obvious internships, co-ops, contract, temporary and part-time wording but cannot prove every remaining job is full-time.
- Fresher eligibility is not guaranteed by a score. Check official job requirements before applying.
- Resume tailoring is rule/keyword-based and uses only existing profile data. Review every draft and remove any inaccurate statement.
- No application forms are filled and no applications are submitted. Approval queue is for manual review only.
- Edit profile.json first; replace EDIT_ME fields and remove or correct anything that is not accurate.
