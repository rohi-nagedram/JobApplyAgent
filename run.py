import csv,json
from datetime import datetime,timezone
from pathlib import Path
from jobapply.sources import fetch_all
from jobapply.matching import evaluate,drafts
ROOT=Path(__file__).resolve().parent; D=ROOT/"data"; D.mkdir(exist_ok=True)
def main():
 raw,errors=fetch_all(); seen=set(); out=[]
 for j in raw:
  url=j.get("url","").rstrip("/"); key=url.lower()
  if not key or key in seen:continue
  seen.add(key); score,note,fresh=evaluate(j)
  if score<25:continue
  j.update(match_score=score,review_notes=note,fresher_wording=fresh,checked_at_utc=datetime.now(timezone.utc).isoformat())
  out.append(j)
 out.sort(key=lambda x:(x["match_score"],x.get("posted_date","")),reverse=True)
 fields=["match_score","fresher_wording","title","company","location","workplace","posted_date","source","url","review_notes","checked_at_utc","description"]
 with (D/"jobs.csv").open("w",newline="",encoding="utf-8-sig") as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(out)
 (D/"jobs.json").write_text(json.dumps(out,indent=2,ensure_ascii=False))
 (D/"source-errors.txt").write_text("\\n".join(errors) if errors else "No source errors recorded.")
 queue=[]
 for j in out[:20]:
  r,c=drafts(j,D/"prepared")
  queue.append({"company":j["company"],"title":j["title"],"url":j["url"],"score":j["match_score"],"resume_draft":r,"cover_letter_draft":c,"approval":"REVIEW_REQUIRED","status":"NOT_SUBMITTED"})
 (D/"approval_queue.json").write_text(json.dumps(queue,indent=2))
 tracker=D/"applications.csv"
 if not tracker.exists():tracker.write_text("date_found,company,job_title,job_url,resume_file,cover_letter_file,status,date_applied,deadline,notes\\n")
 print(f"Fetched {len(raw)} listings; {len(out)} passed keyword scoring; {len(errors)} source errors.")
 print("No applications submitted. Review official links and draft assets in data/prepared/.") 
if __name__=="__main__":main()
