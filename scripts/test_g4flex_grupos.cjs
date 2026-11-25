const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const scale = require('./g4flex_escala.js');

// Executa a renderização real do painel contra um DOM mínimo, sem browser ou rede.
const source = fs.readFileSync(path.join(__dirname, '..', 'main.py'), 'utf8');
const start = source.indexOf('function ssAgentListRow(');
const end = source.indexOf('function g4fRender(', start);
assert.ok(start >= 0 && end > start, 'As funções de renderização do Layout S&S devem estar no painel');

const g4fText = value => String(value ?? '').replace(/[&<>"]/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;',
})[character]);
const agents = [
    { id: 1, nome: 'Abraão Winston', status: 'ativo', office: 'fortaleza' },
    { id: 2, nome: 'Luis Lima', status: 'ativo', office: 'varzea' },
    { id: 3, nome: 'André Bitu', status: 'pausado', motivo_pausa: 'Almoço', office: 'fortaleza' },
    { id: 4, nome: 'Neydson Rodrigues', status: 'ativo', office: 'fortaleza' },
    { id: 5, nome: 'Atendente sem cadastro', status: 'ativo', office: 'outros' },
];
const cutoff = '2026-11-24T16:05:10Z'; // 13:05 em Fortaleza.
const row = { capturado_em: cutoff, recebido_em: cutoff, status: 'online', atendentes: agents };
const agreement = scale.normalize();
const unassigned = { id: 'sem-grupo', label: 'Sem grupo', windows: [] };
const pending = scale.createTracker().update(row, agreement, { now: cutoff });
const context = vm.createContext({
    document: { activeElement: null },
    window: { matchMedia: () => ({ matches: false }) },
    G4FlexEscala: scale,
    g4fText,
    g4fCurrentLayout: 'ss',
    g4fState: () => 'online',
    g4fAgeSec: () => 0,
    g4fTime: () => '13:05:10',
    g4fLastError: '',
    g4fSearchText: '',
    g4fNumber: value => String(value ?? '—'),
    g4fAvatar: () => '',
    g4fQueueTitle: () => '',
    g4fVisibleAgent: () => true,
    g4fAssignmentAlert: false,
    g4fAssignmentRecentlyChanged: new Map(),
    g4fAgentKey: scale.agentKey,
    ssPauseIcon: () => '',
    ssAlertBell: '',
    ssPhoneActive: () => false,
    ssOfficeOf: agent => agent.office,
    ssSchedule: agreement,
    ssUnassignedGroup: unassigned,
    ssPendingPauses: pending,
    ssViewMode: 'lista',
    ssFocusFilter: 'todos',
    ssOfficeFilter: 'todos',
});
vm.runInContext(source.slice(start, end), context, { filename: 'main.py#LayoutS&S' });
const render = vm.runInContext('ssRender', context);
const panelMarkup = vm.runInContext('ssListPanel', context);

function createNode() {
    const classes = new Set();
    const style = new Map();
    return {
        hidden: false,
        textContent: '',
        innerHTML: '',
        data: new Map(),
        classList: {
            contains: name => classes.has(name),
            toggle: (name, set) => set ? classes.add(name) : classes.delete(name),
        },
        style: { setProperty: (name, value) => style.set(name, value), getPropertyValue: name => style.get(name) },
        querySelector(selector) {
            if (!this.data.has(selector)) this.data.set(selector, createNode());
            return this.data.get(selector);
        },
        querySelectorAll() { return []; },
    };
}

const host = createNode();
const root = host.querySelector('[data-ss="view"]');
const list = root.querySelector('[data-ss="list"]');
const panels = [createNode(), createNode(), createNode()];
list.clientWidth = 1500;
list.clientHeight = 550;
list.querySelectorAll = selector => selector === '[data-ss-list-panel]' ? panels : [];
for (const panel of panels) {
    panel.querySelector('.ss-group-head').getBoundingClientRect = () => ({ height: 42 });
}
const body = index => panels[index].querySelector('tbody').innerHTML;
const count = index => panels[index].querySelector('.ss-group-head__count').textContent;

