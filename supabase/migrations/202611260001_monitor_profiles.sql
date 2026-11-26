begin;

create table public.monitor_profiles (
    id smallint primary key check (id = 1),
    revision uuid not null,
    settings jsonb not null check (
        jsonb_typeof(settings) = 'object'
        and settings ? 'profiles'
        and settings ? 'default_profile_id'
        and jsonb_typeof(settings -> 'profiles') = 'object'
        and settings -> 'profiles' <> '{}'::jsonb
        and jsonb_typeof(settings -> 'default_profile_id') = 'string'
        and (settings -> 'profiles') ? (settings ->> 'default_profile_id')
    )
);

alter table public.monitor_profiles enable row level security;
revoke all on public.monitor_profiles from public, anon, authenticated;
grant select, insert, update on public.monitor_profiles to authenticated;

create policy monitor_profiles_read on public.monitor_profiles
    for select to authenticated
    using (
        ((select auth.jwt()) -> 'app_metadata' -> 'monitor_ss_active') is distinct from 'false'::jsonb
        and (
            (select auth.jwt()) -> 'app_metadata' -> 'monitor_ss_managed' = 'true'::jsonb
            or exists (
                select 1 from public.sim_comunicados_admins
                where user_id = (select auth.uid())
            )
        )
    );

create policy monitor_profiles_insert on public.monitor_profiles
    for insert to authenticated
    with check (
        ((select auth.jwt()) -> 'app_metadata' -> 'monitor_ss_active') is distinct from 'false'::jsonb
        and exists (
            select 1 from public.sim_comunicados_admins
            where user_id = (select auth.uid())
        )
    );

create policy monitor_profiles_update on public.monitor_profiles
    for update to authenticated
    using (
        ((select auth.jwt()) -> 'app_metadata' -> 'monitor_ss_active') is distinct from 'false'::jsonb
        and exists (
            select 1 from public.sim_comunicados_admins
            where user_id = (select auth.uid())
        )
    );

commit;
