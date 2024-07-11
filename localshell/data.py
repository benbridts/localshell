import dataclasses
from typing import Mapping, Optional


@dataclasses.dataclass(frozen=True, eq=True)
class VpcConfig:
    vpc_id: str
    subnet_ids: frozenset[str]
    security_group_ids: frozenset[str]

    @classmethod
    def load(cls, e: Mapping):
        return cls(
            vpc_id=e["VpcId"],
            subnet_ids=frozenset(e.get("SubnetIds", [])),
            security_group_ids=frozenset(e.get("SecurityGroupIds", [])),
        )

    def dump(self) -> Mapping:
        return {
            "VpcId": self.vpc_id,
            "SubnetIds": list(self.subnet_ids),
            "SecurityGroupIds": list(self.security_group_ids),
        }


@dataclasses.dataclass(frozen=True, eq=True)
class Environment:
    environment_id: str
    environment_name: Optional[str]
    vcp_config: Optional[VpcConfig]

    @classmethod
    def load(cls, e: Mapping):
        return cls(
            environment_id=e["EnvironmentId"],
            environment_name=e.get("EnvironmentName"),
            vcp_config=VpcConfig.load(e["VpcConfig"]) if "VpcConfig" in e else None,
        )

    def dump(self) -> Mapping:
        return {
            "EnvironmentId": self.environment_id,
            "EnvironmentName": self.environment_name,
            "VpcConfig": self.vcp_config.dump(),
        }
