"""Configuração por perfil dos horários de pausa do Layout S&S."""

import datetime as dt
import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path


_HORARIO = r"(?:[01]\d|2[0-3]):[0-5]\d"
_INTERVALO = re.compile(rf"^\s*({_HORARIO})\s*[-–]\s*({_HORARIO})\s*$")
_DIAS = {
    1: "Segunda",
    2: "Terça",
    3: "Quarta",
    4: "Quinta",
    5: "Sexta",
    6: "Sábado",
    7: "Domingo",
}
_CAMPOS_EXCECAO = ("date", "group", "agent_id", "agent_name", "window")


@lru_cache(maxsize=1)
def _padrao():
    return json.loads(Path(__file__).with_name("g4flex_escala_padrao.json").read_text(encoding="utf-8"))


def _texto(value):
    return value.strip() if isinstance(value, str) else ""


def _chave_nome(name):
    folded = unicodedata.normalize("NFD", name)
    return " ".join(re.sub(r"[\u0300-\u036f]", "", folded).lower().split())


def _membro(value):
    if not isinstance(value, dict):
        return {}
    return {key: text for key in ("id", "name") if (text := _texto(value.get(key)))}


def _chave_membro(member):
    return ("id", member["id"].lower()) if member.get("id") else ("name", _chave_nome(member.get("name", "")))


def _conflito_horarios(windows):
    ordered = sorted(windows, key=lambda window: window["start"])
    return any(left["end"] > right["start"] for left, right in zip(ordered, ordered[1:]))


def _excecao(value, groups, windows):
    if not isinstance(value, dict):
        return None
    entry = {key: _texto(value.get(key)) for key in _CAMPOS_EXCECAO}
    try:
        date = dt.date.fromisoformat(entry["date"])
    except ValueError:
        return None
    if date.isoformat() != entry["date"]:
        return None
    if entry["group"] and entry["group"] not in groups:
        return None
    if entry["window"] and entry["window"] not in windows:
        return None
    return {key: text for key, text in entry.items() if text}


def normalizar_escala(value):
    """Devolve uma escala completa e independente, inclusive para perfis antigos."""
    defaults = _padrao()
    source = value if isinstance(value, dict) else {}
    input_groups = source.get("groups")
    input_groups = input_groups if isinstance(input_groups, list) else []
    groups_by_id = {
        _texto(group.get("id")): group for group in input_groups if isinstance(group, dict)
    }
    groups = []
    assigned = set()
    for fallback in defaults["groups"]:
        provided = groups_by_id.get(fallback["id"], {})
        raw_members = provided.get("members")
        members = []
        for entry in raw_members if isinstance(raw_members, list) else fallback["members"]:
            member = _membro(entry)
            if member and (key := _chave_membro(member)) not in assigned:
                members.append(member)
                assigned.add(key)
        raw_windows = provided.get("windows")
        windows_by_id = {
            _texto(window.get("id")): window
            for window in (raw_windows if isinstance(raw_windows, list) else [])
            if isinstance(window, dict)
        }
        windows = []
        for default_window in fallback["windows"]:
            supplied = windows_by_id.get(default_window["id"], {})
            start, end = (_texto(supplied.get(key)) for key in ("start", "end"))
            time_valid = _INTERVALO.fullmatch(f"{start}-{end}") and start < end
            windows.append({**default_window, **({"start": start, "end": end} if time_valid else {})})
        if _conflito_horarios(windows):
            windows = [dict(window) for window in fallback["windows"]]
        groups.append({**fallback, "members": members, "windows": windows})

    weekdays = source.get("weekdays")
    grace = source.get("grace_minutes")
    raw_exceptions = source.get("exceptions")
    group_ids = {group["id"] for group in groups}
    window_ids = {window["id"] for group in groups for window in group["windows"]}
    exceptions = []
    for raw in raw_exceptions if isinstance(raw_exceptions, list) else []:
        entry = _excecao(raw, group_ids, window_ids)
        if entry and entry not in exceptions:
            exceptions.append(entry)
    return {
        "enabled": source.get("enabled") is not False,
        "grace_minutes": grace if type(grace) is int and 0 <= grace <= 60 else defaults["grace_minutes"],
        "weekdays": sorted({day for day in weekdays if type(day) is int and day in _DIAS})
        if isinstance(weekdays, list) else list(defaults["weekdays"]),
        "groups": groups,
        "exceptions": exceptions,
    }


def _linhas_membros(text, label, errors):
    members = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        if line.count("|") > 1:
            errors.append(f"Na linha {number} do {label}, use o nome ou ID | Nome.")
            continue
        if "|" in line:
            identifier, name = line.split("|")
            member = _membro({"id": identifier, "name": name})
        else:
            member = _membro({"name": line})
        if member:
            members.append(member)
        else:
            errors.append(f"Na linha {number} do {label}, informe o ID ou o nome do atendente.")
    return members


