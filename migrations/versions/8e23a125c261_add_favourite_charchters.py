"""add_favourite_charchters

Revision ID: 8e23a125c261
Revises: 563fe88e52b2
Create Date: 2025-02-13 18:25:44.142609

"""

from typing import Sequence, Union
import sqlmodel
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8e23a125c261"
down_revision: Union[str, None] = "563fe88e52b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "user_favorite_characters",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["lor_characters.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id", "user_id", "character_id"),
    )
    op.create_index(
        op.f("ix_user_favorite_characters_id"),
        "user_favorite_characters",
        ["id"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(
        op.f("ix_user_favorite_characters_id"), table_name="user_favorite_characters"
    )
    op.drop_table("user_favorite_characters")
    # ### end Alembic commands ###
