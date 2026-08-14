"""Explicit, observable tools for the YasinCoder coding agent."""
from __future__ import annotations
import difflib, os, subprocess
from pathlib import Path
from typing import Iterable
from config import PROJECT_PATH
class ToolError(RuntimeError): pass
def _workspace(root=None): return Path(root or PROJECT_PATH).expanduser().resolve()
def safe_path(path, root=None):
    w=_workspace(root); p=Path(path).expanduser(); p=w/p if not p.is_absolute() else p; p=p.resolve()
    try: p.relative_to(w)
    except ValueError as exc: raise ToolError("path escapes configured workspace") from exc
    return p
def result(ok,tool,**data): return {"ok":ok,"tool":tool,**data}
def workspace_info(root=None):
    w=_workspace(root); return result(True,"workspace.info",path=str(w),exists=w.exists())
def read_file(path,root=None):
    p=safe_path(path,root)
    if not p.is_file(): return result(False,"file.read",error="file not found",path=str(p))
    return result(True,"file.read",path=str(p),content=p.read_text(encoding="utf-8"))
def write_file(path,content,*,apply=False,root=None):
    p=safe_path(path,root); old=p.read_text(encoding="utf-8") if p.exists() else ""; patch="".join(difflib.unified_diff(old.splitlines(keepends=True),content.splitlines(keepends=True),fromfile=str(p),tofile=str(p)))
    if not apply: return result(True,"file.write",applied=False,path=str(p),patch=patch)
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(content,encoding="utf-8"); return result(True,"file.write",applied=True,path=str(p),patch=patch)
def search(pattern,*,root=None,paths:Iterable[str]|None=None):
    w=_workspace(root); cmd=["rg","--line-number","--no-heading",pattern]; cmd.extend(str(safe_path(p,w)) for p in paths) if paths else cmd.append(str(w))
    try: proc=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
    except FileNotFoundError:
        import re; rx=re.compile(pattern); matches=[]
        for f in w.rglob("*"):
            if not f.is_file() or ".git" in f.parts: continue
            try: matches += [f"{f}:{n}:{line}" for n,line in enumerate(f.read_text(encoding="utf-8").splitlines(),1) if rx.search(line)]
            except (UnicodeDecodeError,OSError): pass
        return result(True,"search",backend="python",matches=matches)
    return result(proc.returncode in (0,1),"search",backend="ripgrep",matches=proc.stdout.splitlines(),error=proc.stderr or None)
def shell(command,*,root=None,timeout=60):
    p=subprocess.run(command,shell=True,cwd=_workspace(root),capture_output=True,text=True,timeout=timeout); return result(p.returncode==0,"shell.exec",command=command,stdout=p.stdout,stderr=p.stderr,returncode=p.returncode)
def git(args:list[str],*,root=None,timeout=60):
    p=subprocess.run(["git",*args],cwd=_workspace(root),capture_output=True,text=True,timeout=timeout); return result(p.returncode==0,"git.exec",args=args,stdout=p.stdout,stderr=p.stderr,returncode=p.returncode)
def test(command="python -m pytest",*,root=None,timeout=300):
    r=shell(command,root=root,timeout=timeout); r["tool"]="test.run"; return r
def execute(name,payload=None):
    tools={"workspace.info":workspace_info,"file.read":read_file,"file.write":write_file,"search":search,"shell.exec":shell,"git.exec":git,"test.run":test}
    if name not in tools: return result(False,name,error="unknown tool")
    try: return tools[name](**(payload or {}))
    except (ToolError,OSError,subprocess.SubprocessError,ValueError) as exc: return result(False,name,error=str(exc))