const headers = agreement.groups.map((item, i) => panelMarkup(i, item).match(/<header\b[\s\S]*?<\/header>/)[0]);
assert.match(headers[0], /Grupo 1/);
assert.match(headers[0], /10:00–10:15/);
assert.match(headers[1], /Grupo 2/);
assert.match(headers[1], /13:00–14:00/);
for (const header of headers) {
    assert.doesNotMatch(header, /pause-pending|Pausa pendente|Almoço pendente|Almoço em andamento/i);
}
assert.match(panelMarkup(2, unassigned), /ss-list-panel--unassigned/);
assert.match(panelMarkup(2, unassigned), /Sem grupo/);
assert.doesNotMatch(panelMarkup(2, unassigned), /ss-group-head__schedule/);

render(host, row, agents, 'online');
assert.equal(count(0), '2 atendentes');
assert.equal(count(1), '2 atendentes');
assert.equal(count(2), '1 atendente');
assert.equal(panels[2].hidden, false);
assert.match(body(0), /Abraão Winston/);
assert.match(body(0), /Luis Lima/);
assert.doesNotMatch(body(0), /André|Neydson|sem cadastro/);
assert.match(body(1), /Em pausa[\s\S]*Almoço/);
const pendingRow = body(1).match(/<tr\b[\s\S]*?<\/tr>/g).find(item => item.includes('Neydson'));
const statusCell = pendingRow.match(/<td><div class="ss-list-status">([\s\S]*?)<\/div><\/td>/)[1];
assert.match(statusCell, /Online/);
assert.match(statusCell, /Online[\s\S]*Almoço pendente/);
assert.equal(pendingRow.match(/Almoço pendente/g).length, 1);
assert.match(pendingRow, /has-pause-pending/);
assert.doesNotMatch(pendingRow, /is-paused/);
const renderRow = vm.runInContext('ssAgentListRow', context);
const pausedPending = renderRow({ ...agents[3], status: 'pausado', motivo_pausa: 'Atendimento' }, row, pending.get('id:4'));
assert.match(pausedPending, /is-paused[^"]*has-pause-pending/);
assert.match(pausedPending, /Em pausa · Atendimento[\s\S]*Almoço pendente/);
const snack = renderRow(agents[3], row, { id: 'lanche-tarde', label: 'Lanche tarde', start: '15:00', end: '15:15' });
assert.match(snack, /Lanche pendente/);
assert.match(body(2), /Atendente sem cadastro/);

context.ssOfficeFilter = 'fortaleza';
render(host, row, agents, 'online');
assert.equal(count(0), '1 atendente');
assert.equal(count(1), '2 atendentes');
assert.match(body(0), /Abraão Winston/);
assert.doesNotMatch(body(0), /Luis Lima|André|Neydson/);
assert.match(body(1), /André Bitu/);
assert.match(body(1), /Neydson Rodrigues/);
assert.equal(panels[2].hidden, true);

context.ssFocusFilter = 'pausado';
list.clientWidth = 780;
list.clientHeight = 300;
context.window.matchMedia = () => ({ matches: true });
render(host, row, agents, 'online');
assert.equal(list.classList.contains('ss-single-column'), true);
assert.equal(host._ssListPages, 1);
assert.equal(panels[1].hidden, false);
assert.match(body(0), /Nenhum atendente/);
assert.match(body(1), /André Bitu/);
assert.doesNotMatch(body(1), /Neydson/);

assert.equal(scale.groupFor({ nome: 'Abhraão Winston' }), '1');
assert.equal(scale.groupFor({ nome: 'Abraão Wniston' }), '1');
assert.equal(scale.groupFor({ nome: 'Rodrigo Carvalho' }), '1');
assert.equal(scale.groupFor({ nome: 'Armando Rodrigues' }), '2');
assert.equal(scale.groupFor({ nome: 'Tafarel Nascimento' }), '2');

console.log('OK: grupos fixos com filtros, Sem grupo, cabeçalhos compactos e alerta no status.');
