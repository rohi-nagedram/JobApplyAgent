import json,re,urllib.request,html
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
UA="JobApplyAgent/1.0 public job listing reader"
def get(url):
 req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=15) as r:return json.loads(r.read().decode("utf-8","replace"))
def clean(x):return re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",str(x or "")))).strip()
def norm(title,company,loc,url,desc,source,date="",workplace=""):
 return {"title":clean(title),"company":clean(company),"location":clean(loc),"url":clean(url),"description":clean(desc),"source":source,"posted_date":clean(date),"workplace":clean(workplace)}
def fetch_all():
 cfg=json.loads((ROOT/"boards.json").read_text()); jobs=[]; errors=[]
 for token in cfg["greenhouse_board_tokens"]:
  try:
   for j in get(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true").get("jobs",[]):
    jobs.append(norm(j.get("title"),token,(j.get("location") or {}).get("name"),j.get("absolute_url"),j.get("content"),"Greenhouse",j.get("updated_at","")))
  except Exception as e:errors.append(f"Greenhouse {token}: {type(e).__name__}: {e}")
 for site in cfg["lever_sites"]:
  try:
   data=get(f"https://api.lever.co/v0/postings/{site}?mode=json")
   for j in data if isinstance(data,list) else []:
    c=j.get("categories") or {}
    jobs.append(norm(j.get("text"),site,c.get("location"),j.get("hostedUrl"),(j.get("descriptionPlain","")+" "+j.get("additionalPlain","")),"Lever",j.get("createdAt",""),j.get("workplaceType","")))
  except Exception as e:errors.append(f"Lever {site}: {type(e).__name__}: {e}")
 return jobs,errors
