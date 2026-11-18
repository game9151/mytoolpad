/* MyToolPad shared behaviour: theme, fuzzy tool search, My Pad (pins + recents), offline. */
(function(){
'use strict';
var TOOLS=window.MTP_TOOLS||[],CATS=window.MTP_CATS||[];
var root=document.documentElement;
var store={get:function(k,d){try{var v=localStorage.getItem(k);return v===null?d:v}catch(e){return d}},
  set:function(k,v){try{localStorage.setItem(k,v)}catch(e){}},
  list:function(k){try{return JSON.parse(localStorage.getItem(k)||'[]')}catch(e){return []}},
  setList:function(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}};
function el(tag,attrs,html){var e=document.createElement(tag);for(var k in attrs||{})e.setAttribute(k,attrs[k]);if(html!=null)e.innerHTML=html;return e}
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
var catName={};CATS.forEach(function(c){catName[c.id]=c.n});

/* ---------- theme ---------- */
var ACCENTS=[['lime','#c8f135','Lime'],['sky','#5cc8ff','Sky'],['amber','#ffb347','Amber'],['pink','#ff8ac2','Pink'],['mint','#5cdb9a','Mint']];
var mq=window.matchMedia?matchMedia('(prefers-color-scheme: light)'):null;
function applyTheme(){
  var t=store.get('mtp-theme','dark');if(t==='auto')t=mq&&mq.matches?'light':'dark';
  root.setAttribute('data-theme',t);root.setAttribute('data-accent',store.get('mtp-accent','lime'));
  var m=document.querySelector('meta[name=theme-color]');if(m)m.setAttribute('content',t==='light'?'#f5f4ef':'#0f0f0f');
}
if(mq&&mq.addEventListener)mq.addEventListener('change',function(){if(store.get('mtp-theme','dark')==='auto')applyTheme()});
applyTheme();
var pop=null,popBtn=null;
function closePop(){if(pop){pop.remove();pop=null;if(popBtn){popBtn.setAttribute('aria-expanded','false');popBtn.focus()}}}
function openPop(btn){
  if(pop){closePop();return}
  popBtn=btn;btn.setAttribute('aria-expanded','true');
  var t=store.get('mtp-theme','dark'),a=store.get('mtp-accent','lime');
  pop=el('div',{'class':'mtp-pop',role:'dialog','aria-label':'Theme and colour'},
    '<h2 id="mtp-th">Theme</h2><div class="mtp-seg" role="group" aria-labelledby="mtp-th">'+
    [['dark','Dark'],['light','Light'],['auto','Auto']].map(function(o){return '<button type="button" data-t="'+o[0]+'" aria-pressed="'+(t===o[0])+'">'+o[1]+'</button>'}).join('')+
    '</div><h2 id="mtp-ac">Accent colour</h2><div class="mtp-sw" role="group" aria-labelledby="mtp-ac">'+
    ACCENTS.map(function(o){return '<button type="button" data-a="'+o[0]+'" aria-pressed="'+(a===o[0])+'" aria-label="'+o[2]+'" title="'+o[2]+'" style="background:'+o[1]+'"></button>'}).join('')+
    '</div><p>Auto follows your device. Saved on this device only.</p>');
  document.body.appendChild(pop);
  pop.addEventListener('click',function(e){
    var b=e.target.closest('button');if(!b)return;
    if(b.dataset.t){store.set('mtp-theme',b.dataset.t);pop.querySelectorAll('[data-t]').forEach(function(x){x.setAttribute('aria-pressed',x===b)})}
    if(b.dataset.a){store.set('mtp-accent',b.dataset.a);pop.querySelectorAll('[data-a]').forEach(function(x){x.setAttribute('aria-pressed',x===b)})}
    applyTheme();
  });
  var first=pop.querySelector('[aria-pressed=true]')||pop.querySelector('button');first&&first.focus();
}
document.addEventListener('click',function(e){
  var b=e.target.closest('[data-mtp-theme]');
  if(b){openPop(b);return}
  if(pop&&!pop.contains(e.target))closePop();
});

/* ---------- fuzzy search ---------- */
function norm(s){return String(s||'').toLowerCase().normalize('NFKD').replace(/[̀-ͯ]/g,'').replace(/[^a-z0-9%$]+/g,' ').trim()}
function dist(a,b,max){ // optimal string alignment distance with early exit
  var la=a.length,lb=b.length;if(Math.abs(la-lb)>max)return max+1;
  var prev2=null,prev=[],cur;for(var j=0;j<=lb;j++)prev[j]=j;
  for(var i=1;i<=la;i++){cur=[i];var rowMin=i;
    for(j=1;j<=lb;j++){var c=a[i-1]===b[j-1]?0:1;var v=Math.min(prev[j]+1,cur[j-1]+1,prev[j-1]+c);
      if(prev2&&i>1&&j>1&&a[i-1]===b[j-2]&&a[i-2]===b[j-1])v=Math.min(v,prev2[j-2]+1);
      cur[j]=v;if(v<rowMin)rowMin=v}
    if(rowMin>max)return max+1;prev2=prev;prev=cur}
  return prev[lb];
}
TOOLS.forEach(function(t){
  t._name=norm(t.n+' '+t.s);
  t._words=norm(t.n+' '+t.s+' '+t.k+' '+t.c.map(function(c){return catName[c]||c}).join(' ')).split(' ');
  t._desc=norm(t.d).split(' ');
});
function tokenScore(tok,words,weight){
  var best=0,allow=tok.length<=3?0:tok.length<=5?1:2;
  for(var i=0;i<words.length;i++){var w=words[i];if(!w)continue;var s=0;
    if(w===tok)s=30;
    else if(w.indexOf(tok)===0)s=24;
    else if(tok.length>=3&&w.indexOf(tok)>0)s=14;
    else if(allow){var d=Math.min(dist(tok,w,allow),w.length>tok.length?dist(tok,w.slice(0,tok.length),allow):9);if(d<=allow)s=20-7*d}
    if(s>best)best=s}
  return best*weight;
}
function score(t,q){
  var qn=norm(q);if(!qn)return 0;
  var s=0;
  if(t._name.indexOf(qn)===0)s+=60;else if(t._name.indexOf(qn)>-1)s+=40;
  var toks=qn.split(' '),miss=0;
  toks.forEach(function(tok){var a=tokenScore(tok,t._words,1),b=tokenScore(tok,t._desc,.45);var m=Math.max(a,b);if(!m)miss++;s+=m});
  if(miss===toks.length)return 0;
  return s-miss*18;
}
function search(q,limit){
  return TOOLS.map(function(t){return{t:t,s:score(t,q)}}).filter(function(r){return r.s>12}).sort(function(a,b){return b.s-a.s}).slice(0,limit||12).map(function(r){return r.t});
}
window.MTP_search=search;

/* ---------- search palette ---------- */
var back=null,lastFocus=null;
function openPalette(){
  if(back)return;lastFocus=document.activeElement;
  back=el('div',{'class':'mtp-pal-back'});
  back.innerHTML='<div class="mtp-pal" role="dialog" aria-modal="true" aria-label="Search tools"><div class="mtp-pal-in">'+
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>'+
    '<input type="search" placeholder="Search tools… typos are fine" aria-label="Search tools" role="combobox" aria-expanded="true" aria-controls="mtp-pal-list" aria-autocomplete="list" autocomplete="off" spellcheck="false"/></div>'+
    '<ul class="mtp-pal-list" id="mtp-pal-list" role="listbox"></ul>'+
    '<div class="mtp-pal-foot"><span>↑ ↓ to move</span><span>Enter to open</span><span>Esc to close</span></div></div>';
  document.body.appendChild(back);document.body.style.overflow='hidden';
  var input=back.querySelector('input'),list=back.querySelector('ul'),sel=0,items=[];
  function render(){
    var q=input.value.trim();
    items=q?search(q,10):recentTools().concat(TOOLS.filter(function(t){return recentTools().indexOf(t)<0})).slice(0,8);
    sel=0;
    if(!items.length){list.innerHTML='<li class="mtp-pal-empty">No tools match “'+esc(q)+'”. Try a shorter word.</li>';input.removeAttribute('aria-activedescendant');return}
    list.innerHTML=items.map(function(t,i){return '<li role="presentation"><a role="option" id="mtp-o'+i+'" href="'+t.f+'" aria-selected="'+(i===0)+'"><span class="mtp-pal-ic" aria-hidden="true">'+esc(t.i)+'</span><span><div class="mtp-pal-t">'+esc(t.n)+'</div><div class="mtp-pal-d">'+esc(t.d)+'</div></span><span class="mtp-pal-c">'+esc(catName[t.c[0]]||'')+'</span></a></li>'}).join('');
    input.setAttribute('aria-activedescendant','mtp-o0');
  }
  function move(d){if(!items.length)return;sel=(sel+d+items.length)%items.length;
    list.querySelectorAll('a').forEach(function(a,i){a.setAttribute('aria-selected',i===sel)});
    var a=list.querySelector('#mtp-o'+sel);input.setAttribute('aria-activedescendant','mtp-o'+sel);a&&a.scrollIntoView({block:'nearest'})}
  input.addEventListener('input',render);
  input.addEventListener('keydown',function(e){
    if(e.key==='ArrowDown'){e.preventDefault();move(1)}
    else if(e.key==='ArrowUp'){e.preventDefault();move(-1)}
    else if(e.key==='Enter'&&items[sel]){e.preventDefault();location.href=items[sel].f}
    else if(e.key==='Tab'){e.preventDefault()}
  });
  back.addEventListener('mousedown',function(e){if(e.target===back)closePalette()});
  render();input.focus();
}
function closePalette(){if(!back)return;back.remove();back=null;document.body.style.overflow='';lastFocus&&lastFocus.focus&&lastFocus.focus()}
document.addEventListener('click',function(e){if(e.target.closest('[data-mtp-search]')){e.preventDefault();openPalette()}});
document.addEventListener('keydown',function(e){
  if(e.key==='Escape'){if(back){closePalette();return}if(pop){closePop();return}}
  var tag=(e.target.tagName||'').toLowerCase(),typing=tag==='input'||tag==='textarea'||tag==='select'||e.target.isContentEditable;
  if((e.key==='k'||e.key==='K')&&(e.metaKey||e.ctrlKey)){e.preventDefault();back?closePalette():openPalette();return}
  if(e.key==='/'&&!typing&&!back&&!e.metaKey&&!e.ctrlKey&&!e.altKey){
    var hs=document.getElementById('mtp-q');e.preventDefault();if(hs){hs.focus();hs.select()}else openPalette();
  }
});

/* ---------- My Pad: pins + recents ---------- */
function byFile(f){for(var i=0;i<TOOLS.length;i++)if(TOOLS[i].f===f)return TOOLS[i];return null}
function pins(){return store.list('mtp-pins').filter(byFile)}
function recentTools(){return store.list('mtp-recent').map(byFile).filter(Boolean)}
function setPinned(f,on){var p=pins().filter(function(x){return x!==f});if(on)p.unshift(f);store.setList('mtp-pins',p.slice(0,24));syncPins()}
function syncPins(){
  var p=pins();
  document.querySelectorAll('[data-pin]').forEach(function(b){b.setAttribute('aria-pressed',p.indexOf(b.dataset.pin)>-1)});
  var nb=document.querySelector('[data-mtp-pin]'),nav=document.querySelector('.mtp-nav[data-tool]');
  if(nb&&nav){var on=p.indexOf(nav.dataset.tool)>-1;nb.setAttribute('aria-pressed',on);nb.setAttribute('aria-label',on?'Unpin this tool from My Pad':'Pin this tool to My Pad');nb.title=on?'Pinned to My Pad':'Pin to My Pad'}
  renderMyPad();
}
document.addEventListener('click',function(e){
  var b=e.target.closest('[data-pin]');
  if(b){e.preventDefault();e.stopPropagation();setPinned(b.dataset.pin,b.getAttribute('aria-pressed')!=='true');return}
  var nb=e.target.closest('[data-mtp-pin]');
  if(nb){var f=document.querySelector('.mtp-nav').dataset.tool;setPinned(f,nb.getAttribute('aria-pressed')!=='true')}
});
var nav=document.querySelector('.mtp-nav[data-tool]');
if(nav){var r=store.list('mtp-recent').filter(function(x){return x!==nav.dataset.tool});r.unshift(nav.dataset.tool);store.setList('mtp-recent',r.slice(0,12))}

function cardHTML(t){
  return '<a href="'+t.f+'" class="tool-card"><div class="tool-icon" aria-hidden="true">'+esc(t.i)+'</div><div class="tool-name">'+esc(t.n)+'</div><div class="tool-desc">'+esc(t.d)+'</div><div class="tool-cta">Open tool →</div>'+
    '<button class="mtp-pin" type="button" data-pin="'+t.f+'" aria-pressed="false" aria-label="Pin '+esc(t.n)+' to My Pad"><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/></svg></button></a>';
}
function renderMyPad(){
  var sec=document.getElementById('mtp-mypad');if(!sec)return;
  var p=pins().map(byFile),seen={};p.forEach(function(t){seen[t.f]=1});
  var rec=recentTools().filter(function(t){return !seen[t.f]}).slice(0,Math.max(0,6-p.length));
  var all=p.concat(rec);
  sec.hidden=!all.length;
  var g=document.getElementById('mtp-mypad-grid'),html=all.map(cardHTML).join('');
  if(g.innerHTML!==html)g.innerHTML=html;
  var pp=pins();g.querySelectorAll('[data-pin]').forEach(function(b){b.setAttribute('aria-pressed',pp.indexOf(b.dataset.pin)>-1)});
}

/* ---------- home search ---------- */
var hq=document.getElementById('mtp-q');
if(hq){
  var res=document.getElementById('mtp-results'),grid=document.getElementById('mtp-results-grid'),browse=document.getElementById('mtp-browse'),none=document.getElementById('mtp-noresults');
  var run=function(){
    var q=hq.value.trim();
    if(!q){res.hidden=true;browse.hidden=false;return}
    var r=search(q,24);res.hidden=false;browse.hidden=true;
    grid.innerHTML=r.map(cardHTML).join('');none.hidden=!!r.length;syncPins();
  };
  hq.addEventListener('input',run);
  hq.addEventListener('keydown',function(e){if(e.key==='Enter'){var a=grid.querySelector('a');if(a){e.preventDefault();location.href=a.getAttribute('href')}}if(e.key==='Escape'){hq.value='';run()}});
  var qs=new URLSearchParams(location.search).get('q');if(qs){hq.value=qs;run()}
}
syncPins();

/* ---------- offline support ---------- */
if('serviceWorker' in navigator&&location.protocol==='https:'){
  window.addEventListener('load',function(){navigator.serviceWorker.register('/sw.js').catch(function(){})});
}
})();
