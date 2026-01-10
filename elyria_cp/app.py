"""
elyria_cp/app.py — Elyria Control Plane (bells + whistles) + Intelligence Lair

Run:
  python -m elyria_cp.app --help
  python -m elyria_cp.app config
  python -m elyria_cp.app stats --hide-top 0
  python -m elyria_cp.app lair status
  python -m elyria_cp.app lair gate "elyria rise"
  python -m elyria_cp.app lair layer "gate open"

Store path:
  - If ELYRIA_CP_NODESTORE points to a directory -> <dir>/nodes.jsonl
  - If it points to a file -> that file
  - Otherwise defaults to: <package_dir>/nodes.jsonl
"""

import csv
import importlib
import json
import os
import re
import sys
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import typer

app = typer.Typer(add_completion=False, no_args_is_help=True)
lair = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(lair, name="lair")


# ----------------------------
# Store resolution + locking
# ----------------------------

def _resolve_store_path() -> Path:
    env = os.getenv("ELYRIA_CP_NODESTORE")
    if env:
        p = Path(env).expanduser().resolve()
        # If env is a directory or ends with / -> treat as directory
        if (p.exists() and p.is_dir()) or str(env).endswith(("/", "\\")):
            return (p / "nodes.jsonl").resolve()
        return p

    here = Path(__file__).resolve().parent
    return (here / "nodes.jsonl").resolve()


NODES_PATH = _resolve_store_path()


def _ensure_parent_dir(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


class _FileLock:
    """Best-effort lock (works on Linux)."""
    def __init__(self, lock_path: Path):
        self.lock_path = lock_path
        self._fh = None

    def __enter__(self):
        _ensure_parent_dir(self.lock_path)
        self._fh = self.lock_path.open("a+", encoding="utf-8")
        try:
            import fcntl  # type: ignore
            fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX)
        except Exception:
            pass
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._fh:
            try:
                import fcntl  # type: ignore
                fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass
            try:
                self._fh.close()
            except Exception:
                pass


def _lockfile_for(store: Path) -> Path:
    return store.with_suffix(store.suffix + ".lock")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(ts: str) -> Optional[datetime]:
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except Exception:
        return None


# ----------------------------
# Nodes: load / append / write / repair
# ----------------------------

def _node_text(n: Any) -> str:
    if isinstance(n, str):
        return n
    if isinstance(n, dict):
        for k in ("text", "content", "message", "prompt", "raw", "input"):
            v = n.get(k)
            if isinstance(v, str) and v.strip():
                return v
        return json.dumps(n, ensure_ascii=False, default=str)
    return str(n)


def load_nodes(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    p = (path or NODES_PATH).expanduser().resolve()
    if not p.exists():
        return []

    nodes: List[Dict[str, Any]] = []
    try:
        with p.open("r", encoding="utf-8") as f:
            # Detect JSON array vs JSONL
            first_nonws = ""
            while True:
                ch = f.read(1)
                if not ch:
                    break
                if not ch.isspace():
                    first_nonws = ch
                    break
            if not first_nonws:
                return []
            f.seek(0)

            if first_nonws == "[":
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            nodes.append(item)
                        else:
                            nodes.append({"id": str(uuid.uuid4()), "ts": _utc_now_iso(), "text": str(item)})
                return nodes

            # JSONL
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if isinstance(obj, dict):
                        nodes.append(obj)
                    else:
                        nodes.append({"id": str(uuid.uuid4()), "ts": _utc_now_iso(), "text": str(obj)})
                except json.JSONDecodeError:
                    nodes.append({"id": str(uuid.uuid4()), "ts": _utc_now_iso(), "text": line, "parse_error": True})

        return nodes
    except Exception:
        return []


def append_node(node: Dict[str, Any], path: Optional[Path] = None) -> None:
    p = (path or NODES_PATH).expanduser().resolve()
    _ensure_parent_dir(p)

    # Normalize minimal schema
    node = dict(node)
    node.setdefault("id", str(uuid.uuid4()))
    node.setdefault("ts", _utc_now_iso())
    node.setdefault("text", _node_text(node))

    lock = _lockfile_for(p)
    with _FileLock(lock):
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(node, ensure_ascii=False) + "\n")


