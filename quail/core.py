# quail/core.py
from __future__ import annotations
from typing import Any, Dict, Callable, Optional, List, Iterable, Tuple
import functools
import time
import sys
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker

# --- Registries ----------------------------------------------------------------

_TASKS: Dict[str, Callable] = {}
_CHECKS: Dict[str, Callable] = {}

# --- Data types ----------------------------------------------------------------

class CheckResult:
    def __init__(
        self,
        id: str,
        status: str,                 # "running" | "pass" | "fail" | "error" | "skip"
        severity: str = "error",
        metrics: Dict[str, Any] = None,
        description: str | None = None,
        error: str | None = None,
        started_at: float | None = None,
        finished_at: float | None = None,
    ):
        self.id = id
        self.status = status
        self.severity = severity
        self.metrics = metrics or {}
        self.description = description
        self.error = error
        self.started_at = started_at or time.time()
        self.finished_at = finished_at or time.time()

# --- Context -------------------------------------------------------------------

class QContext:
    def __init__(self, env: Dict[str, Any], params: Dict[str, Any], workdir: str = ".quail"):
        self.env = env
        self.params = params
        self.artifacts: Dict[str, Any] = {}
        self.workdir = workdir

    def put(self, k: str, v: Any) -> None:
        self.artifacts[k] = v

    def get(self, k: str, default: Any = None) -> Any:
        # allow a default to be provided
        return self.artifacts.get(k, default)

    def has(self, k: str) -> bool:
        return k in self.artifacts

# --- Decorators ----------------------------------------------------------------

def qtask(id: str | None = None, requires: Optional[List[str]] = None):
    """
    Register a producer step. Its return value is auto-saved in ctx[id].
    If it returns a dict, those keys are also merged into ctx for convenience.
    If ctx already has a value for this id, the function is not re-run.
    """
    requires = requires or []
    def deco(fn):
        rid = id or fn.__name__

        @functools.wraps(fn)
        def wrapper(ctx: QContext):
            # Idempotence: if we already have the artifact, return it
            if ctx.has(rid):
                return ctx.get(rid)
            # Execute user task
            result = fn(ctx)
            # Always store result under the task id
            ctx.put(rid, result)
            # If mapping, merge into ctx for convenient downstream ctx.get("key")
            if isinstance(result, dict):
                for k, v in result.items():
                    ctx.put(k, v)
            return result

        wrapper.__qmeta__ = {"id": rid, "requires": requires, "type": "task"}
        _TASKS[rid] = wrapper
        return wrapper
    return deco

def qcheck(id: str | None = None, requires: Optional[List[str]] = None, severity: str = "error"):
    """
    Register a check. Ensures timing fields and metadata. The CheckResult is
    also cached into ctx[id] for introspection by later nodes or reporting.
    """
    requires = requires or []
    def deco(fn):
        rid = id or fn.__name__

        @functools.wraps(fn)
        def wrapper(ctx: QContext) -> CheckResult:
            start = time.time()
            try:
                # Run user check
                res: CheckResult = fn(ctx)
                # Ensure timing/metadata
                res.started_at = res.started_at or start
                res.finished_at = res.finished_at or time.time()
                res.id = res.id or rid
                res.severity = res.severity or severity
                # Auto-cache the check result
                ctx.put(rid, res)
                return res
            except Exception as e:
                err = CheckResult(
                    id=rid, status="error", severity=severity,
                    error=str(e), started_at=start, finished_at=time.time()
                )
                # Cache the error result too
                ctx.put(rid, err)
                return err

        wrapper.__qmeta__ = {"id": rid, "requires": requires, "type": "check", "severity": severity}
        _CHECKS[rid] = wrapper
        return wrapper
    return deco

# --- Introspection -------------------------------------------------------------

def list_nodes() -> Dict[str, List[str]]:
    return {"tasks": list(_TASKS.keys()), "checks": list(_CHECKS.keys())}

# --- Runner --------------------------------------------------------------------

