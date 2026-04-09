from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

from yaml import safe_load


class GraphESConfigError(ValueError):
    pass


def _parse_dotenv_assignment(line: str) -> tuple[str, str] | None:
    raw = line.strip()
    if not raw or raw.startswith("#"):
        return None
    if raw.startswith("export "):
        raw = raw[len("export ") :].lstrip()
    if "=" not in raw:
        return None
    key, value = raw.split("=", 1)
    key = key.strip()
    if not key:
        return None
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        value = value[1:-1]
    return key, value


def _find_dotenv_file() -> Optional[Path]:
    cwd = Path.cwd()
    for candidate_dir in (cwd, *cwd.parents):
        candidate = candidate_dir / ".env"
        if candidate.exists():
            return candidate
    pkg_root = Path(__file__).resolve().parents[2]
    candidate = pkg_root / ".env"
    if candidate.exists():
        return candidate
    docker_candidate = Path("/app/.env")
    if docker_candidate.exists():
        return docker_candidate
    return None


@lru_cache(maxsize=1)
def _resolve_dotenv_override() -> Optional[Path]:
    override = os.getenv("GRAPHES_CONFIG")
    if override:
        return Path(override).expanduser().resolve()

    dotenv = _find_dotenv_file()
    if not dotenv:
        return None

    try:
        with dotenv.open("r", encoding="utf-8") as fh:
            for line in fh:
                parsed = _parse_dotenv_assignment(line)
                if parsed and parsed[0] == "GRAPHES_CONFIG":
                    value = parsed[1]
                    if value:
                        return Path(value).expanduser().resolve()
    except OSError:
        return None

    return None


@dataclass(frozen=True)
class EnvironmentConfig:
    host_address: str
    port: int
    username: str
    password: str

    @classmethod
    def from_dict(cls, env_name: str, raw: Dict[str, Any]) -> "EnvironmentConfig":
        host = raw.get("host_address", raw.get("hostname"))
        required = ("port", "username", "password")
        missing = [k for k in required if k not in raw]
        if host is None:
            missing = ["host_address|hostname", *missing]
        if missing:
            raise GraphESConfigError(
                f"Environment '{env_name}' missing required keys: {', '.join(missing)}"
            )
        return cls(
            host_address=str(host),
            port=int(raw["port"]),
            username=str(raw["username"]),
            password=str(raw["password"]),
        )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "host_address": self.host_address,
            "port": self.port,
            "username": self.username,
            "password": self.password,
        }


@dataclass(frozen=True)
class GraphESConfig:
    environments: Dict[str, EnvironmentConfig]
    default_env: str
    data_path: Optional[Dict[str, Any]] = None

    @classmethod
    def default_path(cls) -> Path:
        # Backward-compatible single-path accessor.
        # Prefer explicit env path when provided.
        override = _resolve_dotenv_override()
        if override:
            return override
        return Path.cwd() / "config.yaml"

    @classmethod
    def default_paths(cls) -> list[Path]:
        candidates: list[Path] = []

        override = _resolve_dotenv_override()
        if override:
            candidates.append(override)

        # Most common local workflow
        candidates.append(Path.cwd() / "config.yaml")
        # Docker image layout used by this project
        candidates.append(Path("/app/config.yaml"))
        # Legacy package-relative fallback
        candidates.append(Path(__file__).resolve().parents[2] / "config.yaml")

        # De-duplicate while preserving order
        unique: list[Path] = []
        seen: set[str] = set()
        for path in candidates:
            key = str(path)
            if key in seen:
                continue
            seen.add(key)
            unique.append(path)
        return unique

    @classmethod
    def from_default_file(cls) -> "GraphESConfig":
        for path in cls.default_paths():
            if path.exists():
                return cls.from_file(path)
        searched = ", ".join(str(p) for p in cls.default_paths())
        raise GraphESConfigError(f"Config file not found. Searched: {searched}")

    @classmethod
    def from_file(cls, path: Path | str) -> "GraphESConfig":
        cfg_path = Path(path)
        if not cfg_path.exists():
            raise GraphESConfigError(f"Config file not found: {cfg_path}")
        with cfg_path.open("r", encoding="utf-8") as f:
            raw = safe_load(f) or {}
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "GraphESConfig":
        if not isinstance(raw, dict):
            raise GraphESConfigError("config.yaml must parse into a dictionary.")

        # Accept either:
        # 1) top-level elasticsearch block
        # 2) top-level graphes block (legacy transition)
        # 3) top-level keys directly (current config.yaml)
        if isinstance(raw.get("elasticsearch"), dict):
            es_cfg = raw["elasticsearch"]
        elif isinstance(raw.get("graphes"), dict):
            es_cfg = raw["graphes"]
        else:
            es_cfg = raw
        if not isinstance(es_cfg, dict):
            raise GraphESConfigError("Invalid config structure.")

        data_path = es_cfg.get("data_path", raw.get("data_path"))

        environments: Dict[str, EnvironmentConfig] = {}
        env_block = es_cfg.get("environments", raw.get("environments"))
        if isinstance(env_block, dict):
            for env_key, env_value in env_block.items():
                if isinstance(env_value, dict):
                    env_name = str(env_key).removesuffix("_env")
                    environments[env_name] = EnvironmentConfig.from_dict(env_name, env_value)

        reserved_keys = {
            "default_env",
            "data_path",
            "environments",
        }
        for key, value in es_cfg.items():
            if key in reserved_keys or not isinstance(value, dict):
                continue
            if key.endswith("_env"):
                env_name = key.removesuffix("_env")
                environments[env_name] = EnvironmentConfig.from_dict(env_name, value)

        if len(environments) == 0:
            raise GraphESConfigError(
                "No environments found. Define environments under 'environments:' or '*_env' keys."
            )

        default_env_raw = es_cfg.get("default_env", raw.get("default_env"))
        default_env = (
            str(default_env_raw).removesuffix("_env")
            if default_env_raw
            else next(iter(environments.keys()))
        )
        if default_env not in environments:
            raise GraphESConfigError(
                f"default_env '{default_env}' is not in configured environments: {sorted(environments.keys())}"
            )

        return cls(
            environments=environments,
            default_env=default_env,
            data_path=data_path if isinstance(data_path, dict) else None,
        )

    def env_names(self) -> list[str]:
        return list(self.environments.keys())

    def get_env(self, env_name: str) -> EnvironmentConfig:
        if env_name not in self.environments:
            raise GraphESConfigError(
                f"Unknown environment '{env_name}'. Available: {sorted(self.environments.keys())}"
            )
        return self.environments[env_name]

    def export_root(self) -> str:
        if not isinstance(self.data_path, dict) or "export" not in self.data_path:
            raise GraphESConfigError("Missing config path: data_path.export")
        return str(self.data_path["export"])