def write_nodes(nodes: List[Dict[str, Any]], path: Optional[Path] = None) -> None:
    p = (path or NODES_PATH).expanduser().resolve()
    _ensure_parent_dir(p)
    lock = _lockfile_for(p)
    with _FileLock(lock):
        with p.open("w", encoding="utf-8") as f:
            for n in nodes:
                if not isinstance(n, dict):
                    n = {"id": str(uuid.uuid4()), "ts": _utc_now_iso(), "text": str(n)}
                if not n.get("id"):
                    n["id"] = str(uuid.uuid4())
                if not n.get("ts"):
                    n["ts"] = _utc_now_iso()
                if "text" not in n:
                    n["text"] = _node_text(n)
                f.write(json.dumps(n, ensure_ascii=False) + "\n")


def doctor_repair(path: Optional[Path] = None) -> Tuple[int, int]:
    p = (path or NODES_PATH).expanduser().resolve()
    if not p.exists():
        return (0, 0)

    kept: List[Dict[str, Any]] = []
    dropped = 0
    try:
        with p.open("r", encoding="utf-8") as f:
            first_nonws = ""
            while True:
                ch = f.read(1)
                if not ch:
                    break
                if not ch.isspace():
                    first_nonws = ch
                    break
            f.seek(0)

            if first_nonws == "[":
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            kept.append(item)
                        else:
                            kept.append({"id": str(uuid.uuid4()), "ts": _utc_now_iso(), "text": str(item)})
                else:
                    dropped += 1
            else:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        if isinstance(obj, dict):
                            kept.append(obj)
                        else:
                            kept.append({"id": str(uuid.uuid4()), "ts": _utc_now_iso(), "text": str(obj)})
                    except Exception:
                        dropped += 1

        write_nodes(kept, p)
        return (len(kept), dropped)
    except Exception:
        return (0, 0)


# ----------------------------
# Stats / themes
# ----------------------------

STOP_BASE = {
    "a","an","the","and","or","but","if","then","so","to","of","in","on","for","with",
    "is","are","was","were","be","been","being","this","that","these","those","it","its",
    "i","you","we","they","he","she","them","us","my","your","our","their","as","at","by"
}

def _tokenize(text: str, *, extra_stop: Optional[set] = None, min_len: int = 3) -> List[str]:
    words = re.findall(r"[a-z0-9']+", (text or "").lower())
    cleaned: List[str] = []
    for w in words:
        if len(w) < min_len:
            continue
        if w in STOP_BASE:
            continue
        if extra_stop and w in extra_stop:
            continue
        if w.isdigit():
            continue
        # Drop alphabet-run test strings (full or partial)
        if w.isalpha() and len(w) >= 10:
            if len(set(w)) / len(w) > 0.8:
                continue
        cleaned.append(w)
    return cleaned

def _bigrams(words: List[str]) -> List[str]:
    out: List[str] = []
    for i in range(len(words) - 1):
        a, b = words[i], words[i + 1]
        if a == b:
            continue
        out.append(f"{a} {b}")
    return out

def _top_themes(
    texts: List[str],
    *,
    n: int = 50,
    extra_stop: Optional[set] = None,
    min_len: int = 3,
    presence: bool = True,
) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]]]:
    uni = Counter()
    bi = Counter()
    for t in texts:
        w = _tokenize(t, extra_stop=extra_stop, min_len=min_len)
        b = _bigrams(w)
        if presence:
            uni.update(set(w))
            bi.update(set(b))
        else:
            uni.update(w)
            bi.update(b)
    return uni.most_common(n), bi.most_common(n)


# ----------------------------
# CLI: Core commands
# ----------------------------

