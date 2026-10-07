import pathlib,os,stat,fcntl,hashlib,tarfile,json,shutil,sys
R=pathlib.Path(os.environ.get('VALORA_TEST_ROOT','/opt/valora-www-preview-dentist'))
B=pathlib.Path(os.environ.get('VALORA_TEST_BUNDLE','/tmp/first-meeting-bounded-overlay.tgz'))
C=R/'current';N=R/'releases/consumer-oct7-first-meeting-art-word-v1';K=R/'current-before-first-meeting-art-word-v1';TMP=R/'current-first-meeting-art-word.tmp'
PAGE='find-a-financial-advisor/prepare-first-financial-advisor-meeting/index.html'
BASE='059095e44cabe4e3ad670612e49cc2a3aee65c1f1f83c8aaa3366a4fad838e99';OUT='8912741fdf10da79e0f9bc296d9d0d7b2e476bf9290b162692e7191299e12472'
def h(b):return hashlib.sha256(b).hexdigest()
def ex(p):return os.path.lexists(p)
def inv(r):
 out={}
 for parent,dirs,files in os.walk(r,followlinks=False):
  for n in dirs+files:
   p=pathlib.Path(parent)/n;assert not p.is_symlink(),str(p)
   assert p.is_dir() or stat.S_ISREG(p.lstat().st_mode),str(p)
   if p.is_file():out[p.relative_to(r).as_posix()]=h(p.read_bytes())
 return out
def target(c):
 assert c.is_symlink();raw=os.readlink(c);p=pathlib.PurePosixPath(raw);assert len(p.parts)==2 and p.parts[0]=='releases' and '..' not in p.parts
 out=R/raw;assert out.is_dir() and not out.is_symlink();return out
mode=sys.argv[1];assert mode in ['preflight','apply','rollback']
fd=os.open(R/'.release.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
with os.fdopen(fd,'r+') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);prior=target(C)
 if mode=='rollback':
  assert prior==N and not ex(TMP);old=target(K);os.symlink(os.path.relpath(old,R),TMP);assert target(C)==N;os.replace(TMP,C);print('ROLLED_BACK',old);sys.exit(0)
 assert prior.name=='consumer-oct7-tech-art-v1';before=inv(prior);assert len(before)==481
 normalized='\n'.join(sorted(v+'  '+k for k,v in before.items()))+'\n'
 assert h(normalized.encode())=='5388bf607ce1dadce386712b1cf513ca4ec9bc7a27adc4f9b71a009672f134f0','TREE_DRIFT'
 assert before[PAGE]==BASE and h(B.read_bytes())=='61198bb4d7bbfdbb7de95e99f9ba8ee179c9ae6db5e64639d1f34bc3c01a651d'
 assert not any(ex(p)for p in [N,K,TMP])
 with tarfile.open(B)as t:
  ms=t.getmembers();assert len(ms)==9 and all(m.isfile() for m in ms);names=[m.name for m in ms];assert len(set(names))==9
  allowed={'figure-delta.json','sentence-diff.json','SHA256.json'}|{'assets/first-meeting-restored-'+n+'-v1.webp'for n in ['hero','hero-mobile','brief','brief-mobile','next-step','next-step-mobile']};assert set(names)==allowed
  data={n:t.extractfile(n).read()for n in names};checks=json.loads(data['SHA256.json']);assert set(checks)==allowed-{'SHA256.json'}
  assert all(h(data[n])==v for n,v in checks.items())
  reviewed={'assets/first-meeting-restored-hero-v1.webp': '39603c5c8522b67f3736d2c5ebf6e39ab7247fc9b861df0b49a86e7bea82e576', 'assets/first-meeting-restored-hero-mobile-v1.webp': '7833f1022ba8e0b8627fca1068d8e5341084e1a791a58ff1531458a58b49e2fe', 'assets/first-meeting-restored-brief-v1.webp': 'af9fce8ee60e12ec4242be59959200996078a3e932145ff9fc397275efcba5ec', 'assets/first-meeting-restored-brief-mobile-v1.webp': '899123f94d9bb295478c540363761a5bf071e492f63f326aa3c9d7be42fb345d', 'assets/first-meeting-restored-next-step-v1.webp': '41a348b0c924c5bc637da2c70aff66143303bb5ec7cb8438d25afd1390892fd2', 'assets/first-meeting-restored-next-step-mobile-v1.webp': '869e2cba64b15e003a9026a9077776d3e32c413c07b39afa228d5e8197bc6a19'}
  assert all(h(data[n])==v for n,v in reviewed.items()),'ZARA_ART_HASH_MISMATCH'
  d=json.loads(data['figure-delta.json']);s=json.loads(data['sentence-diff.json']);assert len(d)==3 and s['before']=='It does not guarantee a fit or outcome.' and s['after']=='It does not ensure a fit or outcome.'
 original=(prior/PAGE).read_bytes();out=original
 for x in d+[s]:
  a=x['before'].encode();b=x['after'].encode();assert out.count(a)==1;out=out.replace(a,b)
 assert len(out)==42213 and h(out)==OUT
 rev=out
 for x in reversed(d+[s]):assert rev.count(x['after'].encode())==1;rev=rev.replace(x['after'].encode(),x['before'].encode())
 assert rev==original
 content={PAGE:out}
 for n in allowed:
  if n.startswith('assets/'):
   dest='assets/prepare-first-financial-advisor-meeting/'+n.split('/')[-1];assert dest not in before;content[dest]=data[n]
 assert len(content)==7
 print('PREFLIGHT_OK',prior,'481 baseline unchanged; 1 HTML change + 6 assets; four substitutions reversible',flush=True)
 if mode=='preflight':sys.exit(0)
 try:
  shutil.copytree(prior,N,symlinks=False)
  for n,b in content.items():p=N/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
  expected=dict(before);expected.update({n:h(b)for n,b in content.items()});after=inv(N);assert after==expected and len(after)==487
  assert target(C)==prior and inv(prior)==before and not ex(K) and not ex(TMP)
  os.symlink(os.path.relpath(prior,R),K);os.symlink(os.path.relpath(N,R),TMP);assert target(C)==prior;os.replace(TMP,C);assert target(C)==N
  print(json.dumps({'status':'APPLIED','release':str(N),'prior':str(prior),'unchanged_old_paths':480,'new_files':6,'total':487,'target_bytes':len(out),'target_sha256':OUT,'changes':{n:h(b)for n,b in content.items()}},sort_keys=True))
 except BaseException:
  if target(C)==prior:
   if ex(TMP):TMP.unlink()
   if ex(K):K.unlink()
   if N.exists():shutil.rmtree(N)
  raise
