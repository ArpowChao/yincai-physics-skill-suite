from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import re
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RULES_PATH = ROOT / "data" / "tts-pronunciation" / "verified.json"
DEFAULT_FORMULAS_PATH = ROOT / "data" / "tts-pronunciation" / "formulas.json"
FORMULA_RUN_RE = re.compile(
    r"[A-Za-z0-9α-ωΑ-Ω₀-₉⁰¹²³⁴⁵⁶⁷⁸⁹√∫∑∞+\-−*/×÷=≠≤≥<>^().{}\[\],\s]+"
)
FORMULA_SIGNAL_RE = re.compile(r"[²³√∫∑∞+*/×÷=≠≤≥<>]|>=|<=")
FRACTION_RE = re.compile(
    r"(?P<numerator>[A-Za-zα-ωΑ-Ω][A-Za-z0-9₀-₉]*|\d+)\s*/\s*"
    r"(?P<denominator>[A-Za-zα-ωΑ-Ω][A-Za-z0-9₀-₉]*|\d+)"
)


def load_rules(path: Path = DEFAULT_RULES_PATH) -> list[dict[str, Any]]:
    """Load confirmed phrase-level speech substitutions from a JSON file."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return list(payload.get("rules", []))


def load_formula_rules(path: Path = DEFAULT_FORMULAS_PATH) -> dict[str, Any]:
    """Load versioned formula narration settings."""
    return json.loads(path.read_text(encoding="utf-8"))


def narrate_formula(formula: str, config: dict[str, Any]) -> str:
    """Expand a compact formula into editable Traditional Chinese speech text."""
    spoken = FRACTION_RE.sub(
        lambda match: f"{match.group('denominator')} 分之 {match.group('numerator')}",
        formula,
    )
    spoken = re.sub(r"√\s*([A-Za-z0-9α-ωΑ-Ω₀-₉]+)", r"根號 \1", spoken)
    for symbol, narration in config.get("superscripts", {}).items():
        spoken = spoken.replace(symbol, f" {narration}")
    operators = sorted(
        config.get("operators", {}).items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )
    for symbol, narration in operators:
        spoken = re.sub(
            rf"\s*{re.escape(symbol)}\s*",
            f"，{narration} ",
            spoken,
        )
    spoken = re.sub(r"\s+", " ", spoken)
    spoken = re.sub(r"\s*，\s*", "，", spoken)
    return spoken.strip(" ，")


def find_formula_changes(text: str, config: dict[str, Any]) -> list[dict[str, Any]]:
    """Find math-like runs while deliberately ignoring SRT/VTT timing arrows."""
    changes: list[dict[str, Any]] = []
    offset = 0
    for line in text.splitlines(keepends=True) or [text]:
        content = line.rstrip("\r\n")
        if "-->" not in content:
            for match in FORMULA_RUN_RE.finditer(content):
                candidate = match.group(0)
                core = candidate.strip()
                if not core or not FORMULA_SIGNAL_RE.search(core):
                    continue
                narrated = narrate_formula(core, config)
                if narrated == core:
                    continue
                leading = len(candidate) - len(candidate.lstrip())
                trailing = len(candidate) - len(candidate.rstrip())
                start = offset + match.start() + leading
                end = offset + match.end() - trailing
                changes.append(
                    {
                        "id": f"formula-{start}-{end}",
                        "type": "formula",
                        "start": start,
                        "end": end,
                        "original": text[start:end],
                        "spoken": narrated,
                        "pronunciation": "",
                        "verified": True,
                        "source": "confirmed",
                        "note": "依已確認的基礎公式朗讀規則展開；複雜公式請人工確認。",
                    }
                )
        offset += len(line)
    return changes


def _prepare_rules(
    confirmed: Iterable[dict[str, Any]],
    overrides: Iterable[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for rule in confirmed:
        original = str(rule.get("original", ""))
        spoken = str(rule.get("spoken", ""))
        if not original or not spoken:
            continue
        merged[original] = {
            **rule,
            "original": original,
            "spoken": spoken,
            "source": "confirmed",
            "verified": bool(rule.get("verified", False)),
        }
    for rule in overrides or []:
        original = str(rule.get("original", ""))
        spoken = str(rule.get("spoken", ""))
        if not original or not spoken:
            continue
        merged[original] = {
            **rule,
            "original": original,
            "spoken": spoken,
            "source": "personal",
            "verified": bool(rule.get("verified", False)),
        }
    return sorted(merged.values(), key=lambda item: len(item["original"]), reverse=True)


def analyze_text(
    text: str,
    confirmed_rules: Iterable[dict[str, Any]],
    *,
    overrides: Iterable[dict[str, Any]] | None = None,
    formula_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return source text, generated speech text, and non-overlapping changes."""
    rules = _prepare_rules(confirmed_rules, overrides)
    by_first: dict[str, list[dict[str, Any]]] = {}
    for rule in rules:
        by_first.setdefault(rule["original"][0], []).append(rule)

    phrase_changes: list[dict[str, Any]] = []
    index = 0
    while index < len(text):
        match = next(
            (
                rule
                for rule in by_first.get(text[index], [])
                if text.startswith(rule["original"], index)
            ),
            None,
        )
        if match is None:
            index += 1
            continue
        end = index + len(match["original"])
        phrase_changes.append(
            {
                "id": f"phrase-{index}-{end}",
                "type": "pronunciation",
                "start": index,
                "end": end,
                "original": match["original"],
                "spoken": match["spoken"],
                "pronunciation": match.get("pronunciation", ""),
                "verified": match["verified"],
                "source": match["source"],
                "note": match.get("note", ""),
            }
        )
        index = end

    formula_changes = find_formula_changes(
        text,
        formula_config if formula_config is not None else load_formula_rules(),
    )
    changes: list[dict[str, Any]] = []
    for change in sorted(phrase_changes + formula_changes, key=lambda item: item["start"]):
        if changes and change["start"] < changes[-1]["end"]:
            continue
        changes.append(change)

    speech_parts: list[str] = []
    cursor = 0
    for change in changes:
        speech_parts.append(text[cursor : change["start"]])
        speech_parts.append(change["spoken"])
        cursor = change["end"]
    speech_parts.append(text[cursor:])

    return {
        "source_text": text,
        "speech_text": "".join(speech_parts),
        "changes": changes,
    }