@app.command()
def config():
    """Show configuration and store health."""
    typer.echo(f"store_path: {NODES_PATH}")
    typer.echo(f"store_exists: {NODES_PATH.exists()}")
    env = os.getenv("ELYRIA_CP_NODESTORE")
    typer.echo(f"env ELYRIA_CP_NODESTORE: {env!r}")
    if NODES_PATH.exists():
        try:
            size = NODES_PATH.stat().st_size
            typer.echo(f"store_size_bytes: {size}")
            # count lines fast
            with NODES_PATH.open("r", encoding="utf-8") as f:
                lines = sum(1 for _ in f)
            typer.echo(f"store_lines: {lines}")
        except Exception as e:
            typer.echo(f"store_read_error: {e}")

@app.command()
def new(
    text: Optional[str] = typer.Argument(None, help="Node text; if omitted, prompts interactively."),
    tag: List[str] = typer.Option([], "--tag", "-t", help="Tag(s), repeatable."),
    meta: List[str] = typer.Option([], "--meta", "-m", help="Metadata key=value, repeatable."),
    kind: str = typer.Option("node", "--kind", help="Node kind (node/gate/layer/etc)."),
    echo: bool = typer.Option(False, "--echo", help="Echo the JSON node line after writing."),
):
    """Record a new node."""
    if text is None:
        try:
            text = input("→: ").strip()
        except (EOFError, KeyboardInterrupt):
            typer.echo("\n(cancelled)")
            raise typer.Exit(code=1)

    if not text:
        typer.echo("no text provided")
        raise typer.Exit(code=1)

    meta_obj: Dict[str, Any] = {}
    for item in meta:
        if "=" in item:
            k, v = item.split("=", 1)
            meta_obj[k.strip()] = v.strip()
        else:
            meta_obj[item.strip()] = True

    node: Dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "ts": _utc_now_iso(),
        "kind": kind,
        "text": text,
    }
    if tag:
        node["tags"] = tag
    if meta_obj:
        node["meta"] = meta_obj

    append_node(node)
    typer.echo("✓ node recorded")
    if echo:
        typer.echo(json.dumps(node, ensure_ascii=False, default=str))

@app.command()
def last(raw: bool = typer.Option(False, "--raw", help="Print full JSON for last node.")):
    """Print the last recorded node."""
    nodes = load_nodes()
    if not nodes:
        typer.echo("no nodes recorded")
        raise typer.Exit(code=0)
    n = nodes[-1]
    typer.echo(json.dumps(n, ensure_ascii=False, default=str) if raw else _node_text(n))

@app.command()
def list(limit: int = typer.Option(10, "--limit", "-n", help="How many nodes to show.")):
    """List recent nodes (timestamp + preview)."""
    nodes = load_nodes()
    if not nodes:
        typer.echo("no nodes recorded")
        return
    show = nodes[-limit:] if limit > 0 else nodes
    for n in show:
        ts = n.get("ts", "")
        kind = n.get("kind", "node")
        txt = _node_text(n).replace("\n", " ").strip()
        if len(txt) > 120:
            txt = txt[:117] + "..."
        typer.echo(f"{ts}  [{kind}]  {txt}")

@app.command()
def tail(lines: int = typer.Option(5, "--lines", "-n", help="How many last nodes to print.")):
    """Print last N node texts (full, not preview)."""
    nodes = load_nodes()
    if not nodes:
        typer.echo("no nodes recorded")
        return
    for n in nodes[-lines:]:
        typer.echo(_node_text(n))

@app.command()
def search(
    query: str = typer.Argument(..., help="Substring or regex."),
    regex: bool = typer.Option(False, "--regex", help="Treat query as regex."),
    ignore_case: bool = typer.Option(True, "--ignore-case/--case", help="Case-insensitive by default."),
    limit: int = typer.Option(20, "--limit", "-n", help="Max matches."),
):
    """Search node texts."""
    nodes = load_nodes()
    if not nodes:
        typer.echo("no nodes recorded")
        return

    flags = re.IGNORECASE if ignore_case else 0
    rx = None
    if regex:
        try:
            rx = re.compile(query, flags=flags)
        except re.error as e:
            typer.echo(f"invalid regex: {e}")
            raise typer.Exit(code=2)

    shown = 0
    for n in reversed(nodes):
        t = _node_text(n)
        ok = bool(rx.search(t)) if rx else ((query.lower() in t.lower()) if ignore_case else (query in t))
        if ok:
            ts = n.get("ts", "")
            kind = n.get("kind", "node")
            preview = t.replace("\n", " ").strip()
            if len(preview) > 140:
                preview = preview[:137] + "..."
            typer.echo(f"{ts}  [{kind}]  {preview}")
            shown += 1
            if shown >= limit:
                break
    if shown == 0:
        typer.echo("no matches")

