begin;

alter policy monitor_profiles_read on public.monitor_profiles
    using (
        ((select auth.jwt()) -> 'app_metadata' -> 'monitor_ss_active') is distinct from 'false'::jsonb
        and exists (
            select 1 from public.sim_comunicados_admins
            where user_id = (select auth.uid())
        )
    );

create schema if not exists monitor_profile_private;
revoke all on schema monitor_profile_private from public;
grant usage on schema monitor_profile_private to authenticated;

create function monitor_profile_private.profiles_for_account()
returns jsonb language sql stable security definer
set search_path = ''
as $$
    with account as (
        select case
            when raw_app_meta_data ->> 'monitor_ss_profile' in
                ('suporte', 'ti', 'desenvolvimento', 'gestao', 'gestor', 'visualizador')
            then raw_app_meta_data ->> 'monitor_ss_profile'
            else 'visualizador'
        end as access_type
        from auth.users
        where id = (select auth.uid())
          and raw_app_meta_data -> 'monitor_ss_managed' = 'true'::jsonb
          and raw_app_meta_data -> 'monitor_ss_active' is distinct from 'false'::jsonb
          and raw_app_meta_data -> 'monitor_ss_force_password_change' is distinct from 'true'::jsonb
          and (banned_until is null or banned_until <= pg_catalog.now())
    ), visible as (
        select mp.settings ->> 'default_profile_id' as requested_default,
               entries.key, entries.value
        from public.monitor_profiles mp
        cross join account
        cross join lateral pg_catalog.jsonb_each(mp.settings -> 'profiles') as entries
        where mp.id = 1
          and (
              account.access_type = 'gestao'
              or entries.value ->> 'available_to' is null
              or (
                  pg_catalog.jsonb_typeof(entries.value -> 'available_to') = 'array'
                  and (entries.value -> 'available_to') ? account.access_type
              )
          )
    )
    select pg_catalog.jsonb_build_object(
        'profiles', coalesce(pg_catalog.jsonb_object_agg(key, value - 'available_to'), '{}'::jsonb),
        'default_profile_id', coalesce(
            max(key) filter (where key = requested_default),
            (array_agg(key order by value ->> 'nome', key))[1]
        )
    )
    from visible
$$;

revoke all on function monitor_profile_private.profiles_for_account() from public, anon, authenticated;
grant execute on function monitor_profile_private.profiles_for_account() to authenticated;

create function public.monitor_profiles_for_account()
returns jsonb language sql stable security invoker
set search_path = ''
as $$
    select monitor_profile_private.profiles_for_account()
$$;

revoke all on function public.monitor_profiles_for_account() from public, anon, authenticated;
grant execute on function public.monitor_profiles_for_account() to authenticated;

commit;
