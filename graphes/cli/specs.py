# graphes/cli/specs.py
# This module defines the specifications for the CLI commands, including their arguments and handler functions.
from typing import Any, Dict
from graphes.core.config import GraphESConfig, GraphESConfigError

# Import all command handler functions
from graphes.cli.commands import (
    cmd_config,
    cmd_test,
    cmd_info,
    cmd_health,
    cmd_list,
    cmd_copy,
    cmd_export,
    cmd_import,
    cmd_index
)

# Load CLI environment settings from configuration file, with fallback to defaults
def _load_cli_env_settings():
    try:
        cfg = GraphESConfig.from_default_file()
        envs = tuple(cfg.env_names())
        default_env = cfg.default_env
    except (GraphESConfigError, OSError, ValueError):
        raise RuntimeError("Failed to load CLI environment settings from configuration file. Please ensure the config file is present and properly formatted.")
    return envs, default_env

# Load CLI environment settings at module level so they can be used in command specifications
_CLI_ENVS, _CLI_DEFAULT_ENV = _load_cli_env_settings()
_CLI_SECOND_ENV = _CLI_ENVS[1] if len(_CLI_ENVS) > 1 else _CLI_DEFAULT_ENV

# Global common arguments
global_common_args = {
    'env' : dict(
        flags = ('--env',),
        kwargs = dict(
            help = "Specify environment.",
            choices = _CLI_ENVS,
            default = _CLI_DEFAULT_ENV
        )
    )
}

#===================================================#
# CLI Definitions for all Subcommands and Arguments #
#===================================================#
cli_definitions: Dict[str, Any] = {

    #-----------------#
    # Command: config #
    #-----------------#
    'config' : dict(
        help = "Manage and print configuration options.",
        common_args = {},
        commands = {
            'print' : dict(
                help = "Print out config options.",
                func = cmd_config,
                requires_es = False,
                args = [],
                common_args = [],
            )
        }
    ),

    #---------------#
    # Command: test #
    #---------------#
    'test' : dict(
        help = "Test server connectivity.",
        common_args = {
            'env': global_common_args['env']
        },
        func = cmd_test,
        args = [],
        common_args_order = ['env'],
    ),

    #---------------#
    # Command: info #
    #---------------#
    'info' : dict(
        help = "Print server info.",
        common_args = {
            'env': global_common_args['env']
        },
        func = cmd_info,
        args = [],
        common_args_order = ['env'],
    ),

    #-----------------#
    # Command: health #
    #-----------------#
    'health' : dict(
        help = "Print server health.",
        common_args = {
            'env': global_common_args['env']
        },
        func = cmd_health,
        args = [],
        common_args_order = ['env'],
    ),

    #---------------#
    # Command: list #
    #---------------#
    'list' : dict(
        help = "List indexes on the server.",
        common_args = {
            'env': global_common_args['env']
        },
        func = cmd_list,
        args = [
            dict(flags = ('--display_size', '-s'), kwargs = dict(action='store_true', help="Display index list with sizes (in GB).")),
            dict(flags = ('--aliases'     , '-a'), kwargs = dict(action='store_true', help="Display index aliases.")),
        ],
        common_args_order = ['env'],
    ),

    #-----------------#
    # Command: export #
    #-----------------#
    'export' : dict(
        help = "Export index into local folder.",
        common_args = {
            'env': global_common_args['env']
        },
        func = cmd_export,
        args = [
            dict(flags = ('--index_name'   ,), kwargs = dict(required=True,  type=str, help="Name of the index to export.")),
            dict(flags = ('--output_folder',), kwargs = dict(required=True,  type=str, help="Output folder to save the exported index.")),
            dict(flags = ('--chunk_size'   ,), kwargs = dict(required=False, type=int, default=1000000, help="Number of documents to export per batch (default=1000000).")),
            dict(flags = ('--use_gzip'        , '-gz'), kwargs = dict(action='store_true', help="Compress exported data files using GZIP.")),
            dict(flags = ('--replace_existing',  '-r'), kwargs = dict(action='store_true', help="Replace existing files in the output folder if they exist.")),
            dict(flags = ('--force'           ,  '-f'), kwargs = dict(action='store_true', help="Force replace without prompting for confirmation.")),
        ],
        common_args_order = ['env'],
    ),

    #-----------------#
    # Command: import #
    #-----------------#
    'import' : dict(
        help = "Import index from local folder.",
        common_args = {
            'env': global_common_args['env']
        },
        func = cmd_import,
        args = [
            dict(flags = ('--input_folder' ,), kwargs = dict(required=True, type=str, help="Input folder containing the exported index.")),
            dict(flags = ('--rename_to'    ,), kwargs = dict(required=False, type=str, default=None,   help="Rename index to this name on target server.")),
            dict(flags = ('--chunk_size'   ,), kwargs = dict(required=False, type=int, default=100000, help="Number of documents to import per batch (default=100000).")),
            dict(flags = ('--replace_existing',  '-r'), kwargs = dict(action='store_true', help="Replace existing files in the output folder if they exist.")),
            dict(flags = ('--force'           ,  '-f'), kwargs = dict(action='store_true', help="Force replace without prompting for confirmation.")),
        ],
        common_args_order = ['env'],
    ),

    #---------------#
    # Command: copy #
    #---------------#
    'copy' : dict(
        help = "Copy index across servers.",
        common_args = {},
        func = cmd_copy,
        args = [
            dict(flags = ('--index_name'   ,), kwargs = dict(required=False, type=str, default=None,   help="Name of the index to copy.")),
            dict(flags = ('--from_env'     ,), kwargs = dict(required=False, type=str, default='test', help="Source environment.")),
            dict(flags = ('--to_env'       ,), kwargs = dict(required=False, type=str, default='prod', help="Target environment.")),
            dict(flags = ('--rename_to'    ,), kwargs = dict(required=False, type=str, default=None,   help="Rename index to this name on target server.")),
            dict(flags = ('--chunk_size'   ,), kwargs = dict(required=False, type=int, default=1000,   help="Number of documents to copy per batch (default=1000).")),
            dict(flags = ('--alias_pattern',), kwargs = dict(required=False, type=str, default=None,   help="Name of the alias to copy.")),
            dict(flags = ('--use_gzip'        , '-gz'), kwargs = dict(action='store_true', help="Compress exported data files using GZIP.")),
            dict(flags = ('--replace_existing',  '-r'), kwargs = dict(action='store_true', help="Replace existing files in the output folder if they exist.")),
            dict(flags = ('--force'           ,  '-f'), kwargs = dict(action='store_true', help="Force replace without prompting for confirmation.")),
        ],
        common_args_order = [],
    ),

    #----------------#
    # Command: index #
    #----------------#
    'index' : dict(
        help = "Operations related to an individual index.",
        common_args = {
            'env': global_common_args['env']
        },
        func = cmd_index,
        args = [
            dict(flags = ('--index_name'   ,), kwargs = dict(required=True,  type=str, default=None, help="Name of the index to manage.")),
            dict(flags = ('--create_alias' ,), kwargs = dict(required=True, type=str, help="Create alias pointing to index.")),
            # dict(flags = ('--replace_existing', '-r'), kwargs = dict(action='store_true', default=False, help="Replace existing alias.")),
            # dict(flags = ('--force'           , '-f'), kwargs = dict(action='store_true', default=False, help="Force replace without prompting for confirmation."))
        ],
        common_args_order = ['env'],
    )
}
