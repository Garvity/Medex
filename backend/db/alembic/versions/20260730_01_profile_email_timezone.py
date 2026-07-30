"""Add Firebase email storage to profiles.

Revision ID: 20260730_01
Revises:
Create Date: 2026-07-30
"""

from alembic import op


revision = "20260730_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Safely upgrade both legacy and freshly initialized PostgreSQL databases."""
    op.execute(
        """
        do $$
        begin
          if not exists (
            select 1 from information_schema.columns
            where table_schema = current_schema() and table_name = 'profiles' and column_name = 'email'
          ) then
            alter table profiles add column email text;
          end if;
          if not exists (
            select 1 from information_schema.columns
            where table_schema = current_schema() and table_name = 'profiles' and column_name = 'timezone'
          ) then
            alter table profiles add column timezone text not null default 'UTC';
          end if;
        end $$
        """
    )


def downgrade() -> None:
    op.execute("alter table profiles drop column if exists email")
    op.execute("alter table profiles drop column if exists timezone")
