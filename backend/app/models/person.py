"""People book: person, contacts, family, tags, custom fields, contact log."""

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    SmallInteger,
    Table,
    false,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models._mixins import CreatedAt, Timestamps, UUIDPk, check_in

if TYPE_CHECKING:
    from app.models.space import Space

CONTACT_KINDS = ("email", "phone")
FAMILY_RELATIONS = ("father", "mother", "brother", "sister", "spouse", "child", "other")
TAG_KINDS = ("hobby", "like", "dislike")


# No rows for a person means "Personal".
person_spaces = Table(
    "person_spaces",
    Base.metadata,
    Column("person_id", ForeignKey("people.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "space_id",
        ForeignKey("spaces.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    ),
)


class Person(UUIDPk, Timestamps, Base):
    __tablename__ = "people"
    __table_args__ = (
        # Birthday is optional, but day and month come together (decision 23).
        # Full validity (Feb 30, Feb 29 needs no year) is checked in Pydantic.
        CheckConstraint(
            "(birth_day IS NULL) = (birth_month IS NULL)", name="birthday_day_month"
        ),
        CheckConstraint("birth_month BETWEEN 1 AND 12", name="birth_month_range"),
        CheckConstraint("birth_day BETWEEN 1 AND 31", name="birth_day_range"),
        CheckConstraint(
            "birth_year IS NULL OR birth_day IS NOT NULL",
            name="birth_year_needs_day_month",
        ),
        # Trigram index: fast fuzzy / partial search by name (pg_trgm extension).
        Index(
            "ix_people_full_name_trgm",
            "full_name",
            postgresql_using="gin",
            postgresql_ops={"full_name": "gin_trgm_ops"},
        ),
    )

    full_name: Mapped[str]
    nickname: Mapped[str | None]
    birth_day: Mapped[int | None] = mapped_column(SmallInteger)
    birth_month: Mapped[int | None] = mapped_column(SmallInteger)
    birth_year: Mapped[int | None] = mapped_column(SmallInteger)
    # Storage key (core/storage.py), never a public URL: photos are served
    # through a protected route.
    photo_key: Mapped[str | None]
    notes: Mapped[str | None]

    contacts: Mapped[list["PersonContact"]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="PersonContact.position",
    )
    family: Mapped[list["PersonFamily"]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="PersonFamily.position",
    )
    tags: Mapped[list["PersonTag"]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True
    )
    custom_fields: Mapped[list["PersonCustomField"]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="PersonCustomField.position",
    )
    contact_logs: Mapped[list["ContactLog"]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ContactLog.date.desc()",
    )
    spaces: Mapped[list["Space"]] = relationship(
        secondary=person_spaces, passive_deletes=True
    )


class PersonContact(UUIDPk, Base):
    __tablename__ = "person_contacts"
    __table_args__ = (
        CheckConstraint(check_in("kind", CONTACT_KINDS), name="kind_valid"),
    )

    person_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("people.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str]
    label: Mapped[str | None]  # "personal", "work", ...
    value: Mapped[str]  # as entered
    # Normalized phone (+213...), for tap-to-call and wa.me links (decision 24).
    value_e164: Mapped[str | None]
    is_main: Mapped[bool] = mapped_column(default=False, server_default=false())
    position: Mapped[int] = mapped_column(default=0, server_default="0")


# At most one main email and one main phone per person.
Index(
    "uq_person_contacts_one_main_per_kind",
    PersonContact.person_id,
    PersonContact.kind,
    unique=True,
    postgresql_where=PersonContact.is_main.is_(True),
)


class PersonFamily(UUIDPk, Base):
    __tablename__ = "person_family"
    __table_args__ = (
        CheckConstraint(check_in("relation", FAMILY_RELATIONS), name="relation_valid"),
    )

    person_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("people.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str]
    relation: Mapped[str]
    position: Mapped[int] = mapped_column(default=0, server_default="0")


class PersonTag(UUIDPk, Base):
    __tablename__ = "person_tags"
    __table_args__ = (CheckConstraint(check_in("kind", TAG_KINDS), name="kind_valid"),)

    person_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("people.id", ondelete="CASCADE")
    )
    kind: Mapped[str]
    value: Mapped[str]


# No duplicate tag per person and kind, ignoring case ("Chess" vs "chess").
Index(
    "uq_person_tags_person_id_kind_lower_value",
    PersonTag.person_id,
    PersonTag.kind,
    func.lower(PersonTag.value),
    unique=True,
)
# People list tag filter + tag autocomplete.
Index("ix_person_tags_kind_lower_value", PersonTag.kind, func.lower(PersonTag.value))


class PersonCustomField(UUIDPk, Base):
    __tablename__ = "person_custom_fields"

    person_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("people.id", ondelete="CASCADE"), index=True
    )
    label: Mapped[str]
    value: Mapped[str]
    position: Mapped[int] = mapped_column(default=0, server_default="0")


class ContactLog(UUIDPk, CreatedAt, Base):
    """Short dated note. "Last contacted" = max(date) for the person."""

    __tablename__ = "contact_logs"

    person_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("people.id", ondelete="CASCADE")
    )
    date: Mapped[date]
    text: Mapped[str]


Index(
    "ix_contact_logs_person_id_date_desc",
    ContactLog.person_id,
    ContactLog.date.desc(),
)