class Runner:
    def __init__(
        self,
        env: Dict[str, Any],
        params: Dict[str, Any],
        workdir: str = ".quail",
        max_workers: int = 8,
        progress: bool = True,
        stream = sys.stdout
    ):
        self.env = env
        self.params = params
        self.workdir = workdir
        self.max_workers = max_workers
        self.progress = progress
        self._stream = stream

    def _say(self, msg: str):
        if self.progress:
            print(msg, file=self._stream, flush=True)

    def _topo(self, targets: Iterable[str], graph: Dict[str, Callable]) -> List[str]:
        """
        Simple DFS-based topological order over the combined task/check graph
        using each node's __qmeta__["requires"].
        """
        seen, out = set(), []

        def visit(n: str):
            if n in seen:
                return
            for d in graph[n].__qmeta__["requires"]:
                if d not in graph:
                    raise KeyError(f"Unknown dependency '{d}' required by '{n}'")
                visit(d)
            seen.add(n)
            out.append(n)

        for t in targets:
            if t not in graph:
                raise KeyError(f"Unknown node/target: {t}")
            visit(t)
        return out

    def run(self, targets: Iterable[str], parallel: bool = False) -> Dict[str, Tuple[str, Any]]:
        """
        Executes the targets (tasks and/or checks) after computing a topo order
        over their transitive requires. Sequential execution with progress logs.
        """
        if parallel:
            # Parallel execution is not implemented in this minimal core.
            self._say("⚠️ parallel=True requested but not implemented; running sequentially.")

        graph = {**_TASKS, **_CHECKS}
        order = self._topo(targets, graph)
        ctx = QContext(env=self.env, params=self.params, workdir=self.workdir)
        results: Dict[str, Tuple[str, Any]] = {}

        # For the summary
        summary_rows: List[Tuple[str, str, str, str, float]] = []  # (name, type, status, severity, ms)
        check_tally = {"pass": 0, "fail": 0, "skip": 0, "error": 0}
        tasks_run = 0

        for n in order:
            fn = graph[n]
            kind = fn.__qmeta__["type"]

            if kind == "task":
                # Task execution (auto-cached by decorator)
                self._say(f"🏃 running: {n} [task]")
                t0 = time.time()
                val = fn(ctx)
                dt = (time.time() - t0) * 1000
                results[n] = ("task", val)
                self._say(f"✅ done: {n} ({dt:.0f} ms)")
                tasks_run += 1
                summary_rows.append((n, "task", "done", "-", dt))

            else:
                # Check execution (auto-cached by decorator)
                self._say(f"🏃 running: {n} [check]")
                start_wall = time.time()
                res: CheckResult = fn(ctx)
                results[n] = ("check", res)

                # Ensure timings are present
                res.started_at = res.started_at or start_wall
                res.finished_at = res.finished_at or time.time()
                dt = (res.finished_at - res.started_at) * 1000

                if res.status == "pass":
                    badge = "✅ PASS"
                elif res.status == "fail":
                    badge = "❌ FAIL"
                elif res.status == "skip":
                    badge = "⏭️ SKIP"
                else:
                    badge = "💥 ERROR"

                metric_snippet = ""
                if isinstance(res.metrics, dict) and res.metrics:
                    items = list(res.metrics.items())[:2]
                    metric_snippet = " " + " ".join([f"{k}={_short(v)}" for k, v in items])

                self._say(f"{badge}: {n} [{res.severity}] ({dt:.0f} ms){metric_snippet}")

                # Tally & record for summary
                check_tally[res.status if res.status in check_tally else "error"] += 1
                summary_rows.append((n, "check", res.status, res.severity, dt))

        # --- Run Summary ----------------------------------------------------
        if self.progress:
            self._say("\n📋 Run summary")
            self._say(
                f"• tasks: {tasks_run} | checks: "
                f"{check_tally['pass']} pass, "
                f"{check_tally['fail']} fail, "
                f"{check_tally['skip']} skip, "
                f"{check_tally['error']} error"
            )
            # Column header
            self._say("─" * 72)
            self._say(f"{'node':30} {'type':6} {'status':8} {'sev':6} {'time(ms)':8}")
            self._say("─" * 72)
            for name, typ, status, sev, ms in summary_rows:
                self._say(f"{name[:30]:30} {typ:6} {status:8} {sev[:6]:6} {ms:8.0f}")
            self._say("─" * 72)

        return results

