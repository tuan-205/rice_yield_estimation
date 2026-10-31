import {mockPrediction} from './prediction-fixture.mjs';
import fs from 'node:fs';import assert from 'node:assert/strict';import {JSDOM} from 'jsdom';
const dom=new JSDOM(fs.readFileSync(new URL('../dist/index.html',import.meta.url),'utf8'),{url:'http://127.0.0.1:8080/'});
globalThis.window=dom.window;globalThis.document=dom.window.document;globalThis.URL=dom.window.URL;
dom.window.HTMLDialogElement.prototype.showModal=function(){this.open=true};dom.window.HTMLDialogElement.prototype.close=function(){this.open=false};
let monthlyURL='';globalThis.fetch=async (url,options)=>{if(String(url).endsWith('/v1/predict'))return mockPrediction(options);
 if(String(url)==='/health')return {ok:true,json:async()=>({service:'lua-lab-gee-api',gee_configured:true})};
 if(String(url).endsWith('/v1/monthly')){monthlyURL=String(url);return {ok:false,json:async()=>({detail:'Test server: GEE permission not granted'})};}
 return {ok:true,json:async()=>JSON.parse(fs.readFileSync(new URL('../dist/data/'+String(url).split('/').pop(),import.meta.url),'utf8'))};};
const $=id=>document.getElementById(id);async function until(fn){for(let i=0;i<100;i++){if(fn())return;await new Promise(r=>setTimeout(r,20));}throw Error('UI timeout')}
await import('../dist/app.js');await until(()=>$('api-url').value==='http://127.0.0.1:8080');
assert.match($('api-message').textContent,/Không cần nhập/);
$('mode-new').click();$('estimate-form').dispatchEvent(new dom.window.Event('submit',{cancelable:true}));await until(()=>monthlyURL!=='');
assert.equal(monthlyURL,'http://127.0.0.1:8080/v1/monthly');await until(()=>$('form-message').textContent.includes('permission not granted'));assert.equal($('yield-value').textContent,'—');
assert.equal(document.querySelectorAll('input[type=file]').length,1);assert.equal($('csv-file').accept,'.csv,text/csv');
$('api-url').value='';$('test-api').click();await until(()=>$('api-message').textContent.includes('Hãy nhập URL'));
console.log('PASS: same-origin auto connection, no API URL entry, denied GEE produces no result, no credential upload control, friendly blank URL error.');
