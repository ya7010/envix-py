from envix.config.v1.envs.file_envs_v1 import FileEnvsV1
from envix.config.v1.envs.raw_envs_v1 import RawEnvsV1

from .bitwarden_envs_v1 import BitwardenEnvsV1
from .google_cloud_secret_manager_envs_v1 import GoogleCloudSecretManagerEnvsV1
from .local_envs_v1 import LocalEnvsV1

EnvsV1 = (
    RawEnvsV1
    | FileEnvsV1
    | LocalEnvsV1
    | GoogleCloudSecretManagerEnvsV1
    | BitwardenEnvsV1
)
