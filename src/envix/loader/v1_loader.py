import asyncio
import os
from typing import TYPE_CHECKING, assert_never

from pydantic import SecretStr

from envix.config.v1.envs import EnvsV1
from envix.config.v1.envs.bitwarden_envs_v1 import BitwardenEnvsV1
from envix.config.v1.envs.file_envs_v1 import FileEnvsV1
from envix.config.v1.envs.google_cloud_secret_manager_envs_v1 import (
    GoogleCloudSecretManagerEnvsV1,
)
from envix.config.v1.envs.local_envs_v1 import LocalEnvsV1
from envix.config.v1.envs.raw_envs_v1 import RawEnvsV1
from envix.exception import (
    EnvixBitwardenError,
    EnvixEnvInjectionError,
    EnvixEnvironmentFileLoadError,
    EnvixEnvironmentNotSetting,
    EnvixGoogleCloudSecretManagerError,
)
from envix.types import Secrets

if TYPE_CHECKING:
    from google.cloud import secretmanager


async def load_raw_envs_v1(
    envs: RawEnvsV1,
) -> tuple[Secrets, list[EnvixEnvInjectionError]]:
    secrets: Secrets = {}
    errors: list[EnvixEnvInjectionError] = []

    for envname, secret in envs.items.items():
        if envs.overwrite or envname not in os.environ:
            os.environ[envname] = secret
            secrets[envname] = SecretStr(secret)

    return secrets, errors


async def load_file_envs_v1(
    envs: FileEnvsV1,
) -> tuple[Secrets, list[EnvixEnvInjectionError]]:
    secrets: Secrets = {}
    errors: list[EnvixEnvInjectionError] = []

    for envname, filepath in envs.items.items():
        if envs.overwrite or envname not in os.environ:
            try:
                with open(filepath, "r") as f:
                    envvar = f.read().strip()
                    os.environ[envname] = envvar
                    secrets[envname] = SecretStr(envvar)

            except Exception:
                errors.append(EnvixEnvironmentFileLoadError(envname, filepath))

    return secrets, errors


async def load_local_envs_v1(
    envs: LocalEnvsV1,
) -> tuple[Secrets, list[EnvixEnvInjectionError]]:
    secrets: Secrets = {}
    errors: list[EnvixEnvInjectionError] = []

    for envname, envvar in envs._items.items():
        if envvar not in os.environ:
            errors.append(EnvixEnvironmentNotSetting(envvar))
            continue

        if envs.overwrite or envname not in os.environ:
            os.environ[envname] = os.environ[envvar]
            secrets[envname] = SecretStr(os.environ[envvar])

    return secrets, errors


async def load_google_cloud_secret_manager_envs_v1(
    envs: GoogleCloudSecretManagerEnvsV1,
    *,
    client: "secretmanager.SecretManagerServiceAsyncClient | None" = None,
) -> tuple[Secrets, list[EnvixEnvInjectionError]]:
    from google.cloud import secretmanager

    secrets: Secrets = {}
    errors: list[EnvixEnvInjectionError] = []
    client = client or secretmanager.SecretManagerServiceAsyncClient()

    async def access_secret_version(envname: str, secret_name: str):
        if envs.overwrite or envname not in os.environ:
            try:
                response = await client.access_secret_version(
                    request={"name": secret_name}
                )
                envvar = response.payload.data.decode("UTF-8")
                os.environ[envname] = envvar
                secrets[envname] = SecretStr(envvar)

            except Exception as e:
                errors.append(EnvixGoogleCloudSecretManagerError(envname, e))

    await asyncio.gather(
        *(
            access_secret_version(envname, secret_name)
            for envname, secret_name in envs.secret_items.items()
        ),
    )

    return secrets, errors


async def load_bitwarden_envs_v1(
    envs: BitwardenEnvsV1,
) -> tuple[Secrets, list[EnvixEnvInjectionError]]:
    secrets: Secrets = {}
    errors: list[EnvixEnvInjectionError] = []

    try:
        from bitwarden_sdk import BitwardenClient, ClientSettings

        client = BitwardenClient(ClientSettings())
        await client.initialize()

        for envname, item in envs.secret_items.items():
            if envs.overwrite or envname not in os.environ:
                try:
                    # アイテムIDとフィールドIDを抽出
                    item_id = item.split("/")[1]
                    field_id = item.split("/")[3]

                    # アイテムを取得
                    secret_item = await client.get_secret(item_id)

                    # フィールドの値を取得
                    field = next(
                        (f for f in secret_item.fields if f.id == field_id), None
                    )

                    if field is None:
                        errors.append(
                            EnvixBitwardenError(f"Field not found: {field_id}")
                        )
                        continue

                    value = field.value
                    os.environ[envname] = value
                    secrets[envname] = SecretStr(value)

                except Exception as e:
                    errors.append(
                        EnvixBitwardenError(f"Failed to get Bitwarden item: {str(e)}")
                    )

        await client.cleanup()

    except ImportError:
        errors.append(EnvixBitwardenError("bitwarden-sdk package is not installed"))
    except Exception as e:
        errors.append(
            EnvixBitwardenError(f"Failed to initialize Bitwarden client: {str(e)}")
        )

    return secrets, errors


async def load_envs_v1(
    envs: EnvsV1,
    google_cloud_secret_manager_client: "secretmanager.SecretManagerServiceAsyncClient | None" = None,
) -> tuple[Secrets, list[EnvixEnvInjectionError]]:
    match envs:
        case RawEnvsV1():
            return await load_raw_envs_v1(envs)

        case FileEnvsV1():
            return await load_file_envs_v1(envs)

        case LocalEnvsV1():
            return await load_local_envs_v1(envs)

        case GoogleCloudSecretManagerEnvsV1():
            return await load_google_cloud_secret_manager_envs_v1(
                envs, client=google_cloud_secret_manager_client
            )

        case BitwardenEnvsV1():
            return await load_bitwarden_envs_v1(envs)

        case _:
            assert_never(envs)