# --- Utils --------------------------------------------------------------------

def _short(v: Any) -> str:
    s = str(v)
    return s if len(s) <= 80 else s[:77] + "..."

# --- Quail helpers (moved here from prototype) --------------------------------
# Lightweight, optional dependencies: imports happen inside functions.

def load_quail_config(path: str = "quail.yml"):
    """
    Load quail.yml, resolve profile/env/params, expand ${VAR} in params.
    Returns: (cfg, env_cfg, params, targets, default_covey, profile)
    """
    try:
        import os
        import yaml  # type: ignore
    except Exception as e:
        raise RuntimeError("load_quail_config requires PyYAML and os") from e

    with open(path, "r", encoding="utf-8") as f:
        cfg = (yaml.safe_load(f) or {})

    # profile resolution: env var or yaml
    profile = os.environ.get("QUAIL_PROFILE") or cfg.get("profile") or "dev"
    envs = cfg.get("envs") or {}
    env_cfg = envs.get(profile, {})
    params = (cfg.get("params") or {}).copy()

    # expand ${VAR} in string params
    for k, v in list(params.items()):
        if isinstance(v, str):
            params[k] = os.path.expandvars(v)

    targets = cfg.get("targets") or {}
    default_covey = cfg.get("default_covey") or "pricing"
    return cfg, env_cfg, params, targets, default_covey, profile

def build_env_from_orm(orm_cfg: dict):
    """
    Build DB env using the new service-oriented architecture.
    
    Supports both SQL and MongoDB configurations:
    - SQL: {"kind": "sql", "url": "...", "schema": "...", "reflect": [...]}
    - MongoDB: {"kind": "mongo", "url": "...", "database": "..."}
    """
    from .context import ServiceContext
    from .database import SqlDbContext, MongoDbContext
    
    if not isinstance(orm_cfg, dict):
        raise ValueError("envs.<profile>.orm must be a dict")

    kind = orm_cfg.get("kind", "sql").lower()
    
    if kind == "sql":
        # SQL configuration
        url = orm_cfg.get("url")
        if not url:
            raise ValueError("envs.<profile>.orm.url is required for SQL")

        default_schema = orm_cfg.get("schema")
        reflect = orm_cfg.get("reflect", []) or []

        # Create service context with SQL configuration
        service_config = {
            'environment': 'dev',  # Default, can be overridden
            'sql': {
                'url': url,
                'schema': default_schema,
                'engine_options': orm_cfg.get('engine_options', {})
            }
        }
        
        service_context = ServiceContext(service_config)
        
        # Reflect tables if specified
        tables = {}
        registry = {}
        
        if reflect:
            reflection_result = service_context.reflect_tables(reflect)
            # Get the actual table objects from the SQL context
            with service_context.sql_context as db:
                tables = db.tables.copy()
                registry = db.table_registry.copy()

        env = {
            "service_context": service_context,
            "sql_service": service_context.get_sql_service(),
            "schema": default_schema,
            "tables": tables,
            "table_registry": registry,
            "reflect": reflect,  # pass-through for tasks
        }
        
        # Legacy compatibility - expose engine and session_factory
        if service_context.sql_context:
            with service_context.sql_context as db:
                env["engine"] = db.engine
                env["session_factory"] = db._session_factory

    elif kind == "mongo":
        # MongoDB configuration
        url = orm_cfg.get("url")
        database = orm_cfg.get("database")
        
        if not url or not database:
            raise ValueError("envs.<profile>.orm.url and database are required for MongoDB")

        # Create service context with MongoDB configuration
        service_config = {
            'environment': 'dev',  # Default, can be overridden
            'mongo': {
                'url': url,
                'database': database,
                'timeout_minutes': orm_cfg.get('timeout_minutes', 120)
            }
        }
        
        service_context = ServiceContext(service_config)
        
        env = {
            "service_context": service_context,
            "mongo_service": service_context.get_mongo_service(),
            "database": database,
        }
        
        # Legacy compatibility - expose mongo client and db
        if service_context.mongo_context:
            with service_context.mongo_context as db:
                env["mongo_client"] = db.client
                env["mongo_db"] = db.database

    elif kind == "hybrid":
        # Both SQL and MongoDB
        sql_config = orm_cfg.get("sql", {})
        mongo_config = orm_cfg.get("mongo", {})
        
        if not sql_config.get("url") or not mongo_config.get("url"):
            raise ValueError("Both SQL and MongoDB configurations required for hybrid mode")

        service_config = {
            'environment': 'dev',
            'sql': {
                'url': sql_config['url'],
                'schema': sql_config.get('schema'),
                'engine_options': sql_config.get('engine_options', {})
            },
            'mongo': {
                'url': mongo_config['url'], 
                'database': mongo_config['database'],
                'timeout_minutes': mongo_config.get('timeout_minutes', 120)
            }
        }
        
        service_context = ServiceContext(service_config)
        
        # Reflect SQL tables if specified
        tables = {}
        registry = {}
        reflect = sql_config.get("reflect", [])
        
        if reflect:
            reflection_result = service_context.reflect_tables(reflect)
            with service_context.sql_context as db:
                tables = db.tables.copy()
                registry = db.table_registry.copy()

        env = {
            "service_context": service_context,
            "sql_service": service_context.get_sql_service(),
            "mongo_service": service_context.get_mongo_service(),
            "quality_service": service_context.get_quality_service(),
            "report_service": service_context.get_report_service(),
            "schema": sql_config.get('schema'),
            "tables": tables,
            "table_registry": registry,
            "reflect": reflect,
        }

    else:
        raise NotImplementedError(f"ORM kind '{kind}' not supported. Use 'sql', 'mongo', or 'hybrid'")

    return env
