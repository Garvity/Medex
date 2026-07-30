create extension if not exists pgcrypto;
create table if not exists profiles (
  id text primary key,
  name text,
  phone text,
  email text,
  timezone text not null default 'Asia/Kolkata',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create table if not exists chat_sessions (
  id uuid primary key,
  user_id text not null references profiles(id) on delete cascade,
  name text not null default 'New consultation',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists idx_chat_sessions_user_updated on chat_sessions (user_id, updated_at desc);
create table if not exists chat_messages (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references chat_sessions(id) on delete cascade,
  user_id text not null references profiles(id) on delete cascade,
  query text not null,
  response text not null,
  role text not null default 'user' check (role in ('user', 'doctor')),
  sources jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_chat_messages_session_created on chat_messages (session_id, created_at);
create table if not exists reminders (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references profiles(id) on delete cascade,
  medicine text not null,
  reminder_time text not null,
  timezone text not null default 'Asia/Kolkata',
  frequency text not null default 'once' check (
    frequency in ('once', 'daily', 'weekly', 'every_8_hours')
  ),
  notification_pref text not null default 'in_app',
  status text not null default 'active' check (status in ('active', 'completed')),
  last_triggered_at timestamptz,
  next_occurrence_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists idx_reminders_user_status on reminders (user_id, status);
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
create table if not exists evaluation_runs (
  id uuid primary key default gen_random_uuid(),
  suite_name text not null,
  metrics jsonb not null,
  created_at timestamptz not null default now()
);
