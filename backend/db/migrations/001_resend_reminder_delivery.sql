-- Apply once to databases created before the reminder-worker migration.
alter table profiles
add column if not exists email text;
alter table profiles
add column if not exists timezone text not null default 'UTC';
alter table reminders
add column if not exists timezone text not null default 'UTC';
alter table reminders
add column if not exists next_occurrence_at timestamptz;
update reminders r
set timezone = p.timezone
from profiles p
where r.user_id = p.id
  and r.timezone = 'UTC'
  and p.timezone <> 'UTC';
-- Initialize schedules for existing active reminders that use the legacy UI's
-- normalized 12-hour time format. Other legacy values remain null and can be
-- corrected by editing the reminder in the current UI.
update reminders
set next_occurrence_at = case
    when (
      (
        (now() at time zone timezone)::date + reminder_time::time
      ) at time zone timezone
    ) <= now() then (
      (
        (now() at time zone timezone)::date + 1 + reminder_time::time
      ) at time zone timezone
    )
    else (
      (
        (now() at time zone timezone)::date + reminder_time::time
      ) at time zone timezone
    )
  end
where status = 'active'
  and next_occurrence_at is null
  and reminder_time ~* '^\\s*(0?[1-9]|1[0-2]):[0-5][0-9]\\s*(AM|PM)\\s*$';
create index if not exists idx_reminders_due on reminders (next_occurrence_at)
where status = 'active';
create table if not exists reminder_deliveries (
  id uuid primary key default gen_random_uuid(),
  reminder_id uuid not null references reminders(id) on delete cascade,
  user_id text not null references profiles(id) on delete cascade,
  scheduled_for timestamptz not null,
  recipient_email text not null,
  status text not null default 'pending' check (
    status in (
      'pending',
      'sending',
      'sent',
      'retrying',
      'failed'
    )
  ),
  attempt_count integer not null default 0 check (attempt_count >= 0),
  next_retry_at timestamptz,
  locked_at timestamptz,
  provider_message_id text,
  last_error text,
  created_at timestamptz not null default now(),
  sent_at timestamptz,
  updated_at timestamptz not null default now(),
  unique (reminder_id, scheduled_for)
);
create index if not exists idx_reminder_deliveries_pending on reminder_deliveries (status, next_retry_at)
where status in ('pending', 'retrying', 'sending');