"""Save cumulative source changes, regression files, and validate clean-base application."""
import io,json,shutil,subprocess,tarfile,tempfile
from pathlib import Path
root=Path.cwd();upstream=root/'upstream'
assert (root/'llms.txt').read_bytes()==(upstream/'app/llms.txt').read_bytes(), 'Agent guides must match'
patch=subprocess.check_output(['git','diff','--binary'],cwd=upstream)
new_files=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=upstream,text=True).splitlines()
for name in new_files:
    if name.startswith('tests/'):continue
    result=subprocess.run(['git','diff','--no-index','--binary','--','/dev/null',name],cwd=upstream,stdout=subprocess.PIPE)
    assert result.returncode in [0,1]
    patch+=result.stdout
(root/'verification/repairs.patch').write_bytes(patch)
regression=root/'verification/regression-tests'
shutil.copytree(upstream/'tests',regression,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache','*.pyc'))
archive=subprocess.check_output(['git','archive','HEAD'],cwd=upstream)
with tempfile.TemporaryDirectory(prefix='social-trends-patch-') as directory:
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:tar.extractall(directory,filter='data')
    subprocess.run(['git','apply','--check',str(root/'verification/repairs.patch')],cwd=directory,check=True)
    subprocess.run(['git','apply',str(root/'verification/repairs.patch')],cwd=directory,check=True)
    for name in [name for name in new_files if not name.startswith('tests/')]:
        assert Path(directory,name).read_bytes()==Path(upstream,name).read_bytes()
result={'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=upstream,text=True).strip(),'clean_base_apply':True,'new_source_files':[x for x in new_files if not x.startswith('tests/')]}
(root/'verification/patch-validation.json').write_text(json.dumps(result,indent=2))
print('PASS: cumulative patch applies to pristine upstream, including all new source modules; regression files saved.')
