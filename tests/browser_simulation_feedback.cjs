/* Browser regression test; requires Playwright with Chromium installed.
   Run: node tests/browser_simulation_feedback.cjs
   PLAYWRIGHT_MODULE may point to an existing Playwright installation. */
const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const {once} = require('node:events');
const readline = require('node:readline');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..');
const server = spawn(process.env.PYTHON || 'python3', ['-u', '-c', `
import json,sys,tempfile
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'web'))
from server import App, make_server, Simulation
with tempfile.TemporaryDirectory() as temporary:
    app=App(Path(temporary)/'data', codex='unavailable-test-cli')
    project=app.create('Browser feedback fixture')
    workspace=app.directory(project['id'])/'workspace'
    engine=Simulation(workspace)
    config={'candidate_id':'first-flow','candidate_version':'v1','question':'Compare recorded feedback',
        'max_rounds':2,'baseline':{},'participants':[{'id':pid,'role':role,'goals':['Understand'],
        'constraints':[],'knowledge':[],'basis':['Synthetic test fixture'],'resources':{}}
        for pid,role in [('a','Learner'),('b','Teacher'),('c','Observer'),('d','Skeptic')]]}
    run=engine.create(config)['run_id']
    for actor in ('a','b','c','d'):
        engine.apply(run, {'event_id':'trial-'+actor,'actor_id':actor,'type':'try','reason':'First round '+actor})
    engine.advance(run)
    engine.apply(run, {'event_id':'question','actor_id':'a','type':'ask','target_id':'b',
        'content':'How does this work? <img src=x onerror="window.injected=true">','reason':'Need an example'})
    engine.apply(run, {'event_id':'reply','actor_id':'b','type':'share','target_id':'a',
        'content':'Start with the example.','reason':'Answer the learner'})
    engine.apply(run, {'event_id':'adoption','actor_id':'c','type':'adopt','reason':'Clear after trying'})
    engine.apply(run, {'event_id':'rejection','actor_id':'d','type':'reject','reason':'Too much effort'})
    engine.advance(run)
    config['candidate_id']='second-flow'
    empty=engine.create(config)['run_id']
    http=make_server(app,0)
    print(json.dumps({'base':'http://127.0.0.1:'+str(http.server_port),'project':project['id'],'run':run,'empty':empty}),flush=True)
    try: http.serve_forever()
    except KeyboardInterrupt: pass
    finally: http.server_close()
`], {cwd:root, stdio:['ignore','pipe','inherit']});
(async()=>{
  let browser;
  const startup = readline.createInterface({input:server.stdout});
  try {
    const [line] = await Promise.race([once(startup,'line'), once(server,'exit').then(()=>{throw new Error('Fixture server exited');})]);
    const fixture=JSON.parse(line);
    browser=await chromium.launch();
    const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];
    page.on('pageerror',error=>errors.push(error.message));
    await page.addInitScript(id=>localStorage.setItem('contest-project',id),fixture.project);
    // Exercise old-server compatibility: the file listing remains the source of run paths.
    await page.route('**/api/projects/'+fixture.project,async route=>{
      const response=await route.fetch(),data=await response.json();delete data.simulations;
      await route.fulfill({response,json:data});
    });
    await page.goto(fixture.base);
    await page.locator('.feedback-open').waitFor({state:'attached'});
    await page.locator('#simulation-section').evaluate(el=>el.open=true);
    await page.locator('.feedback-open').click();
    await page.waitForFunction(()=>document.querySelectorAll('#feedback-run option').length===2);
    await page.locator('#feedback-run').selectOption(`simulations/${fixture.run}/run.json`);
    assert.equal(await page.locator('.feedback-event').count(),8);
    assert.match(await page.locator('#feedback-content').innerText(),/미정에서 채택/);
    assert.match(await page.locator('#feedback-content').innerText(),/미정에서 거절/);
    await page.locator('#feedback-kind').selectOption('messages');
    assert.equal(await page.locator('.feedback-event').count(),2);
    assert.match(await page.locator('.feedback-event').first().innerText(),/받는 사람: Teacher \(b\)/);
    assert.match(await page.locator('.feedback-message').first().innerText(),/<img src=x/);
    assert.equal(await page.locator('#feedback-content img').count(),0);
    assert.equal(await page.evaluate(()=>window.injected),undefined);
    await page.locator('#feedback-person').selectOption('b');
    assert.equal(await page.locator('.feedback-event').count(),2,'Include received and sent messages');
    await page.locator('#feedback-round').selectOption('1');
    assert.equal(await page.locator('.feedback-event').count(),0);
    await page.locator('#feedback-round').selectOption('2');
    await page.locator('#refresh-feedback').click();
    await page.waitForFunction(()=>!document.querySelector('#refresh-feedback').disabled);
    await page.waitForTimeout(2200); // Normal project polling must preserve the open viewer and filters.
    assert.equal(await page.locator('#feedback-person').inputValue(),'b');
    assert.equal(await page.locator('#feedback-round').inputValue(),'2');
    assert.equal(await page.locator('.feedback-event').count(),2);
    const download=page.waitForEvent('download');await page.locator('#feedback-download').click();
    assert.equal((await download).suggestedFilename(),'run.json');
    await page.locator('#feedback-run').selectOption(`simulations/${fixture.empty}/run.json`);
    assert.match(await page.locator('#feedback-content').innerText(),/아직 기록된 참여자 행동이 없습니다/);
    await page.locator('#feedback-run').selectOption(`simulations/${fixture.run}/run.json`);
    await page.setViewportSize({width:390,height:844});
    assert.equal(await page.locator('#simulation-feedback-dialog').evaluate(el=>el.scrollWidth>el.clientWidth),false);
    // A read error must not display an earlier run's feedback as if it were current.
    await page.route('**/file?*',route=>route.fulfill({status:404,json:{error:'Missing test snapshot'}}));
    await page.locator('#refresh-feedback').click();
    await page.waitForFunction(()=>!document.querySelector('#refresh-feedback').disabled);
    assert.match(await page.locator('#feedback-status').innerText(),/2개 기록을 읽지 못했습니다/);
    assert.equal(await page.locator('.feedback-event').count(),0);
    assert.deepEqual(errors,[]);
    console.log('PASS: run/person/round filters, sent/received dialogue, original reasons, decision changes, refresh, download, missing records, HTML safety, mobile layout.');
  } finally {
    if(browser)await browser.close();startup.close();
    const exited=once(server,'exit');server.kill('SIGINT');await exited;
  }
})().catch(error=>{console.error(error);process.exitCode=1;});
