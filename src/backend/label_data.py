from datetime import date, datetime, timedelta
from typing import Any, Literal, Type
from plum import dispatch
import serde
from serde import field
import shortuuid
from src.backend.member import Member

class DateTimeSerializer:
    @dispatch
    def serialize(self, value: datetime) -> str:
        return datetime.isoformat(value, timespec='seconds')

class DateTimeDeserializer:
    @dispatch
    def deserialize(self, cls: Type[datetime], value: Any) -> datetime:
        return datetime.fromisoformat(value)

# Workaround for https://github.com/yukinarit/pyserde/issues/453
serde.add_serializer(DateTimeSerializer())
serde.add_deserializer(DateTimeDeserializer())

@serde.serde
class LabelBase:
    id: int
    created_by_member_number: int # Can be different if a board member created the label for someone else
    member_number: int
    member_name: str
    created_at: datetime
    version: Literal[3]

    @staticmethod
    def from_member(member: Member):
        generator = shortuuid.ShortUUID()
        generator.set_alphabet("0123456789")
        # Generate a random 13-digit numeric ID
        # 13 digits gives us 10^13 unique IDs, which
        # is enough to randomly generate IDs without
        # any significant risk of collisions,
        # even if we generate tens of thousands of them.
        # See https://www.bdayprob.com/.
        id = int(generator.random(13))

        return LabelBase(
            id=id,
            created_by_member_number=member.member_number,
            member_number=member.member_number,
            member_name=member.get_name(),
            created_at=datetime.now(),
            version=3
        )

    def approximately_equal(self, other: 'LabelBase') -> bool:
        return self.member_number == other.member_number and self.member_name == other.member_name and abs(self.created_at - other.created_at) < timedelta(minutes=5) and self.created_by_member_number == other.created_by_member_number


@serde.serde
class TemporaryStorageLabel:
    base: LabelBase = field(flatten=True)
    description: str
    expires_at: date = field(serializer=date.isoformat, deserializer=date.fromisoformat)

    @staticmethod
    def from_member(member: Member, description: str, expires_at: date):
        base = LabelBase.from_member(member)
        return TemporaryStorageLabel(base=base, description=description, expires_at=expires_at)

    def approximately_equal(self, other: 'LabelType') -> bool:
        return isinstance(other, TemporaryStorageLabel) and self.base.approximately_equal(other.base) and self.description == other.description and self.expires_at == other.expires_at


@serde.serde
class BoxLabel:
    base: LabelBase = field(flatten=True)

    @staticmethod
    def from_member(member: Member):
        return BoxLabel(base=LabelBase.from_member(member))

    def approximately_equal(self, other: 'LabelType') -> bool:
        return isinstance(other, BoxLabel) and self.base.approximately_equal(other.base)

@serde.serde
class FireSafetyLabel:
    base: LabelBase = field(flatten=True)
    expires_at: date = field(serializer=date.isoformat, deserializer=date.fromisoformat)

    @staticmethod
    def from_member(member: Member, expires_at: date):
        return FireSafetyLabel(base=LabelBase.from_member(member), expires_at=expires_at)

    def approximately_equal(self, other: 'LabelType') -> bool:
        return isinstance(other, FireSafetyLabel) and self.base.approximately_equal(other.base) and self.expires_at == other.expires_at

@serde.serde
class Printer3DLabel:
    base: LabelBase = field(flatten=True)

    @staticmethod
    def from_member(member: Member):
        return Printer3DLabel(base=LabelBase.from_member(member))

    def approximately_equal(self, other: 'LabelType') -> bool:
        return isinstance(other, Printer3DLabel) and self.base.approximately_equal(other.base)

@serde.serde
class NameTag:
    base: LabelBase = field(flatten=True)
    membership_expires_at: date | None = field(
        serializer=date.isoformat,
        deserializer=date.fromisoformat
    )

    @staticmethod
    def from_member(member: Member):
        return NameTag(base=LabelBase.from_member(member), membership_expires_at=member.membership.end_date.date() if member.membership.end_date is not None else None)

    def approximately_equal(self, other: 'LabelType') -> bool:
        return isinstance(other, NameTag) and self.base.approximately_equal(other.base) and self.membership_expires_at == other.membership_expires_at

@serde.serde
class MeetupNameTag:
    base: LabelBase = field(flatten=True)

    @staticmethod
    def from_member(member: Member):
        return MeetupNameTag(base=LabelBase.from_member(member))

    def approximately_equal(self, other: 'LabelType') -> bool:
        return isinstance(other, MeetupNameTag) and self.base.approximately_equal(other.base)

@serde.serde
class DryingLabel:
    base: LabelBase = field(flatten=True)
    expires_at: datetime = field(
        serializer=datetime.isoformat,
        deserializer=datetime.fromisoformat
    )

    @staticmethod
    def from_member(member: Member, drying_hours: int):
        base = LabelBase.from_member(member)
        expires_at = roundUpHour(base.created_at + timedelta(hours=drying_hours))
        return DryingLabel(base=base, expires_at=expires_at)

    def approximately_equal(self, other: 'LabelType') -> bool:
        return isinstance(other, DryingLabel) and self.base.approximately_equal(other.base) and abs(self.expires_at - other.expires_at) < timedelta(minutes=5)

def roundUpHour(dt: datetime) -> datetime:
    if dt.minute > 0:
        dt = dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    else:
        dt = dt.replace(minute=0, second=0, microsecond=0)
    return dt

LabelType = TemporaryStorageLabel | BoxLabel | FireSafetyLabel | Printer3DLabel | NameTag | MeetupNameTag | DryingLabel