@app.command()
def export(out: Path = typer.Argument(..., help="Output file (.jsonl/.json/.csv).")):
    """Export nodes to jsonl/json/csv."""
    nodes = load_nodes()
    out = out.expanduser().resolve()
    _ensure_parent_dir(out)

    suf = out.suffix.lower()
    if suf == ".jsonl":
        write_nodes(nodes, out)
        typer.echo(f"exported {len(nodes)} nodes -> {out}")
        return
    if suf == ".json":
        with out.open("w", encoding="utf-8") as f:
            json.dump(nodes, f, ensure_ascii=False, indent=2, default=str)
        typer.echo(f"exported {len(nodes)} nodes -> {out}")
        return
    if suf == ".csv":
        with out.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "ts", "kind", "text", "tags", "meta"])
            for n in nodes:
                w.writerow([
                    n.get("id",""),
                    n.get("ts",""),
                    n.get("kind","node"),
                    _node_text(n),
                    ",".join(n.get("tags", [])) if isinstance(n.get("tags"), list) else "",
                    json.dumps(n.get("meta", {}), ensure_ascii=False, default=str) if isinstance(n.get("meta"), dict) else "",
                ])
        typer.echo(f"exported {len(nodes)} nodes -> {out}")
        return

    typer.echo("unsupported export format (use .jsonl/.json/.csv)")
    raise typer.Exit(code=2)

@app.command(name="import")
def import_nodes(src: Path = typer.Argument(..., help="Source file (.jsonl or .json array)."), merge: bool = typer.Option(True, "--merge/--replace")):
    """Import nodes from jsonl/json (merge or replace)."""
    src = src.expanduser().resolve()
    if not src.exists():
        typer.echo(f"source not found: {src}")
        raise typer.Exit(code=2)

    incoming = load_nodes(src)
    if merge:
        current = load_nodes()
        write_nodes(current + incoming)
        typer.echo(f"imported {len(incoming)} (merged) -> total {len(current) + len(incoming)}")
    else:
        write_nodes(incoming)
        typer.echo(f"imported {len(incoming)} (replaced store)")

@app.command()
def doctor(repair: bool = typer.Option(True, "--repair/--no-repair")):
    """Validate store health and optionally repair."""
    typer.echo(f"store: {NODES_PATH}")
    if not NODES_PATH.exists():
        typer.echo("store missing: ok (no nodes yet)")
        return
    nodes = load_nodes()
    typer.echo(f"load_nodes: {len(nodes)} nodes")
    parse_errors = sum(1 for n in nodes if isinstance(n, dict) and n.get("parse_error") is True)
    if parse_errors:
        typer.echo(f"parse_error nodes present: {parse_errors}")
    if repair:
        kept, dropped = doctor_repair()
        typer.echo(f"repair rewrite: kept={kept} dropped={dropped}")

@app.command()
def clear(yes: bool = typer.Option(False, "--yes", help="Skip confirmation prompt.")):
    """Clear the node store (destructive)."""
    if not yes:
        if not typer.confirm(f"Delete all nodes in {NODES_PATH}?"):
            typer.echo("cancelled")
            return
    write_nodes([])
    typer.echo("cleared")

