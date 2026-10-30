// Styled, keyboard-accessible listboxes mirror native selects, keeping form logic intact.
const controls=new Map();
export function closeSelects(except){for(const [select,c] of controls)if(select!==except){c.list.hidden=true;c.wrapper.classList.remove('is-open','open-upward');c.button.setAttribute('aria-expanded','false');c.button.removeAttribute('aria-activedescendant');}}
export function refreshSelects(){for(const c of controls.values())c.sync();}
export function enhanceSelect(select){
 const wrapper=document.createElement('div');wrapper.className='select-control';wrapper.id=select.id+'-control';select.before(wrapper);wrapper.append(select);
 select.setAttribute('aria-hidden','true');select.tabIndex=-1;
 const button=document.createElement('button');button.type='button';button.id=select.id+'-trigger';button.className='select-trigger';button.setAttribute('role','combobox');button.setAttribute('aria-haspopup','listbox');button.setAttribute('aria-expanded','false');
 const label=document.querySelector(`label[for="${select.id}"]`);if(label){label.id=select.id+'-label';label.htmlFor=button.id;button.setAttribute('aria-labelledby',label.id+' '+select.id+'-value');}
 const value=document.createElement('span');value.className='select-value';value.id=select.id+'-value';
 button.append(value);const chevron=document.createElementNS('http://www.w3.org/2000/svg','svg');chevron.setAttribute('viewBox','0 0 12 12');chevron.setAttribute('class','select-chevron');chevron.setAttribute('aria-hidden','true');chevron.innerHTML='<path d="m2 4 4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.5"/>';button.append(chevron);
 const list=document.createElement('ul');list.className='select-list';list.id=select.id+'-list';list.hidden=true;list.setAttribute('role','listbox');button.setAttribute('aria-controls',list.id);if(label)list.setAttribute('aria-labelledby',label.id);
 wrapper.append(button,list);let index=0,search='',searchTime=0;
 const active=()=>{[...list.children].forEach((li,i)=>li.classList.toggle('is-active',i===index));const item=list.children[index];if(item){button.setAttribute('aria-activedescendant',item.id);item.scrollIntoView?.({block:'nearest'});}};
 const choose=i=>{select.selectedIndex=i;select.dispatchEvent(new Event('change',{bubbles:true}));closeSelects();button.focus();};
 const sync=()=>{value.textContent=select.options[select.selectedIndex]?.textContent||'Chọn';button.disabled=select.disabled;list.replaceChildren();[...select.options].forEach((option,i)=>{const li=document.createElement('li');li.className='select-option';li.id=select.id+'-option-'+i;li.setAttribute('role','option');li.setAttribute('aria-selected',String(option.selected));li.textContent=option.textContent;li.addEventListener('click',()=>choose(i));list.append(li);});index=Math.max(0,select.selectedIndex);};
 const open=()=>{closeSelects(select);sync();list.hidden=false;wrapper.classList.add('is-open');const rect=button.getBoundingClientRect();wrapper.classList.toggle('open-upward',window.innerHeight-rect.bottom<220&&rect.top>window.innerHeight-rect.bottom);button.setAttribute('aria-expanded','true');active();};
 button.onclick=()=>{if(list.hidden)open();else closeSelects();};
 button.onkeydown=e=>{
  if(e.key==='Tab'){closeSelects();return;}
  if(e.key==='Escape'){e.preventDefault();closeSelects();return;}
  if(['ArrowDown','ArrowUp','Home','End','Enter',' '].includes(e.key)){
   e.preventDefault();if(list.hidden){open();if(e.key==='Home')index=0;if(e.key==='End')index=select.options.length-1;active();return;}
   if(e.key==='Enter'||e.key===' '){choose(index);return;}
   if(e.key==='Home')index=0;else if(e.key==='End')index=select.options.length-1;else index=Math.max(0,Math.min(select.options.length-1,index+(e.key==='ArrowDown'?1:-1)));active();return;
  }
  if(e.key.length===1&&!e.ctrlKey&&!e.metaKey&&!e.altKey){e.preventDefault();const now=Date.now();search=now-searchTime>700?e.key:search+e.key;searchTime=now;if(list.hidden)open();const found=[...select.options].findIndex(o=>o.textContent.toLocaleLowerCase('vi').startsWith(search.toLocaleLowerCase('vi')));if(found>=0){index=found;active();}}
 };
 select.addEventListener('change',sync);controls.set(select,{wrapper,button,list,sync});sync();
}
document.addEventListener('click',e=>{if(!e.target.closest('.select-control'))closeSelects();});
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeSelects();});
