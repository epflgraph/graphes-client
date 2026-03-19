# graphes/models/esquery.py
# Rich-aware ES query model with metadata and rendering helpers.
from __future__ import annotations

import json
import re
import textwrap
import hashlib
from time import perf_counter
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator
from rich import box
from rich.console import Console, Group
from rich.json import JSON as RichJSON
from rich.markup import escape
from rich.panel import Panel
from rich.rule import Rule
from rich.text import Text

BoxStyle = Literal["rounded", "heavy", "double", "minimal", "simple", "none"]

_BOX_MAP = {
    "rounded": box.ROUNDED,
    "heavy": box.HEAVY,
    "double": box.DOUBLE,
    "minimal": box.MINIMAL,
    "simple": box.SIMPLE,
    "none": None,
}


class ESQuery(BaseModel):
    """
    Rich-aware ES query object with metadata, timing, and rendering helpers.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(..., min_length=1, description="Raw ES query text (typically JSON/QDSL).")
    description: str = Field(default="", description="Human-readable query context.")
    query_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier.")
    params: Any = Field(default=None, description="Bound parameters.")
    elapsed_ms: float | None = Field(default=None, ge=0, description="Execution time in milliseconds.")
    es: str | None = Field(default=None, description="Cluster, database, or engine name.")
    title: str = Field(default="ES Query", description="Render title.")
    theme: str = Field(default="monokai", description="Compatibility field (unused by JSON renderer).")
    word_wrap: bool = Field(default=True, description="Compatibility field (unused by JSON renderer).")
    show_header: bool = Field(default=True, description="Render title rule.")
    box_style: BoxStyle = Field(default="minimal", description="Panel box style.")
    copyable: bool = Field(default=False, description="Print plain query text if True.")
    redact_params: bool = Field(default=True, description="Redact sensitive values in displayed params.")
    row_count: int | None = Field(default=None, ge=0, description="Number of hits returned/affected.")
    error: str | None = Field(default=None, description="Last execution error, if any.")

    _timer_started_at: float | None = PrivateAttr(default=None)

    @field_validator("query")
    @classmethod
    def _query_not_blank(cls, value: str) -> str:
        normalized = textwrap.dedent(value).strip()
        if not normalized:
            raise ValueError("query cannot be blank.")
        return value

    def _query_obj(self) -> Any | None:
        try:
            return json.loads(self.query)
        except Exception:
            return None

    def canonical_qdsl(self) -> str:
        """
        Canonical representation of the query for hashing/logging.
        """
        obj = self._query_obj()
        if obj is not None:
            return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return re.sub(r"\s+", " ", self.query.strip())

    def canonical_sql(self) -> str:
        """Backward-compatible alias for canonical_qdsl()."""
        return self.canonical_qdsl()

    def one_line_qdsl(self, max_len: int = 240) -> str:
        compact = self.canonical_qdsl()
        if len(compact) <= max_len:
            return compact
        return f"{compact[: max_len - 3]}..."

    def one_line_sql(self, max_len: int = 240) -> str:
        """Backward-compatible alias for one_line_qdsl()."""
        return self.one_line_qdsl(max_len=max_len)

    def aligned_qdsl(self) -> str:
        """
        Backward-compatible alias. No custom alignment is applied.
        """
        return self.query.strip()

    def aligned_sql(self) -> str:
        """Backward-compatible alias for aligned_qdsl()."""
        return self.aligned_qdsl()

    def normalize_qdsl_lines(self) -> list[str]:
        return [line.rstrip() for line in textwrap.dedent(self.query).strip("\n").splitlines() if line.strip()]

    def normalize_sql_lines(self) -> list[str]:
        """Backward-compatible alias for normalize_qdsl_lines()."""
        return self.normalize_qdsl_lines()

    def fingerprint(self, *, include_params: bool = False, length: int = 12) -> str:
        payload = self.canonical_qdsl()
        if include_params and self.params is not None:
            payload += f"|{repr(self.redacted_params())}"
        digest = hashlib.sha1(payload.encode("utf-8")).hexdigest()
        return digest[:length]

    def redacted_params(
        self,
        *,
        sensitive_keys: tuple[str, ...] = ("password", "passwd", "pwd", "token", "secret", "api_key"),
    ) -> Any:
        if self.params is None:
            return None

        sensitive = tuple(k.lower() for k in sensitive_keys)

        def _walk(value: Any, key: str | None = None) -> Any:
            if isinstance(value, dict):
                out: dict[str, Any] = {}
                for k, v in value.items():
                    key_str = str(k)
                    out[key_str] = _walk(v, key=key_str)
                return out
            if isinstance(value, (list, tuple)):
                return [_walk(v, key=key) for v in value]
            if key and any(s in key.lower() for s in sensitive):
                return "***REDACTED***"
            return value

        return _walk(self.params)

    def start_timer(self) -> "ESQuery":
        self._timer_started_at = perf_counter()
        return self

    def stop_timer(self, *, row_count: int | None = None, error: Exception | str | None = None) -> "ESQuery":
        if self._timer_started_at is not None:
            self.elapsed_ms = (perf_counter() - self._timer_started_at) * 1000
            self._timer_started_at = None
        if row_count is not None:
            self.row_count = row_count
        if error is not None:
            self.error = str(error)
        return self

    def debug_snapshot(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "fingerprint": self.fingerprint(include_params=False),
            "es": self.es,
            "elapsed_ms": self.elapsed_ms,
            "row_count": self.row_count,
            "has_error": self.error is not None,
            "error": self.error,
            "description": self.description or None,
            "query": self.one_line_qdsl(),
            "params": self.redacted_params(),
        }

    def meta_text(self, *, include_debug: bool = False) -> Text:
        meta = Text()
        if self.es:
            meta.append(f"es={self.es}  ", style="dim")
        if self.elapsed_ms is not None:
            meta.append("time=", style="dim")
            meta.append(f"{self.elapsed_ms:.2f} ms", style="bold magenta")
        if self.row_count is not None:
            meta.append("  hits=", style="dim")
            meta.append(str(self.row_count), style="bold cyan")
        if self.params is not None:
            params_for_display = self.redacted_params() if self.redact_params else self.params
            meta.append("  params=", style="dim")
            meta.append(repr(params_for_display), style="yellow")
        if include_debug:
            meta.append("  qid=", style="dim")
            meta.append(self.query_id[:8], style="bold blue")
            meta.append("  fp=", style="dim")
            meta.append(self.fingerprint(), style="bold green")
        if self.error:
            meta.append("  error=", style="dim")
            meta.append(self.error, style="bold red")
        return meta

    def json_renderable(self) -> RichJSON | Text:
        obj = self._query_obj()
        if obj is not None:
            return RichJSON.from_data(obj)
        return Text(self.query.strip())

    def panel(self, *, include_debug: bool = False) -> Panel:
        meta = self.meta_text(include_debug=include_debug)
        return Panel(
            Group(self.json_renderable(), meta if meta.plain else Text()),
            border_style="bright_cyan",
            box=_BOX_MAP[self.box_style],
            padding=(1, 2),
            expand=False,
        )

    def print(self, console: Console | None = None) -> None:
        target = console or Console()
        if self.show_header:
            target.print(Rule(f"[bold bright_blue]{escape(self.title)}"))
        if self.copyable:
            target.print(self.query.strip())
            meta = self.meta_text()
            if meta.plain:
                target.print(meta)
            return
        target.print(self.panel())

    def print_debug(self, console: Console | None = None) -> None:
        target = console or Console()
        target.print(Rule(f"[bold bright_blue]{escape(self.title)} [dim](debug)[/dim]"))
        target.print(self.panel(include_debug=True))

    def execute_with_timing(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        self.start_timer()
        try:
            result = fn(*args, **kwargs)
            if isinstance(result, (list, tuple)):
                self.stop_timer(row_count=len(result))
            else:
                self.stop_timer()
            return result
        except Exception as exc:
            self.stop_timer(error=exc)
            raise

    def as_copyable(self) -> str:
        obj = self._query_obj()
        text = json.dumps(obj, ensure_ascii=False, indent=2) if obj is not None else self.query.strip()
        meta = self.meta_text()
        return text if not meta.plain else f"{text}\n{meta.plain}"

    @classmethod
    def from_dict(cls, payload: dict[str, Any], *, title: str = "ES Query", **kwargs: Any) -> "ESQuery":
        return cls(query=json.dumps(payload, ensure_ascii=False, indent=2), title=title, **kwargs)

    @classmethod
    def from_parts(
        cls,
        select: str,
        from_: str,
        where: str | None = None,
        *,
        title: str = "ES Query",
        **kwargs: Any,
    ) -> "ESQuery":
        lines = [f"SELECT {select}", f"FROM {from_}"]
        if where:
            lines.append(f"WHERE {where}")
        return cls(query="\n".join(lines), title=title, **kwargs)


def print_qdsl(
    query: str,
    *,
    params: Any = None,
    elapsed_ms: float | None = None,
    es: str | None = None,
    title: str = "ES Query",
    show_header: bool = True,
    box_style: BoxStyle = "minimal",
    copyable: bool = False,
    theme: str = "monokai",
    word_wrap: bool = True,
    console: Console | None = None,
) -> None:
    """
    Compatibility wrapper around ESQuery for drop-in usage.
    """
    ESQuery(
        query=query,
        params=params,
        elapsed_ms=elapsed_ms,
        es=es,
        title=title,
        show_header=show_header,
        box_style=box_style,
        copyable=copyable,
        redact_params=True,
        theme=theme,
        word_wrap=word_wrap,
    ).print(console=console)
