"""Rules the schema itself enforces (PROPOSAL §2), tested on real Postgres.

Fake data only: no real people (CLAUDE.md privacy rule).
"""

from datetime import date, time

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    Department,
    Event,
    Idea,
    Person,
    PersonContact,
    Pin,
    Space,
    Step,
    Task,
    person_spaces,
)

SOME_DAY = date(2026, 12, 3)


def make_space(db_session: Session, name: str = "Space") -> Space:
    space = Space(name=name, color="indigo", icon="folder")
    db_session.add(space)
    db_session.flush()
    return space


def make_department(
    db_session: Session, space: Space, name: str = "Dept"
) -> Department:
    department = Department(space_id=space.id, name=name)
    db_session.add(department)
    db_session.flush()
    return department


def make_task(db_session: Session, space: Space, **fields) -> Task:
    task = Task(space_id=space.id, title="Task", **fields)
    db_session.add(task)
    db_session.flush()
    return task


def test_deleting_department_moves_its_tasks_to_no_department(
    db_session: Session,
) -> None:
    space = make_space(db_session)
    department = make_department(db_session, space)
    task = make_task(db_session, space, department_id=department.id)

    db_session.execute(delete(Department).where(Department.id == department.id))
    db_session.refresh(task)

    assert task.department_id is None
    assert task.space_id == space.id  # same space, "No department"


def test_task_cannot_use_a_department_of_another_space(db_session: Session) -> None:
    space_a = make_space(db_session, "A")
    space_b = make_space(db_session, "B")
    department_a = make_department(db_session, space_a)

    with pytest.raises(IntegrityError):
        make_task(db_session, space_b, department_id=department_a.id)


def test_deleting_space_deletes_its_content_but_keeps_events_and_people(
    db_session: Session,
) -> None:
    space = make_space(db_session)
    department = make_department(db_session, space)
    task = make_task(db_session, space, department_id=department.id)
    step = Step(task_id=task.id, title="Step")
    idea = Idea(text="Idea", space_id=space.id)
    event = Event(
        title="Meeting", date=SOME_DAY, start_time=time(14, 0), space_id=space.id
    )
    person = Person(full_name="Test Person")
    db_session.add_all([step, idea, event, person])
    db_session.flush()
    db_session.add(Pin(date=SOME_DAY, step_id=step.id))
    db_session.execute(
        person_spaces.insert().values(person_id=person.id, space_id=space.id)
    )
    db_session.flush()

    db_session.execute(delete(Space).where(Space.id == space.id))
    db_session.expire_all()

    for model in (Department, Task, Step, Idea, Pin):
        assert db_session.scalar(select(func.count()).select_from(model)) == 0, model
    assert db_session.get(Event, event.id).space_id is None
    assert db_session.get(Person, person.id) is not None
    links = select(func.count()).select_from(person_spaces)
    assert db_session.scalar(links) == 0


def test_only_one_main_contact_per_kind(db_session: Session) -> None:
    person = Person(full_name="Test Person")
    db_session.add(person)
    db_session.flush()
    db_session.add_all(
        [
            PersonContact(
                person_id=person.id, kind="email", value="a@example.com", is_main=True
            ),
            PersonContact(
                person_id=person.id, kind="phone", value="0550000000", is_main=True
            ),
            PersonContact(person_id=person.id, kind="email", value="b@example.com"),
        ]
    )
    db_session.flush()  # one main email + one main phone + a non-main email: fine

    db_session.add(
        PersonContact(
            person_id=person.id, kind="email", value="c@example.com", is_main=True
        )
    )
    with pytest.raises(IntegrityError):
        db_session.flush()


@pytest.mark.parametrize("target", ["none", "both"])
def test_pin_targets_exactly_one_task_or_step(db_session: Session, target: str) -> None:
    task = make_task(db_session, make_space(db_session))
    step = Step(task_id=task.id, title="Step")
    db_session.add(step)
    db_session.flush()
    ids = {"none": {}, "both": {"task_id": task.id, "step_id": step.id}}[target]

    db_session.add(Pin(date=SOME_DAY, **ids))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_waiting_fields_only_on_waiting_tasks(db_session: Session) -> None:
    with pytest.raises(IntegrityError):
        make_task(
            db_session,
            make_space(db_session),
            status="todo",
            waiting_on_text="Some Org",
        )
