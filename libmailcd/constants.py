LOCAL_MB_ROOT = ".mb"
LOCAL_INBOX_DIRNAME = "inbox" # TODO(Matthew): rename to have _MB_ in name
LOCAL_OUTBOX_DIRNAME = "outbox" # TODO(Matthew): rename to have _MB_ in name
LOCAL_MB_LOGS_ROOT_DIRNAME = "logs"
LOCAL_MB_LOGS_BUILD_DIRNAME = "build"
LOCAL_ENV_DIRNAME = "env" # TODO(Matthew): rename to have _MB_ in name
LOCAL_ENV_SELECT_FILENAME = ".selected"
LOCAL_LIB_SELECT_FILENAME = ".selected"
LOCAL_MB_STAGE_ROOT = "stages"

DEFAULT_ENV_CONFIG_NAME = "default" # Maybe this should be "develop"?

DEFAULT_LIBRARY_NAME = 'default'

PIPELINE_CONTAINERFILE_SEPARATOR = ':'
PIPELINE_CONTAINERFILE_OS_WINDOWS = 'windows'
PIPELINE_CONTAINERFILE_OS_LINUX = 'linux'
PIPELINE_COPY_SEPARATOR = "->"

AGENT_CONTAINER_WORKSPACE = '/.ws'