def write_outputs(input_path: Path, output_dir: Path, result: dict[str, Any]) -> tuple[Path, Path]:
    """Write derivative files next to an untouched source file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    speech_path = output_dir / f"{input_path.stem}.tts.txt"
    changes_path = output_dir / f"{input_path.stem}.changes.json"
    speech_path.write_text(result["speech_text"], encoding="utf-8")
    changes_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_file": input_path.name,
                "changes": result["changes"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return speech_path, changes_path


def create_server(
    root: Path = ROOT,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> ThreadingHTTPServer:
    """Create a local-only static and JSON API server for the review interface."""
    root = root.resolve()
    confirmed = load_rules(root / "data" / "tts-pronunciation" / "verified.json")
    formulas = load_formula_rules(root / "data" / "tts-pronunciation" / "formulas.json")

    class ReviewHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, directory=str(root), **kwargs)

        def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
            route = urlparse(self.path).path
            if route == "/api/config":
                self._send_json({"rules": confirmed, "formulas": formulas})
                return
            if route == "/":
                self.path = "/showcase/tts-pronunciation/index.html"
            elif route in {"/styles.css", "/app.js"}:
                self.path = f"/showcase/tts-pronunciation{route}"
            elif route in {"/data/verified.json", "/data/formulas.json", "/data/submission.json"}:
                self.path = f"/data/tts-pronunciation/{Path(route).name}"
            super().do_GET()

        def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
            if urlparse(self.path).path != "/api/analyze":
                self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                text = str(payload.get("text", ""))
                overrides = payload.get("overrides", [])
                if not isinstance(overrides, list):
                    raise ValueError("overrides must be a list")
                self._send_json(
                    analyze_text(
                        text,
                        confirmed,
                        overrides=overrides,
                        formula_config=formulas,
                    )
                )
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

        def log_message(self, format: str, *args: Any) -> None:
            return

    return ThreadingHTTPServer((host, port), ReviewHandler)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="建立不污染原稿的網路配音稿。")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="分析檔案並輸出配音稿。")
    analyze_parser.add_argument("input", type=Path)
    analyze_parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs")
    analyze_parser.add_argument("--overrides", type=Path)

    serve_parser = subparsers.add_parser("serve", help="啟動本機人工校對頁面。")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8765)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "analyze":
        source = args.input.read_text(encoding="utf-8-sig")
        overrides: list[dict[str, Any]] = []
        if args.overrides:
            override_payload = json.loads(args.overrides.read_text(encoding="utf-8"))
            overrides = list(override_payload.get("rules", override_payload))
        result = analyze_text(source, load_rules(), overrides=overrides)
        speech_path, changes_path = write_outputs(args.input, args.output_dir, result)
        print(f"配音稿：{speech_path}")
        print(f"修改紀錄：{changes_path}")
        return 0

    server = create_server(ROOT, args.host, args.port)
    print(f"本機校對頁面：http://{args.host}:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