# def build_env_from_orm(orm_cfg: dict):
#     """
#     Minimal SQL ORM builder based on YAML block:
#       orm:
#         kind: sql
#         url: postgresql+psycopg2://...
#         schema: raw_data
#         reflect: ["pricing_report"]

#     Returns dict with: engine, session_factory, metadata, tables, schema
#     """
#     try:
#         from sqlalchemy import create_engine, MetaData, Table  # type: ignore
#         from sqlalchemy.orm import sessionmaker  # type: ignore
#     except Exception as e:
#         raise RuntimeError("build_env_from_orm requires SQLAlchemy") from e

#     kind = (orm_cfg or {}).get("kind", "").lower()
#     if kind != "sql":
#         raise SystemExit("Only orm.kind=sql is supported here.")

#     url = orm_cfg.get("url")
#     if not url:
#         raise SystemExit("orm.url is required (e.g., DB_URL env var).")

#     schema = orm_cfg.get("schema")
#     reflect = orm_cfg.get("reflect") or []

#     engine = create_engine(url, pool_pre_ping=True, future=True)
#     Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

#     md = MetaData(schema=schema) if schema else MetaData()
#     tables = {}
#     for name in reflect:
#         t = Table(name, md, schema=schema, autoload_with=engine)
#         key = f"{schema}.{name}" if schema else name
#         tables[key] = t

#     return {
#         "engine": engine,
#         "session_factory": Session,
#         "metadata": md,
#         "tables": tables,
#         "schema": schema,
#     }


def resolve_targets(cfg_targets: dict, default_covey: str, cli_targets: Optional[List[str]]):
    """
    CLI may pass explicit node names/target groups; otherwise use default covey from YAML.
    """
    if cli_targets:
        resolved: List[str] = []
        for t in cli_targets:
            if t in cfg_targets:  # group name (like 'daily')
                resolved.extend(cfg_targets[t])
            else:                 # direct node id
                resolved.append(t)
        return resolved
    return cfg_targets.get(default_covey, [])


__all__ = [
    # core
    "QContext", "CheckResult", "qtask", "qcheck", "Runner", "list_nodes",
    # helpers
    "load_quail_config", "build_env_from_orm", "resolve_targets",
]
