"""Use Asia/Kolkata as the default reminder timezone.

Revision ID: 20260730_02
Revises: 20260730_01
Create Date: 2026-07-30
"""

from alembic import op


revision = "20260730_02"
down_revision = "20260730_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Defaults apply only to future rows. Existing reminders retain their stored
    # timezone and occurrence so an upgrade never silently changes a schedule.
    op.execute("alter table profiles alter column timezone set default 'Asia/Kolkata'")
    op.execute("alter table reminders alter column timezone set default 'Asia/Kolkata'")


def downgrade() -> None:
    op.execute("alter table profiles alter column timezone set default 'UTC'")
    op.execute("alter table reminders alter column timezone set default 'UTC'")
