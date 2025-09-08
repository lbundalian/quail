from typing import Dict, Any

def build_env_from_cfg(cfg: Dict[str,Any])->Dict[str,Any]:
    kind=(cfg.get("kind") or "").lower()
    if kind=="sql":
        from sqlalchemy import create_engine, MetaData, Table
        from sqlalchemy.orm import sessionmaker
        url=cfg.get("url"); schema=cfg.get("schema")
        engine=create_engine(url) if url else None
        Session=sessionmaker(bind=engine) if engine else None
        md=MetaData(schema=schema)
        tables={}
        for name in cfg.get("reflect") or []:
            tables[f"{schema}.{name}"]=Table(name,md,schema=schema,autoload_with=engine)
        return {"engine":engine,"session_factory":Session,"metadata":md,"tables":tables}
    if kind=="mongo":
        from pymongo import MongoClient
        url=cfg.get("url"); dbn=cfg.get("database")
        client=MongoClient(url) if url else None
        db=client[dbn] if client and dbn else None
        return {"mongo_client":client,"mongo_db":db,"get_collection":(lambda n: db[n])}
    return {}