@app.command()
def stats(
    top: int = typer.Option(8, "--top"),
    hide_top: int = typer.Option(5, "--hide-top", help="Hide N most common raw tokens from filtered view."),
    min_len: int = typer.Option(3, "--min-len"),
    presence: bool = typer.Option(True, "--presence/--frequency", help="Per-node presence vs raw frequency."),
    days: int = typer.Option(14, "--days", help="Activity over last N days (UTC)."),
):
    """Show stats: total, activity, raw top words, filtered top words + phrases."""
    nodes = load_nodes()
    texts = [_node_text(n) for n in nodes if _node_text(n).strip()]
    typer.echo(f"total nodes: {len(nodes)}")

    if not texts:
        typer.echo("top raw words:")
        typer.echo("top words:")
        typer.echo("top phrases:")
        return

    # activity
    if days > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days - 1)
        buckets = Counter()
        for n in nodes:
            dt = _parse_iso(n.get("ts",""))
            if not dt:
                continue
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            if dt >= cutoff:
                buckets[dt.date().isoformat()] += 1
        if buckets:
            typer.echo(f"activity (last {days} days, UTC):")
            for day in sorted(buckets.keys()):
                typer.echo(f"  {day}: {buckets[day]}")

    raw = Counter()
    for t in texts:
        raw.update(re.findall(r"[a-z0-9']+", t.lower()))

    typer.echo("top raw words:")
    for w, c in raw.most_common(top):
        typer.echo(f"  {w}: {c}")

    dynamic_stop = {w for w, _ in raw.most_common(hide_top)} if hide_top > 0 else set()
    words, phrases = _top_themes(texts, n=max(100, top * 20), extra_stop=dynamic_stop, min_len=min_len, presence=presence)

    typer.echo("top words:")
    for w, c in words[:top]:
        typer.echo(f"  {w}: {c}")

    typer.echo("top phrases:")
    for p, c in phrases[:top]:
        typer.echo(f"  {p}: {c}")


# ----------------------------
# Intelligence Lair (auto-detect gate/layer)
# ----------------------------

def _try_import(names: List[str]):
    for name in names:
        try:
            return importlib.import_module(name)
        except Exception:
            continue
    return None

def _find_callable(mod, preferred: List[str]) -> Optional[str]:
    if not mod:
        return None
    for name in preferred:
        if hasattr(mod, name) and callable(getattr(mod, name)):
            return name
    return None

def _call(mod, func_name: str, text: str) -> Any:
    fn = getattr(mod, func_name)
    return fn(text)

@lair.command()
def status():
    """Show what the lair can see (gate/layer modules + likely entrypoints)."""
    gate_mod = _try_import(["intelligence_gate", "elyria_cp.intelligence_gate"])
    layer_mod = _try_import(["intelligence_layer", "elyria_cp.intelligence_layer"])

    gate_fn = _find_callable(gate_mod, ["intelligence_gate", "run_gate", "gate", "evaluate", "run"])
    layer_fn = _find_callable(layer_mod, ["intelligence_layer", "run_layer", "layer", "process", "run"])

    typer.echo("INTELLIGENCE LAIR STATUS")
    typer.echo(f"  store: {NODES_PATH}")
    typer.echo(f"  gate module:  {getattr(gate_mod, '__name__', None)}")
    typer.echo(f"  gate entry:   {gate_fn}")
    typer.echo(f"  layer module: {getattr(layer_mod, '__name__', None)}")
    typer.echo(f"  layer entry:  {layer_fn}")
    typer.echo("")
    typer.echo("Tip:")
    typer.echo("  python -m elyria_cp.app lair gate \"elyria rise\"")
    typer.echo("  python -m elyria_cp.app lair layer \"gate open\"")
    typer.echo("  python -m elyria_cp.app lair gate --func <function_name> \"text\"")

