from typing import Any, Iterable

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema


class AttrDict(dict):
    """
    A *magic* wrapper over built-in `dict` that allows to interact with dict items via attributes.
    """

    def __dir__(self) -> Iterable[str]:
        return list(super().__dir__()) + [str(k) for k in self.keys()]

    def __getattr__(self, item: str) -> Any:
        if item in self:
            return self[item]
        raise AttributeError(f"Object 'AttrDict' has no attribute '{item}'")

    def __getattribute__(self, item: str) -> Any:
        try:
            return super().__getattribute__(item)
        except AttributeError:
            return self.__getattr__(item)

    def __setattr__(self, key: str, value: Any):
        self[key] = value

    @classmethod
    def _dict_to_attrdict(
        cls, value: dict, _info: core_schema.ValidationInfo
    ) -> "AttrDict":
        return cls(value)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        def init_cls(data: dict) -> "AttrDict":
            return AttrDict(data)

        base_schema = core_schema.chain_schema(
            [
                core_schema.dict_schema(),
                core_schema.no_info_plain_validator_function(init_cls),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=base_schema,
            python_schema=core_schema.union_schema(
                [core_schema.is_instance_schema(AttrDict), base_schema]
            ),
        )
