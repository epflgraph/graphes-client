# graphes/cli/context.py
# This module defines the shared context for CLI commands, including the GraphES instance.
from dataclasses import dataclass
from typing import TYPE_CHECKING

# If TYPE_CHECKING is True, these imports are only for type checking and will not be executed at runtime
if TYPE_CHECKING:
    from graphes.core.graphes import GraphES

# Define a dataclass to hold shared context for CLI commands
@dataclass
class CLIContext:
    es : "GraphES"
