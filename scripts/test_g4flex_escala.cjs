const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const scale = require('./g4flex_escala.js');
const { defaults, normalize, groupFor, agentKey, currentWindows, createTracker } = scale;

const agent = { id: 42, nome: 'Neydson Rodrigues', status: 'ativo' };
const key = agentKey(agent);
const active = (at, options = {}) => ({ ...agent, ...options, at });
const snapshot = (...agents) => ({
    capturado_em: agents[0]?.at,
    status: 'online',
    atendentes: agents.map(({ at, ...item }) => item),
});
const lunch = '2026-11-24T16:';
const time = (minute, second = '00') => lunch + minute + ':' + second + 'Z';

assert.equal(groupFor({ nome: '  CÉLIO   Neto ' }), '1');
assert.equal(groupFor({ nome: 'Vinicius Ferreira' }), '1');
assert.equal(groupFor({ nome: 'Andre Bitu' }), '2');
assert.equal(groupFor({ nome: 'Outros Ferreira' }), null);
assert.equal(groupFor({ nome: 'Desconhecido' }), null);
assert.equal(groupFor({ nome: 'Desconhecido' }, { groups: {} }), null);
const custom = normalize({ groups: [{ id: '1', members: [{ id: '42', name: 'Neydson Rodrigues' }] }] });
assert.equal(groupFor(agent, custom), '1');
assert.equal(groupFor({ ...agent, id: 100 }, custom), '2');
assert.equal(groupFor(agent, { enabled: false }), null);
assert.equal(currentWindows(defaults, time('00')).get('2').reason, 'Almoço');
assert.equal(currentWindows(defaults, time('00')).has('1'), false);
assert.equal(currentWindows(defaults, '2026-11-24T13:15:00Z').get('2').id, 'lanche-manha');
assert.equal(currentWindows(defaults, '2026-11-24T18:15:00Z').get('2').id, 'lanche-tarde');
assert.equal(currentWindows(defaults, '2026-11-28T16:10:00Z').size, 0);
assert.equal(currentWindows({ weekdays: [6] }, '2026-11-28T16:10:00Z').get('2').reason, 'Almoço');

const tracker = createTracker();
const read = (at, props, now = at) => tracker.update(snapshot(active(at, props)), defaults, { now });
assert.equal(read(time('04', '59')).size, 0);
assert.equal(read(time('04', '59'), {}, time('05', '02')).size, 0);
assert.equal(read(time('05')).get(key).id, 'almoco');
assert.equal(read(time('05'), {}, time('05', '40')).has(key), true);
assert.equal(read(time('05'), {}, time('05', '41')).size, 0);
assert.equal(tracker.update(snapshot(active(time('05', '20'))), defaults, { now: time('05', '20'), online: false }).size, 0);
assert.equal(read(time('06'), { status: 'pausado', motivo_pausa: 'Atendimento' }).has(key), true);
assert.equal(read(time('07'), { status: 'pausado', motivo_pausa: 'Motivo não informado' }).size, 0);
assert.equal(read(time('08'), { status: 'desconhecido' }).size, 0);
assert.equal(read(time('09'), { status: 'pausado', motivo_pausa: '  ALMOÇO ' }).size, 0);
assert.equal(read(time('10')).size, 0);
assert.equal(read(time('07')).size, 0);
assert.equal(tracker.update(snapshot(active('2026-11-24T18:20:00Z')), defaults, {
    now: '2026-11-24T18:20:00Z',
}).get(key).id, 'lanche-tarde');

const lifecycle = createTracker();
const initialPause = snapshot(active(time('01'), { status: 'pausado', motivo_pausa: 'Almoço' }));
assert.equal(lifecycle.update(initialPause, defaults, { now: time('01') }).size, 0);
assert.equal(lifecycle.update(snapshot(active(time('20'))), defaults, { now: time('20') }).size, 0);
assert.equal(lifecycle.update(snapshot(active('2026-11-25T16:07:00Z')), defaults, { now: '2026-11-25T16:07:00Z' }).has(key), true);

const at = time('15');
const row = snapshot(active(at));
const evaluate = (config = defaults, data = row, now = at) => createTracker().update(data, config, { now });
assert.equal(evaluate({ grace_minutes: 20 }).size, 0);
assert.equal(evaluate({ exceptions: [{ date: '2026-11-24' }] }).size, 0);
assert.equal(evaluate({ exceptions: [{ date: '2026-11-24', group: '2', agent_id: '42', window: 'almoco' }] }).size, 0);
assert.equal(evaluate({ exceptions: [{ date: '2026-11-24', agent_name: 'NEYDSON  RODRIGUES' }] }).size, 0);
assert.equal(evaluate({ exceptions: [{ date: '2026-11-24', group: '1' }] }).has(key), true);
assert.equal(evaluate(defaults, { ...row, status: 'offline' }).size, 0);
assert.equal(evaluate(defaults, { ...row, atendentes: [] }).size, 0);
assert.equal(evaluate(defaults, { ...row, atendentes: [agent, agent] }).size, 0);
assert.equal(evaluate(defaults, {
    ...row,
    resumo: { voz_status: 'online' },
    atendentes: [{ ...agent, voz_status: 'em_ligacao' }],
}).size, 0);
assert.equal(evaluate(defaults, { ...row, resumo: { voz_status: 'offline' }, atendentes: [{ ...agent, voz_status: 'em_ligacao' }] }).has(key), true);
assert.equal(evaluate(defaults, { ...row, recebido_em: at, capturado_em: time('10') }).size, 0);
assert.equal(evaluate(defaults, snapshot(active(time('59', '58'))), '2026-11-24T17:00:00Z').size, 0);

const browser = vm.createContext({ G4FlexEscalaPadrao: defaults });
vm.runInContext(fs.readFileSync(path.join(__dirname, 'g4flex_escala.js'), 'utf8'), browser);
assert.equal(vm.runInContext("G4FlexEscala.groupFor({ nome: 'André Bitu' })", browser), '2');
console.log('OK: grupos, Fortaleza, janelas e pausas, snapshots, exceções, voz e uso no navegador.');
