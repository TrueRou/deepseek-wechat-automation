import contextlib
from sqlalchemy import text
from alembic import command
from alembic.config import Config as AlembicConfig
from sqlalchemy.exc import OperationalError
from sqlmodel import SQLModel, create_engine, Session


from deepseek_wechat_automation.app import settings
from deepseek_wechat_automation.app.logging import Ansi, log


engine = create_engine(settings.db_url, echo=False)


def init_db():
    try:
        with session_ctx() as session:
            session.exec(text("SELECT 1"))
    except OperationalError:
        log("Failed to connect to the database.", Ansi.RED)
    try:
        command.upgrade(AlembicConfig(config_args={"script_location": "alembic"}), "head")
    except Exception as e:
        log(f"Failed to run database migration: {e}", Ansi.RED)


@contextlib.contextmanager
def session_ctx():
    with Session(engine, expire_on_commit=False) as session:
        yield session


def add_model(session: Session, *models):
    [session.add(model) for model in models if model]
    session.commit()
    [session.refresh(model) for model in models if model]


def delete_model(session: Session, model: SQLModel):
    session.delete(model)
    session.commit()


def partial_update_model(session: Session, item: SQLModel, updates: SQLModel):
    if item and updates:
        update_data = updates.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(item, key, value)
        session.commit()
        session.refresh(item)
