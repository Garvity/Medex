-- Apply after 001 if it was previously run with the Resend transport.
-- Preserve all delivery history while making the provider identifier generic.
do $$
begin
  if exists (
    select 1 from information_schema.columns
    where table_schema = current_schema()
      and table_name = 'reminder_deliveries'
      and column_name = 'resend_message_id'
  ) and not exists (
    select 1 from information_schema.columns
    where table_schema = current_schema()
      and table_name = 'reminder_deliveries'
      and column_name = 'provider_message_id'
  ) then
    alter table reminder_deliveries rename column resend_message_id to provider_message_id;
  end if;
end $$;