@lair.command()
def gate(
    text: Optional[str] = typer.Argument(None, help="Text to run through gate; prompts if omitted."),
    func: Optional[str] = typer.Option(None, "--func", help="Override gate function name."),
    record: bool = typer.Option(True, "--record/--no-record", help="Record result node."),
):
    """Run the intelligence gate (auto-detected) and print results."""
    if text is None:
        try:
            text = input("→ gate: ").strip()
        except (EOFError, KeyboardInterrupt):
            typer.echo("\n(cancelled)")
            raise typer.Exit(code=1)

    gate_mod = _try_import(["intelligence_gate", "elyria_cp.intelligence_gate"])
    if not gate_mod:
        typer.echo("gate module not found (expected intelligence_gate.py).")
        raise typer.Exit(code=2)

    gate_fn = func or _find_callable(gate_mod, ["intelligence_gate", "run_gate", "gate", "evaluate", "run"])
    if not gate_fn:
        typer.echo("no callable gate entry found. Use --func <name> after checking module.")
        raise typer.Exit(code=2)

    try:
        result = _call(gate_mod, gate_fn, text)
    except TypeError:
        # Some gates accept dict payloads; try minimal fallback
        try:
            result = getattr(gate_mod, gate_fn)({"text": text})
        except Exception as e:
            typer.echo(f"gate call failed: {e}")
            raise typer.Exit(code=2)
    except Exception as e:
        typer.echo(f"gate call failed: {e}")
        raise typer.Exit(code=2)

    # Print
    if isinstance(result, (dict, list)):
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    else:
        typer.echo(str(result))

    if record:
        append_node({
            "kind": "gate",
            "text": text,
            "gate": result if isinstance(result, (dict, list, str, int, float, bool)) else str(result),
        })
        typer.echo("✓ recorded gate result")

@lair.command()
def layer(
    text: Optional[str] = typer.Argument(None, help="Text to run through layer; prompts if omitted."),
    func: Optional[str] = typer.Option(None, "--func", help="Override layer function name."),
    record: bool = typer.Option(True, "--record/--no-record", help="Record result node."),
):
    """Run the intelligence layer (auto-detected) and print results."""
    if text is None:
        try:
            text = input("→ layer: ").strip()
        except (EOFError, KeyboardInterrupt):
            typer.echo("\n(cancelled)")
            raise typer.Exit(code=1)

    layer_mod = _try_import(["intelligence_layer", "elyria_cp.intelligence_layer"])
    if not layer_mod:
        typer.echo("layer module not found (expected intelligence_layer.py).")
        raise typer.Exit(code=2)

    layer_fn = func or _find_callable(layer_mod, ["intelligence_layer", "run_layer", "layer", "process", "run"])
    if not layer_fn:
        typer.echo("no callable layer entry found. Use --func <name> after checking module.")
        raise typer.Exit(code=2)

    try:
        result = _call(layer_mod, layer_fn, text)
    except TypeError:
        try:
            result = getattr(layer_mod, layer_fn)({"text": text})
        except Exception as e:
            typer.echo(f"layer call failed: {e}")
            raise typer.Exit(code=2)
    except Exception as e:
        typer.echo(f"layer call failed: {e}")
        raise typer.Exit(code=2)

    if isinstance(result, (dict, list)):
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    else:
        typer.echo(str(result))

    if record:
        append_node({
            "kind": "layer",
            "text": text,
            "layer": result if isinstance(result, (dict, list, str, int, float, bool)) else str(result),
        })
        typer.echo("✓ recorded layer result")

@lair.command()
def replay(
    n: int = typer.Option(10, "--n", help="How many recent nodes to replay into gate/layer."),
    do_gate: bool = typer.Option(True, "--gate/--no-gate", help="Run gate on each."),
    do_layer: bool = typer.Option(False, "--layer/--no-layer", help="Run layer on each."),
    gate_func: Optional[str] = typer.Option(None, "--gate-func"),
    layer_func: Optional[str] = typer.Option(None, "--layer-func"),
):
    """Replay the last N node texts through gate/layer."""
    nodes = load_nodes()
    if not nodes:
        typer.echo("no nodes recorded")
        return

    texts = [ _node_text(x) for x in nodes[-n:] ]
    for t in texts:
        if do_gate:
            typer.echo("\n--- gate ---")
            gate(text=t, func=gate_func, record=True)
        if do_layer:
            typer.echo("\n--- layer ---")
            layer(text=t, func=layer_func, record=True)


def main():
    app()

if __name__ == "__main__":
    main()
