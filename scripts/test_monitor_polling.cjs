const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '..', 'main.py'), 'utf8');
function section(from, to) {
    const start = source.indexOf(from);
    const end = source.indexOf(to, start);
    assert.ok(start >= 0 && end > start);
    return source.slice(start, end);
}

async function testSim() {
    const context = vm.createContext({
        URLSearchParams, AbortSignal,
        profile: {id: 'fixture'},
        simAlertSettings: {enabled: true, poll_seconds: 25, supabase_url: 'https://example.test', supabase_publishable_key: 'fixture'},
        localStorage: {
            values: new Map(),
            getItem(key) {return this.values.get(key);},
            setItem(key, value) {this.values.set(key, value);}
        },
        simPollTimer: null, robotHeartbeatStatus: null,
        log() {}, setSimPollStatus() {}, clearInterval() {},
        renderRobotHeartbeat() {},
        enqueueSimAlert(event) {alerts.push(event.event_id);},
        fetchRobotStatus: async () => ({}),
        setInterval(fn, delay) {intervals.push({fn, delay});}
    });
    const alerts = [];
    const intervals = [];
    const requests = [];
    let respond;
    context.fetch = url => {
        requests.push(new URL(url).searchParams);
        return new Promise(resolve => {respond = rows => resolve({ok: true, json: async () => rows});});
    };
    const pollers = vm.runInContext(
        'let pollSimDeliveries, startSimDeliveryPolling;\n' +
        section('            const simReferenceKey=', '            testarUltimaEntregaSIM=async function(){') +
        '\n({pollSimDeliveries,startSimDeliveryPolling})',
        context
    );
    const flush = () => new Promise(resolve => setImmediate(resolve));
    const time = '2026-11-21T20:05:00.000000+00:00';
    const event = id => ({event_id: id, detectado_em: time, municipio: 'Fortaleza'});
    pollers.startSimDeliveryPolling();
    await flush();
    assert.equal(intervals[0].delay, 25000);
    assert.equal(requests[0].get('limit'), '1');
    await pollers.pollSimDeliveries();
    assert.equal(requests.length, 1, 'ciclo em andamento deve ser reaproveitado');
    respond([event('a')]);
    await flush();
    assert.deepEqual(alerts, [], 'primeira leitura deve estabelecer referência sem tocar alerta');

    const polling = intervals[0].fn();
    await flush();
    assert.equal(requests[1].get('order'), 'detectado_em.asc,event_id.asc');
    assert.ok(requests[1].get('or').includes('event_id.gt."a"'));
    respond([event('b'), event('c')]);
    await polling;
    assert.deepEqual(alerts, ['b', 'c']);
    assert.equal(JSON.parse(context.localStorage.getItem('monitor_sim_robot_cursor_fixture')).event_id, 'c');
}

async function testPortal() {
    let now = 10;
    let requests = 0;
    let resolve;
    let reject;
    const read = vm.runInNewContext(
        section('const portalCurrentRequests=', 'async function portalPoll(){') + '\nportalReadCurrent',
        {
            Date: {now: () => now},
            portalServices: {portais: {current: 'fixture'}},
            portalFetchTable() {
                requests++;
                return new Promise((success, failure) => {resolve = success; reject = failure;});
            }
        }
    );
    const view = read('portais');
    assert.equal(read('portais'), view);
    resolve([]);
    await view;
    now += 9000;
    await read('portais');
    assert.equal(requests, 1, 'painel e alerta devem compartilhar a leitura recente');
    now += 4000;
    const failed = read('portais');
    reject(new Error('falha simulada'));
    await assert.rejects(failed, /falha simulada/);
    const recovered = read('portais');
    resolve([]);
    await recovered;
    assert.equal(requests, 3, 'uma falha não deve entrar no cache');
}

async function testComunicados() {
    let now = 100;
    let calls = 0;
    let reject;
    const poll = vm.runInNewContext(
        section('            let comPollLoggedError', '            let comPollRetryAt') +
        'let comPollRetryAt = 0;\n' +
        section('            async function comPolling(){', '            function iniciarComPolling(){') +
        '\ncomPolling',
        {
            Date: {now: () => now},
            log() {},
            comBuscarRecentes() {
                calls++;
                return new Promise((_, failure) => {reject = failure;});
            }
        }
    );
    const pending = poll();
    await poll();
    assert.equal(calls, 1);
    reject(new Error('falha simulada'));
    await pending;
    now += 3000;
    await poll();
    assert.equal(calls, 1, 'erro deve adiar nova tentativa');
    now += 3000;
    const retry = poll();
    assert.equal(calls, 2);
    reject(new Error('segunda falha simulada'));
    await retry;
}

async function main() {
    const opening = section('    sim_poll_cfg = normalizar_sim_alerts', '    components.html(html_painel,');
    assert.ok(!opening.includes('buscar_ultimo_evento_robo_supabase()'));
    assert.ok(opening.indexOf("afterIndexChange('Inicial')") < opening.indexOf('            startSimDeliveryPolling();'));
    await testSim();
    await testPortal();
    await testComunicados();
    console.log('OK: abertura, intervalo e sequência SIM, leitura compartilhada de Portais e espera de Comunicados.');
}
main().catch(error => {console.error(error); process.exitCode = 1;});
