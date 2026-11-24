/* Escala de pausas do Layout S&S. Consome exclusivamente o snapshot já recebido. */
const G4FlexEscala = (() => {
    'use strict';

    const defaults = typeof module !== 'undefined' && module.exports
        ? require('./g4flex_escala_padrao.json')
        : globalThis.G4FlexEscalaPadrao;
    const maxSnapshotAge = 40_000;
    const formatter = new Intl.DateTimeFormat('en-CA', {
        timeZone: 'America/Fortaleza',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hourCycle: 'h23',
    });
    const prepared = new WeakSet();
    const clean = value => String(value ?? '').trim();
    const normalizedName = value => clean(value).normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '').replace(/\s+/g, ' ').toLocaleLowerCase('pt-BR');
    const identifier = value => clean(value).toLocaleLowerCase('pt-BR');

    function minuteOf(value) {
        if (!/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(value)) return NaN;
        const [hours, minutes] = value.split(':').map(Number);
        return hours * 60 + minutes;
    }

    function normalizeWindow(window) {
        const { id, label, start, end, reason } = window ?? {};
        if (![id, label, start, end, reason].every(value => typeof value === 'string' && value.trim())) return null;
        const startMinute = minuteOf(start);
        const endMinute = minuteOf(end);
        if (!(startMinute < endMinute)) return null;
        return { id, label, start, end, reason };
    }

    function normalize(config) {
        if (prepared.has(config)) return config;
        const source = config ?? {};
        const selectedGroups = Array.isArray(source.groups) ? source.groups : defaults.groups;
        const groups = defaults.groups.map(fallback => {
            const selected = selectedGroups.find(group => clean(group?.id) === fallback.id) ?? fallback;
            const members = Array.isArray(selected.members) ? selected.members : fallback.members;
            const windows = Array.isArray(selected.windows) ? selected.windows : fallback.windows;
            return {
                id: fallback.id,
                label: clean(selected.label) || fallback.label,
                members: members.map(member => ({ id: clean(member?.id), name: clean(member?.name) }))
                    .filter(member => member.id || member.name),
                windows: windows.map(normalizeWindow).filter(Boolean),
            };
        });
        const weekdays = Array.isArray(source.weekdays) ? source.weekdays : defaults.weekdays;
        const grace = source.grace_minutes ?? defaults.grace_minutes;
        const exceptions = Array.isArray(source.exceptions) ? source.exceptions : defaults.exceptions;
        const result = {
            enabled: source.enabled !== false,
            grace_minutes: Number.isInteger(grace) && grace >= 0 && grace <= 60 ? grace : defaults.grace_minutes,
            weekdays: [...new Set(weekdays.filter(day => Number.isInteger(day) && day >= 1 && day <= 7))],
            groups,
            exceptions: exceptions.filter(entry => /^\d{4}-\d{2}-\d{2}$/.test(entry?.date ?? '')).map(entry => ({
                date: entry.date,
                group: clean(entry.group),
                window: clean(entry.window),
                agent_id: clean(entry.agent_id),
                agent_name: clean(entry.agent_name),
            })),
        };
        prepared.add(result);
        return result;
    }

    function agentKey(agent) {
        const id = identifier(agent?.id);
        const name = normalizedName(agent?.nome);
        return id ? 'id:' + id : name ? 'name:' + name : '';
    }

    function groupFor(agent, config) {
        const { enabled, groups } = normalize(config);
        if (!enabled) return null;
        const id = identifier(agent?.id);
        if (id) {
            const group = groups.find(item => item.members.some(member => identifier(member.id) === id));
            if (group) return group.id;
        }
        const name = normalizedName(agent?.nome);
        if (!name) return null;
        return groups.find(item => item.members.some(member =>
            (!member.id || !id) && normalizedName(member.name) === name
        ))?.id ?? null;
    }

    function localTime(time) {
        const value = new Date(time);
        if (!Number.isFinite(value.getTime())) return null;
        const parts = Object.fromEntries(formatter.formatToParts(value).map(part => [part.type, part.value]));
        const utcMidnight = Date.UTC(Number(parts.year), Number(parts.month) - 1, Number(parts.day));
        return {
            date: [parts.year, parts.month, parts.day].join('-'),
            weekday: new Date(utcMidnight).getUTCDay() || 7,
            minute: Number(parts.hour) * 60 + Number(parts.minute),
        };
    }

    function windowsAt(config, local) {
        const active = new Map();
        if (!local || !config.enabled || !config.weekdays.includes(local.weekday)) return active;
        for (const group of config.groups) {
            const window = group.windows.find(item => minuteOf(item.start) <= local.minute && local.minute < minuteOf(item.end));
            if (window) {
                active.set(group.id, {
                    ...window,
                    date: local.date,
                    startMinute: minuteOf(window.start),
                    endMinute: minuteOf(window.end),
                });
            }
        }
        return active;
    }

    function currentWindows(config, now = Date.now()) {
        return windowsAt(normalize(config), localTime(now));
    }

    function hasException(config, agent, groupId, window) {
        return config.exceptions.some(entry =>
            entry.date === window.date &&
            (!entry.group || entry.group === groupId) &&
            (!entry.window || entry.window === window.id) &&
            (!entry.agent_id || identifier(entry.agent_id) === identifier(agent.id)) &&
            (!entry.agent_name || normalizedName(entry.agent_name) === normalizedName(agent.nome))
        );
    }

    function createTracker() {
        let lastTimestamp = -Infinity;
        let lastDate = '';
        let pending = new Map();
        const completed = new Set();

        return {
            update(row, config, { now = Date.now(), online = true } = {}) {
                const scale = normalize(config);
                const receivedAt = new Date(now).getTime();
                const capturedAt = Date.parse(row?.capturado_em || row?.recebido_em || '');
                const status = identifier(row?.status);
                if (!scale.enabled || !online || (status && !['online', 'ok', 'ativo'].includes(status)) ||
                    !Number.isFinite(receivedAt) || !Number.isFinite(capturedAt) ||
                    receivedAt - capturedAt > maxSnapshotAge || capturedAt > receivedAt + 5000 ||
                    capturedAt < lastTimestamp || !Array.isArray(row?.atendentes)) return new Map();

                const capture = localTime(capturedAt);
                const current = localTime(receivedAt);
                const active = windowsAt(scale, current);
                if (capturedAt > lastTimestamp) {
                    if (capture.date !== lastDate) {
                        completed.clear();
                        lastDate = capture.date;
                    }
                    const capturedWindows = windowsAt(scale, capture);
                    lastTimestamp = capturedAt;
                    pending = new Map();
                    const ambiguous = new Set();
                    const seen = new Set();
                    for (const agent of row.atendentes) {
                        const key = agentKey(agent);
                        if (!key) continue;
                        if (seen.has(key)) ambiguous.add(key);
                        seen.add(key);
                    }
                    for (const agent of row.atendentes) {
                        const key = agentKey(agent);
                        if (!key || ambiguous.has(key)) continue;
                        const group = groupFor(agent, scale);
                        const window = capturedWindows.get(group);
                        if (!window || hasException(scale, agent, group, window)) continue;
                        const pauseKey = [group, window.id, window.start, window.end, key].join('|');
                        const reason = normalizedName(agent.motivo_pausa);
                        if (agent.status === 'pausado' && reason === normalizedName(window.reason)) {
                            completed.add(pauseKey);
                            continue;
                        }
                        if (completed.has(pauseKey) || capture.minute < window.startMinute + scale.grace_minutes) continue;
                        const calling = row.resumo?.voz_status === 'online' && agent.voz_status === 'em_ligacao';
                        const knownPause = agent.status === 'pausado' && reason &&
                            !['nao informado', 'motivo nao informado', 'desconhecido', 'sem motivo', '—', '-'].includes(reason);
                        if (calling || (agent.status !== 'ativo' && !knownPause)) continue;
                        pending.set(key, { ...window, group });
                    }
                }

                // Um snapshot repetido não inicia alerta. Uma janela encerrada não permanece visível.
                return new Map([...pending].filter(([, alert]) => {
                    const window = active.get(alert.group);
                    return window?.date === alert.date && window.id === alert.id &&
                        window.start === alert.start && window.end === alert.end;
                }));
            },
        };
    }

    return { defaults, normalize, agentKey, groupFor, currentWindows, createTracker };
})();

if (typeof module !== 'undefined' && module.exports) module.exports = G4FlexEscala;
