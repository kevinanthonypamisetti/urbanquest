create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  name text not null,
  email text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.saved_trips (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  trip_data jsonb not null,
  created_at timestamptz not null default now()
);

create table if not exists public.ai_conversations (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  trip_id uuid references public.saved_trips(id) on delete cascade,
  summary text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.ai_messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references public.ai_conversations(id) on delete cascade,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  input_tokens integer not null default 0,
  output_tokens integer not null default 0,
  created_at timestamptz not null default now()
);

create table if not exists public.ai_usage (
  user_id uuid not null references auth.users(id) on delete cascade,
  usage_date date not null default current_date,
  requests integer not null default 0,
  input_tokens integer not null default 0,
  output_tokens integer not null default 0,
  estimated_cost numeric(12, 6) not null default 0,
  primary key (user_id, usage_date)
);

alter table public.profiles enable row level security;
alter table public.saved_trips enable row level security;
alter table public.ai_conversations enable row level security;
alter table public.ai_messages enable row level security;
alter table public.ai_usage enable row level security;

create policy "Users can read their profile" on public.profiles for select using (auth.uid() = id);
create policy "Users can create their profile" on public.profiles for insert with check (auth.uid() = id);
create policy "Users can update their profile" on public.profiles for update using (auth.uid() = id);
create policy "Users can manage their trips" on public.saved_trips for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "Users can manage their AI conversations" on public.ai_conversations for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "Users can manage their AI messages" on public.ai_messages for all using (
  exists (select 1 from public.ai_conversations c where c.id = conversation_id and c.user_id = auth.uid())
) with check (
  exists (select 1 from public.ai_conversations c where c.id = conversation_id and c.user_id = auth.uid())
);
create policy "Users can read their AI usage" on public.ai_usage for select using (auth.uid() = user_id);

create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public
as $$
begin
  insert into public.profiles (id, name, email)
  values (new.id, coalesce(new.raw_user_meta_data->>'name', split_part(new.email, '@', 1)), new.email)
  on conflict (id) do update set name = excluded.name, email = excluded.email;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
