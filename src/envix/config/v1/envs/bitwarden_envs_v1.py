from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from envix.pattern import ENVNAME_PATTERN

from ._common import OverwriteType


class BitwardenItem(BaseModel):
    """
    Bitwarden item configuration.
    """

    item_id: Annotated[
        str,
        Field(
            title="Item Id",
        ),
    ]

    field_id: Annotated[
        str,
        Field(
            title="Field Id",
        ),
    ]


class BitwardenEnvsV1(BaseModel):
    """
    Bitwarden environment variables.
    """

    model_config = ConfigDict(extra="forbid")

    type: Annotated[
        Literal["Bitwarden"],
        Field(title="Bitwarden environment variables."),
    ]

    items: dict[
        Annotated[str, Field(pattern=ENVNAME_PATTERN)],
        Annotated[
            str,
            Field(
                title="Name of the Bitwarden item and field to read.",
                pattern=r"items/\w+/fields/\w+",
                examples=["items/123/fields/456"],
            ),
        ]
        | BitwardenItem,
    ]

    overwrite: OverwriteType = True

    @property
    def secret_items(self) -> dict[str, str]:
        items: dict[str, str] = {}
        for envname, item in self.items.items():
            if isinstance(item, str):
                items[envname] = item
            elif isinstance(item, BitwardenItem):
                items[envname] = f"items/{item.item_id}/fields/{item.field_id}"

        return items
