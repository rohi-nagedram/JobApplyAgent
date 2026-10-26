import json, re, urllib.request, html, xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote
ROOT=Path(__file__).resolve().parents[1]
UA='JobApplyAgent/1.1 (personal job-search; public listings reader)'
def fetch_text(url, accept='application/json'):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':accept})
    with urllib.request.urlopen(req,timeout=20) as r: return r.read().decode('utf-8','replace')
def get(url): return json.loads(fetch_text(url))
def clean(x): return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',str(x or '')))).strip()
def norm(title,company,loc,url,desc,source,date='',workplace='',employment_type=''):
    return {'title':clean(title),'company':clean(company),'location':clean(loc),'url':clean(url),'description':clean(desc),'source':source,'posted_date':clean(date),'workplace':clean(workplace),'employment_type':clean(employment_type)}
def fetch_all():
    cfg=json.loads((ROOT/'boards.json').read_text()); jobs=[]; errors=[]
    def record(label, fn):
        try: jobs.extend(fn())
        except Exception as e: errors.append(f'{label}: {type(e).__name__}: {e}')
    for token in cfg.get('greenhouse_board_tokens',[]):
        def gh(token=token):
            data=get(f'https://boards-api.greenhouse.io/v1/boards/{quote(token)}/jobs?content=true')
            return [norm(j.get('title'),token,(j.get('location') or {}).get('name'),j.get('absolute_url'),j.get('content'),'Greenhouse',j.get('updated_at',''),employment_type='') for j in data.get('jobs',[])]
        record('Greenhouse '+token,gh)
    for site in cfg.get('lever_sites',[]):
        def lever(site=site):
            data=get(f'https://api.lever.co/v0/postings/{quote(site)}?mode=json')
            out=[]
            for j in data if isinstance(data,list) else []:
                c=j.get('categories') or {}
                out.append(norm(j.get('text'),site,c.get('location'),j.get('hostedUrl'),(j.get('descriptionPlain','')+' '+j.get('additionalPlain','')),'Lever',j.get('createdAt',''),j.get('workplaceType',''),c.get('commitment','')))
            return out
        record('Lever '+site,lever)
    for board in cfg.get('ashby_board_names',[]):
        def ashby(board=board):
            data=get(f'https://api.ashbyhq.com/posting-api/job-board/{quote(board)}')
            out=[]
            for j in data.get('jobs',[]):
                if j.get('isListed') is False: continue
                addr=j.get('address') or {}; postal=addr.get('postalAddress') or {}
                loc=postal.get('addressLocality') or j.get('location') or ''
                if postal.get('addressCountry'): loc += ', '+postal['addressCountry']
                out.append(norm(j.get('title'),j.get('companyName') or board,loc,j.get('jobUrl') or j.get('applyUrl'),j.get('descriptionPlain') or j.get('descriptionHtml'),'Ashby',j.get('publishedAt',''),'Remote' if j.get('isRemote') else '',j.get('employmentType','')))
            return out
        record('Ashby '+board,ashby)
    # Public remote feeds. Preserve the source URL and source attribution in each record.
    if cfg.get('enable_remotive',True):
        def remotive():
            data=get('https://remotive.com/api/remote-jobs?category=software-dev')
            return [norm(j.get('title'),j.get('company_name'),j.get('candidate_required_location'),j.get('url'),j.get('description'),'Remotive',j.get('publication_date',''),'Remote',j.get('job_type','')) for j in data.get('jobs',[])]
        record('Remotive remote API',remotive)
    if cfg.get('enable_jobicy',True):
        def jobicy():
            data=get('https://jobicy.com/api/v2/remote-jobs?count=50&tag=software')
            return [norm(j.get('jobTitle'),j.get('companyName'),j.get('jobGeo'),j.get('url'),j.get('jobDescription'),'Jobicy',j.get('pubDate',''),'Remote',j.get('jobType','')) for j in data.get('jobs',[])]
        record('Jobicy remote API',jobicy)
    if cfg.get('enable_remoteok',True):
        def remoteok():
            data=get('https://remoteok.com/api')
            return [norm(j.get('position'),j.get('company'),j.get('location') or 'Worldwide Remote',j.get('url') or ('https://remoteok.com/remote-jobs/'+str(j.get('id',''))),j.get('description'),'RemoteOK',j.get('date',''),'Remote',j.get('job_type','')) for j in data if isinstance(j,dict) and j.get('position') and j.get('id')]
        record('RemoteOK API',remoteok)
    if cfg.get('enable_wwr',True):
        def wwr():
            root=ET.fromstring(fetch_text('https://weworkremotely.com/remote-jobs.rss','application/rss+xml, application/xml, text/xml'))
            out=[]
            for item in root.findall('.//item'):
                out.append(norm(item.findtext('title'), 'We Work Remotely', 'Remote; eligibility varies', item.findtext('link'), item.findtext('description'), 'We Work Remotely RSS', item.findtext('pubDate',''), 'Remote'))
            return out
        record('We Work Remotely RSS',wwr)
    return jobs,errors
