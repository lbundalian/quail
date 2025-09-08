import argparse,sys,os,runpy,yaml,importlib
from .core import Runner,list_nodes
from .orm import build_env_from_cfg

def load_config(path="quail.yml"):
    with open(path) as f: cfg=yaml.safe_load(f) or {}
    profile=os.environ.get("QUAIL_PROFILE") or cfg.get("profile","dev")
    env_cfg=cfg.get("envs",{}).get(profile,{}) 
    params=cfg.get("params",{})
    return cfg,env_cfg,params,profile

def import_trail(cfg,cfg_dir,explicit=None):
    if explicit: importlib.import_module(explicit); return
    if cfg.get("modules"): [importlib.import_module(m) for m in cfg["modules"]]; return
    trail_path=os.path.join(cfg_dir,"Quailtrail")
    if not os.path.isfile(trail_path): sys.exit("No Quailtrail file found")
    runpy.run_path(trail_path,run_name="__quailtrail__")

def cmd_trail(args):
    cfg,env_cfg,params,_=load_config(args.config)
    cfg_dir=os.path.abspath(os.path.dirname(args.config) or ".")
    import_trail(cfg,cfg_dir,args.module)
    env=build_env_from_cfg(env_cfg.get("orm",{}))
    runner=Runner(env,params)
    targets=args.targets or cfg.get("targets",{}).get(cfg.get("default_covey","daily"),[])
    results=runner.run(targets)
    from .reporting.markdown_reporter import print_markdown; print_markdown(results)

def cmd_list(args):
    cfg,_,_,_=load_config(args.config)
    import_trail(cfg,os.path.abspath(os.path.dirname(args.config) or "."),args.module)
    nodes=list_nodes()
    print("# Tasks"); [print("-",n) for n in nodes["tasks"]]
    print("# Checks"); [print("-",n) for n in nodes["checks"]]

def cmd_nest(args):
    open("quail.yml","w").write("project: covey\nprofile: dev\ndefault_covey: daily\n")
    open("Quailtrail","w").write("from quail.core import qtask,qcheck,CheckResult\n@qtask(id='hello')\ndef hello(ctx): return 'hi'\n")

def main():
    p=argparse.ArgumentParser("quail")
    sub=p.add_subparsers(dest="cmd")
    t=sub.add_parser("trail"); t.add_argument("targets",nargs="*"); t.add_argument("--config",default="quail.yml"); t.add_argument("--module"); t.set_defaults(func=cmd_trail)
    l=sub.add_parser("list"); l.add_argument("--config",default="quail.yml"); l.add_argument("--module"); l.set_defaults(func=cmd_list)
    n=sub.add_parser("nest"); n.set_defaults(func=cmd_nest)
    if len(sys.argv)>1 and sys.argv[1] not in {"trail","list","nest"}: sys.argv.insert(1,"trail")
    args=p.parse_args(); 
    if not getattr(args,"func",None): p.print_help(); sys.exit(0)
    args.func(args)