def _excecoes_editor(st, current, key, groups):
    import pandas as pd

    fields = list(_CAMPOS_EXCECAO)
    rows = [{**entry, "date": dt.date.fromisoformat(entry["date"])} for entry in current]
    frame = pd.DataFrame(rows, columns=fields).astype({field: "string" for field in fields[1:]})
    frame["date"] = pd.Series(frame["date"], dtype="datetime64[us]")
    edited = st.data_editor(
        frame,
        num_rows="dynamic",
        hide_index=True,
        key=key,
        column_config={
            "date": st.column_config.DateColumn("Data", format="DD/MM/YYYY", required=True),
            "group": st.column_config.SelectboxColumn("Grupo", options=list(groups)),
            "agent_id": st.column_config.TextColumn("ID G4Flex"),
            "agent_name": st.column_config.TextColumn("Nome no G4Flex"),
            "window": st.column_config.SelectboxColumn(
                "Intervalo", options=["Lanche manhã", "Almoço", "Lanche tarde"]
            ),
        },
    )
    return edited.astype(object).where(edited.notna(), None).to_dict("records")


def render_escala(st, value, profile_id):
    """Valida todos os campos juntos e devolve a escala para gravação pelo painel."""
    current = normalizar_escala(value)
    key = f"g4flex_escala_{profile_id}"
    groups = {group["label"]: group["id"] for group in current["groups"]}
    windows = {window["label"]: window["id"] for group in current["groups"] for window in group["windows"]}
    group_labels = {identifier: label for label, identifier in groups.items()}
    window_labels = {identifier: label for label, identifier in windows.items()}
    displayed_exceptions = [
        {**entry, "group": group_labels.get(entry.get("group")), "window": window_labels.get(entry.get("window"))}
        for entry in current["exceptions"]
    ]
    with st.expander("Escala de pausas por grupo"):
        with st.form(key):
            enabled = st.checkbox(
                "Exibir grupos e avisos de pausa no Layout S&S", value=current["enabled"],
                key=f"{key}_enabled",
            )
            grace = st.number_input(
                "Tolerância para o aviso (minutos)", min_value=0, max_value=60, step=1,
                value=current["grace_minutes"], key=f"{key}_grace",
            )
            weekdays = st.multiselect(
                "Dias em que os avisos devem aparecer", options=list(_DIAS),
                default=current["weekdays"], format_func=_DIAS.__getitem__, key=f"{key}_weekdays",
            )
            entries = []
            for group in current["groups"]:
                st.markdown(f"**{group['label']}**")
                columns = st.columns(len(group["windows"]))
                periods = [
                    column.text_input(
                        window["label"], value=f"{window['start']}–{window['end']}",
                        key=f"{key}_{group['id']}_{window['id']}",
                        help="Informe o início e o fim em formato como 10:00–10:15, no horário de Fortaleza.",
                    )
                    for column, window in zip(columns, group["windows"])
                ]
                members = st.text_area(
                    f"Atendentes do {group['label']}",
                    value="\n".join(
                        f"{member['id']} | {member.get('name', '')}" if member.get("id") else member["name"]
                        for member in group["members"]
                    ),
                    key=f"{key}_{group['id']}_membros",
                    help="Uma identificação por linha. Use o nome como aparece no painel ou ID | Nome quando souber o ID.",
                )
                entries.append((group, periods, members))
            st.markdown("**Exceções de pausa**")
            st.caption(
                "Informe uma data. Para limitar a exceção, preencha grupo, atendente ou intervalo. "
                "Uma linha com apenas a data suspende os avisos daquele dia."
            )
            exceptions = _excecoes_editor(st, displayed_exceptions, f"{key}_excecoes", groups)
            submitted = st.form_submit_button("Aplicar escala")
        if not submitted:
            return current

        errors = []
        chosen_groups = []
        assigned = {}
        for group, periods, text in entries:
            label = group["label"]
            members = _linhas_membros(text, label, errors)
            for member in members:
                member_key = _chave_membro(member)
                previous = assigned.setdefault(member_key, label)
                if previous != label:
                    errors.append(f"{member.get('name') or member['id']} já pertence ao {previous}.")
            chosen_windows = []
            for window, period in zip(group["windows"], periods):
                match = _INTERVALO.fullmatch(period)
                if not match or match[1] >= match[2]:
                    errors.append(f"Em {label} · {window['label']}, use HH:MM–HH:MM com início anterior ao fim.")
                    continue
                chosen_windows.append({**window, "start": match[1], "end": match[2]})
            if _conflito_horarios(chosen_windows):
                errors.append(f"Remova a sobreposição entre os intervalos do {label}.")
            chosen_groups.append({**group, "members": members, "windows": chosen_windows})

        chosen_exceptions = []
        for index, row in enumerate(exceptions, start=1):
            if not any(row.values()):
                continue
            date = row["date"]
            if isinstance(date, dt.datetime):
                date = date.date()
            entry = _excecao({
                **row,
                "date": date.isoformat() if isinstance(date, dt.date) else _texto(date),
                "group": groups.get(row["group"], row["group"]),
                "window": windows.get(row["window"], row["window"]),
            }, group_labels, window_labels)
            if entry is None:
                errors.append(f"Confira a data, o grupo e o intervalo na linha {index} das exceções.")
            else:
                chosen_exceptions.append(entry)
        if errors:
            for message in dict.fromkeys(errors):
                st.error(message)
            return current
        return normalizar_escala({
            "enabled": enabled,
            "grace_minutes": int(grace),
            "weekdays": weekdays,
            "groups": chosen_groups,
            "exceptions": chosen_exceptions,
        })
