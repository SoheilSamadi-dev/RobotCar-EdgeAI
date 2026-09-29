// Exercise browser input races without a real UNO or browser dependencies.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('tools/web/app.js', 'utf8');
const settle = async () => { for (let i = 0; i < 40; i++) await Promise.resolve(); };
function setup() {
  const calls = [];
  let acquireResolve;
  let commandResolve;
  let delayAcquire = false;
  let delayCommand = false;
  const element = () => ({classList:{toggle(){}, add(){}, remove(){}},
    children:[], scrollTop:0, clientHeight:0, textContent:'',
    get scrollHeight(){return this.children.length * 20;},
    get lastElementChild(){return this.children.at(-1);},
    append(...nodes){for(const node of nodes){node.parent=this;this.children.push(node);}},
    prepend(node){node.parent=this;this.children.unshift(node);},
    remove(){const items=this.parent.children;items.splice(items.indexOf(this),1);},
    replaceChildren(){this.children=[];}, addEventListener(){}});
  const elements = new Map();
  const context = vm.createContext({
    console, AbortController, Date, JSON, Set, CSS:{escape:s=>s},
    setTimeout(){return 1;},clearTimeout(){},setInterval(){return 1;},clearInterval(){},
    document:{hidden:false, addEventListener(){},createElement:element,
      querySelector(s){if(!elements.has(s))elements.set(s,element());return elements.get(s);},
      querySelectorAll(){return [];}},
    window:{addEventListener(){}},
    fetch: async (path, options={}) => {
      const body = options.body ? JSON.parse(options.body) : null;
      calls.push({path,body});
      const response = data => ({ok:true,json:async()=>data});
      if(path.startsWith('/api/status')) return response({connected:true,firmware_ready:true,configuration:{speed:195,curve:75},port:'fake',baud:9600,events:[]});
      if(path==='/api/control') {
        if(delayAcquire) return new Promise(resolve=>{acquireResolve=()=>resolve(response({token:'test-token'}));});
        return response({token:'test-token'});
      }
      if(path==='/api/command' && delayCommand)
        return new Promise(resolve=>{commandResolve=()=>resolve(response({ok:true}));});
      return response({ok:true});
    },
  });
  vm.runInContext(source,context);
  return {calls,run:s=>vm.runInContext(s,context),
    delayAcquire:()=>{delayAcquire=true;},resolveAcquire:()=>acquireResolve(),
    delayCommand:()=>{delayCommand=true;},resolveCommand:()=>commandResolve()};
}
(async()=>{
  {
    const ui=setup();await settle();ui.delayAcquire();
    ui.run('beginMovement("w")');await settle();ui.run('endMovement("w")');
    ui.resolveAcquire();await settle();
    assert(!ui.calls.some(c=>c.path==='/api/command'),'release while acquiring must not move');
    assert(ui.calls.some(c=>c.path==='/api/stop'&&c.body.token==='test-token'));
  }
  {
    const ui=setup();await settle();ui.delayCommand();
    ui.run('beginMovement("w")');await settle();
    ui.run('sendCommand("w", true); sendCommand("w", true)');await settle();
    assert.equal(ui.calls.filter(c=>c.path==='/api/command').length,1,'do not queue heartbeats');
    ui.run('endMovement("w")');await settle();
    assert(ui.calls.some(c=>c.path==='/api/stop'),'stop must bypass an in-flight motion');
    ui.resolveCommand();await settle();assert.equal(ui.run('activeMotion'),null);
  }
  {
    const ui=setup();await settle();ui.run('beginMovement("w")');await settle();
    assert(ui.calls.some(c=>c.path==='/api/command'&&c.body.command==='w'));
    ui.run('sendOneShot("x")');await settle();
    assert(ui.calls.some(c=>c.path==='/api/stop'&&!c.body.token),'emergency stop is global');
    assert.equal(ui.run('activeMotion'),null);
  }
  {
    const ui=setup();await settle();ui.run('sendOneShot("5")');await settle();
    assert(ui.calls.some(c=>c.path==='/api/command'&&c.body.command==='5'));
    assert(ui.calls.some(c=>c.path==='/api/stop'),'one-shot control releases ownership');
  }
  {
    const ui=setup();await settle();
    ui.run('appendEvent({time:"1",level:"info",message:"older"}); appendEvent({time:"2",level:"info",message:"newer"})');
    assert.equal(ui.run('eventLog.children[0].children[2].textContent'),'newer');
    ui.run('for(let i=0;i<160;i++)appendEvent({time:"3",level:"info",message:String(i)})');
    assert.equal(ui.run('eventLog.children.length'),150);
    assert.equal(ui.run('eventLog.children[0].children[2].textContent'),'159');
    assert.equal(ui.run('eventLog.lastElementChild.children[2].textContent'),'10');
  }
  {
    const ui=setup();await settle();ui.run('sendCommand("@c100")');await settle();
    assert(ui.calls.some(c=>c.path==='/api/command'&&c.body.command==='@c100'));
    assert.equal(ui.run('speedValue.textContent'),195);
    assert.equal(ui.run('curveValue.textContent'),'75%');
    ui.run('describeCurve(100)');
    assert(ui.run('curveDetail.textContent').includes('released'));
  }
  console.log('6 browser control tests passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
