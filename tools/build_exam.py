# -*- coding: utf-8 -*-
"""exam_data.py から受験用HTMLと採点ツールHTMLを生成する。

    python3 tools/build_exam.py

出力:
    exam/営業職適性検査_受験用.html      解答キーを含まない。候補者へ配布する。
    exam/営業職適性検査_採点ツール.html  解答キーを含む。社外秘。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exam_data as D  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "exam")

# ---------------------------------------------------------------- 共通CSS
CSS = """
:root{
  --paper:#F5F7FA; --surface:#FFFFFF; --surface-2:#EDF0F5;
  --ink:#151C26; --ink-2:#4C5867; --ink-3:#7C8796;
  --rule:#D6DCE4; --rule-2:#E7EBF1;
  --indigo:#2E4E7E; --indigo-soft:#E9EEF6;
  --vermilion:#B23A26; --vermilion-soft:#FAEDEA;
  --green:#2F6B4F; --green-soft:#E8F1EC;
  --on-accent:#FFFFFF;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --paper:#10141A; --surface:#161B23; --surface-2:#1D242E;
  --ink:#E3E8EF; --ink-2:#A6B1C0; --ink-3:#78838F;
  --rule:#2A323D; --rule-2:#222933;
  --indigo:#8FB0DC; --indigo-soft:#1A2432;
  --vermilion:#E4836A; --vermilion-soft:#2C1E1A;
  --green:#7FBF9C; --green-soft:#152420;
  --on-accent:#10141A;
}}
:root[data-theme="dark"]{
  --paper:#10141A; --surface:#161B23; --surface-2:#1D242E;
  --ink:#E3E8EF; --ink-2:#A6B1C0; --ink-3:#78838F;
  --rule:#2A323D; --rule-2:#222933;
  --indigo:#8FB0DC; --indigo-soft:#1A2432;
  --vermilion:#E4836A; --vermilion-soft:#2C1E1A;
  --green:#7FBF9C; --green-soft:#152420;
  --on-accent:#10141A;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);
  font-family:"Hiragino Kaku Gothic ProN","Hiragino Sans","Yu Gothic Medium","Yu Gothic",
    "Noto Sans JP",Meiryo,system-ui,sans-serif;
  font-size:15px;line-height:1.85;-webkit-font-smoothing:antialiased}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"Courier New",monospace;
  font-feature-settings:"tnum";font-variant-numeric:tabular-nums}
.wrap{max-width:880px;margin:0 auto;padding:0 24px}
h1,h2,h3{font-family:"Hiragino Mincho ProN","Yu Mincho","Noto Serif JP",serif;
  font-weight:600;letter-spacing:.02em;text-wrap:balance}
a{color:var(--indigo)}
button{font:inherit}
.btn{appearance:none;border:1px solid var(--ink);background:var(--ink);color:var(--surface);
  padding:12px 30px;font-size:15px;font-weight:500;cursor:pointer;transition:opacity .15s}
.btn:hover{opacity:.85}
.btn:disabled{opacity:.4;cursor:not-allowed}
.btn.ghost{background:transparent;color:var(--ink);border-color:var(--rule)}
.btn.accent{background:var(--indigo);border-color:var(--indigo);color:var(--on-accent)}
:focus-visible{outline:2px solid var(--indigo);outline-offset:2px}
.note{border:1px solid var(--rule);border-left:3px solid var(--indigo);
  background:var(--surface);padding:16px 20px;margin:20px 0;font-size:13.5px;
  line-height:1.8;color:var(--ink-2)}
.note.warn{border-left-color:var(--vermilion);background:var(--vermilion-soft)}
.note.ok{border-left-color:var(--green);background:var(--green-soft)}
.note b{color:var(--ink);display:block;margin-bottom:5px;font-size:12px;letter-spacing:.1em}
.kicker{font-size:11.5px;letter-spacing:.18em;color:var(--indigo);margin:0 0 10px}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th,td{text-align:left;padding:10px 14px;border-bottom:1px solid var(--rule-2);vertical-align:top}
thead th{font-size:11px;letter-spacing:.1em;color:var(--ink-3);font-weight:500;
  background:var(--surface-2);border-bottom:1px solid var(--rule);white-space:nowrap}
.tablewrap{overflow-x:auto;border:1px solid var(--rule);background:var(--surface)}
td.num,th.num{text-align:right;white-space:nowrap;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-variant-numeric:tabular-nums}
@media (prefers-reduced-motion:no-preference){html{scroll-behavior:smooth}}
"""


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def qtext(s):
    """設問文は <em> <br> <b> を許可した上で埋め込む。"""
    return s


def part_questions_html(part, offset_note=None, with_key=False, passage=None):
    """設問群のHTMLを組み立てる。with_key=True で正解と解説を含める（採点ツール用）。"""
    out = []
    for i, q in enumerate(part, 1):
        if passage and q.get("passage"):
            out.append(passage)
        out.append('<fieldset class="q"><legend class="q-legend">'
                   '<span class="q-no mono">問 %d</span></legend>'
                   '<p class="q-text">%s</p><div class="opts">' % (i, qtext(q["q"])))
        for j, o in enumerate(q["opts"]):
            out.append('<label class="opt"><input type="radio" name="__NAME__%d" value="%d">'
                       '<span class="opt-mk mono">%s</span>'
                       '<span class="opt-t">%s</span></label>'
                       % (i, j, D.CHOICES[j], esc(o)))
        out.append("</div></fieldset>")
    return "\n".join(out)


# ================================================================ 受験用
CANDIDATE_TMPL = r"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>営業職 採用適性検査</title>
<style>
__CSS__
/* ---- 受験画面 ---- */
#bar{position:sticky;top:0;z-index:50;background:var(--surface);
  border-bottom:1px solid var(--rule);padding:9px 24px;
  display:flex;align-items:center;justify-content:space-between;gap:12px 20px;flex-wrap:wrap}
#bar .id{font-size:13.5px;font-weight:700;white-space:nowrap}
#bar .mid{display:flex;align-items:center;gap:10px;font-size:12px;color:var(--ink-3);min-width:0}
.dots{display:flex;gap:5px}
.dots i{width:7px;height:7px;border-radius:50%;background:var(--rule);display:block}
.dots i.on{background:var(--indigo)}
.dots i.done{background:var(--ink-3)}
#timer{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-variant-numeric:tabular-nums;
  font-size:21px;font-weight:500;letter-spacing:.02em;padding:2px 12px;
  border:1px solid var(--rule);background:var(--paper);min-width:96px;text-align:center}
#timer.low{color:var(--vermilion);border-color:var(--vermilion);background:var(--vermilion-soft)}
#timer.hidden{visibility:hidden}
main{padding:0 0 90px}
.screen{padding:44px 0 0}
h1{font-size:clamp(26px,5vw,38px);line-height:1.35;margin:0 0 20px}
h2{font-size:23px;margin:0 0 6px}
.lead{color:var(--ink-2);max-width:40em;margin:0 0 26px}
.sec-meta{display:flex;gap:20px;flex-wrap:wrap;margin:0 0 30px;font-size:12.5px;color:var(--ink-3);
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.sec-meta b{color:var(--ink-2);font-weight:500}
.field{display:grid;gap:5px;margin:0 0 16px;max-width:30em}
.field label{font-size:12.5px;color:var(--ink-2);letter-spacing:.04em}
.field label .req{color:var(--vermilion);margin-left:5px;font-size:11px}
.field input{font:inherit;font-size:15px;padding:10px 13px;border:1px solid var(--rule);
  background:var(--surface);color:var(--ink);width:100%}
.consent{display:grid;grid-template-columns:auto 1fr;gap:0 12px;align-items:start;
  margin:12px 0;padding:15px 17px;border:1px solid var(--rule);background:var(--surface);
  font-size:13.5px;line-height:1.8;color:var(--ink-2);cursor:pointer}
.consent input{margin-top:6px;width:17px;height:17px;accent-color:var(--indigo)}
.q{border:0;border-top:1px solid var(--rule);margin:0;padding:26px 0;min-width:0}
.q-legend{padding:0}
.q-no{font-size:12px;letter-spacing:.06em;color:var(--indigo)}
.q-text{margin:6px 0 0;font-size:14.5px;line-height:1.85}
.q-text em{font-style:normal;font-weight:700;
  background:linear-gradient(transparent 62%,var(--indigo-soft) 62%)}
.opts{display:grid;gap:4px;margin:15px 0 0}
.opt{display:grid;grid-template-columns:auto auto 1fr;gap:0 12px;align-items:baseline;
  padding:11px 15px;background:var(--surface);border:1px solid var(--rule-2);
  border-left:3px solid transparent;cursor:pointer;transition:border-color .12s,background .12s}
.opt:hover{border-color:var(--rule);border-left-color:var(--rule)}
.opt input{margin:0;align-self:center;width:16px;height:16px;accent-color:var(--indigo)}
.opt-mk{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;color:var(--ink-3)}
.opt-t{font-size:14px;line-height:1.75}
.opt:has(input:checked){border-color:var(--indigo);border-left-color:var(--indigo);
  background:var(--indigo-soft)}
.opt:has(input:checked) .opt-mk{color:var(--indigo);font-weight:700}
.passage{margin:0 0 4px;padding:22px 24px;background:var(--surface);border:1px solid var(--rule);
  border-left:3px solid var(--ink-3);
  font-family:"Hiragino Mincho ProN","Yu Mincho","Noto Serif JP",serif;font-size:15px;line-height:2.05}
.passage p{margin:0 0 1.1em}.passage p:last-child{margin:0}
.passage .plabel{font-family:inherit;font-size:11.5px;letter-spacing:.14em;color:var(--ink-3);
  margin:0 0 12px;font-weight:400}
.likert-legend{position:sticky;top:52px;z-index:20;display:flex;gap:0;margin:0 0 2px;
  background:var(--surface-2);border:1px solid var(--rule);font-size:11px;color:var(--ink-2)}
.likert-legend div{flex:1;padding:7px 4px;text-align:center;border-right:1px solid var(--rule-2)}
.likert-legend div:last-child{border-right:0}
.likert-legend b{display:block;font-size:14px;color:var(--indigo);
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.item{display:grid;grid-template-columns:38px 1fr;gap:0 8px;align-items:center;
  padding:10px 12px;background:var(--surface);border:1px solid var(--rule-2);margin-top:3px}
.item.miss{border-color:var(--vermilion)}
.it-no{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;color:var(--ink-3);
  text-align:right}
.it-t{font-size:14px;line-height:1.7}
.lk{grid-column:1/-1;display:flex;gap:3px;margin-top:8px}
.lk label{flex:1;display:flex;align-items:center;justify-content:center;gap:6px;
  padding:7px 2px;border:1px solid var(--rule-2);background:var(--paper);cursor:pointer;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:13px;color:var(--ink-2)}
.lk label:hover{border-color:var(--rule)}
.lk input{margin:0;width:15px;height:15px;accent-color:var(--indigo)}
.lk label:has(input:checked){border-color:var(--indigo);background:var(--indigo-soft);
  color:var(--indigo);font-weight:700}
@media (min-width:700px){
  .item{grid-template-columns:38px 1fr auto;gap:0 14px}
  .lk{grid-column:auto;margin-top:0;width:330px}
}
.navbar{position:sticky;bottom:0;margin-top:36px;padding:16px 0 20px;background:var(--paper);
  border-top:1px solid var(--rule);display:flex;align-items:center;
  justify-content:space-between;gap:16px;flex-wrap:wrap}
.navbar .status{font-size:12.5px;color:var(--ink-3);
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.navbar .status.miss{color:var(--vermilion)}
#outbox{width:100%;min-height:150px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  font-size:11.5px;line-height:1.6;padding:14px;border:1px solid var(--rule);
  background:var(--surface);color:var(--ink-2);white-space:pre;overflow:auto}
.actions{display:flex;gap:12px;flex-wrap:wrap;margin:22px 0}
.summary{display:flex;flex-wrap:wrap;gap:0;border:1px solid var(--rule);background:var(--surface);
  margin:24px 0}
.summary div{flex:1 1 120px;padding:13px 16px;border-right:1px solid var(--rule-2)}
.summary div:last-child{border-right:0}
.summary dt{font-size:11px;letter-spacing:.1em;color:var(--ink-3);margin:0 0 3px}
.summary dd{margin:0;font-size:17px;font-weight:500;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.summary dd.miss{color:var(--vermilion)}
</style>
</head>
<body>
<header id="bar">
  <div class="id">営業職 採用適性検査</div>
  <div class="mid">
    <span id="partlabel">受検前</span>
    <span class="dots" id="dots" aria-hidden="true"></span>
  </div>
  <div id="timer" class="hidden" role="timer" aria-live="off">--:--</div>
</header>
<main><div class="wrap" id="app"></div></main>

<script>
"use strict";
var DATA = __DATA_JSON__;
var CH = ["ア","イ","ウ","エ"];
var LS = "sales-aptitude-v1";
var S = null, timerId = null, deadline = null, dirty = false;

/* ---------- utils ---------- */
function el(id){ return document.getElementById(id); }
function esc(s){ return String(s).replace(/[&<>"]/g, function(c){
  return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]; }); }
function two(n){ return (n<10?"0":"")+n; }
function fmt(sec){ if(sec<0) sec=0; return two(Math.floor(sec/60))+":"+two(sec%60); }
function nowIso(){ return new Date().toISOString(); }
function jdate(d){ var x=new Date(d); return x.getFullYear()+"-"+two(x.getMonth()+1)+"-"+two(x.getDate())
  +" "+two(x.getHours())+":"+two(x.getMinutes()); }
function dur(ms){ var s=Math.round(ms/1000); return Math.floor(s/60)+"分"+two(s%60)+"秒"; }
function fnv1a(str){ var h=0x811c9dc5;
  for(var i=0;i<str.length;i++){ h^=str.charCodeAt(i); h=(h+((h<<1)+(h<<4)+(h<<7)+(h<<8)+(h<<24)))>>>0; }
  return ("0000000"+h.toString(16)).slice(-8); }
function b64(str){ var bytes=new TextEncoder().encode(str), bin="";
  for(var i=0;i<bytes.length;i++) bin+=String.fromCharCode(bytes[i]);
  return btoa(bin); }
function chunk(s,n){ var o=[]; for(var i=0;i<s.length;i+=n) o.push(s.slice(i,i+n)); return o.join("\n"); }

/* ---------- state ---------- */
function fresh(){
  return { meta:{name:"",email:"",code:"",start:null,end:null,reloads:0},
           screen:"intro", parts:[], ans:[[],[],[],[],[]] };
}
function save(){
  try{ localStorage.setItem(LS, JSON.stringify({s:S, deadline:deadline})); }catch(e){}
}
function load(){
  try{ var r=localStorage.getItem(LS); return r?JSON.parse(r):null; }catch(e){ return null; }
}
function clearSaved(){ try{ localStorage.removeItem(LS); }catch(e){} }

/* ---------- chrome ---------- */
function paintChrome(){
  var d=""; for(var i=0;i<5;i++){
    var cls = S.screen==="p"+i ? "on" : (S.parts.length>i ? "done" : "");
    d += '<i class="'+cls+'"></i>';
  }
  el("dots").innerHTML=d;
  var m = /^p(\d)$/.exec(S.screen);
  el("partlabel").textContent = m ? ("第"+(+m[1]+1)+"部　"+DATA.titles[+m[1]])
    : (S.screen==="done" ? "終了" : "受検前");
}

/* ---------- timer ---------- */
function stopTimer(){ if(timerId){ clearInterval(timerId); timerId=null; } deadline=null;
  el("timer").className="hidden"; el("timer").textContent="--:--"; }
function startTimer(limit, resumeDeadline){
  var t=el("timer");
  if(limit===null){ t.className="hidden"; t.textContent="--:--"; return; }
  deadline = resumeDeadline || (Date.now()+limit*1000);
  t.className="";
  tick();
  timerId = setInterval(tick, 250);
}
function tick(){
  if(deadline===null) return;
  var left = Math.ceil((deadline-Date.now())/1000);
  var t=el("timer");
  t.textContent = fmt(left);
  t.className = left<=60 ? "low" : "";
  if(left<=0){ clearInterval(timerId); timerId=null; deadline=null; finishPart(true); }
}

/* ---------- screens ---------- */
function go(screen){ S.screen=screen; save(); render(); window.scrollTo(0,0); }

function render(){
  paintChrome();
  if(S.screen==="intro") return renderIntro();
  if(S.screen==="done")  return renderDone();
  var m=/^p(\d)$/.exec(S.screen);
  if(m) return renderPart(+m[1]);
  renderIntro();
}

function renderIntro(){
  stopTimer();
  var app=el("app");
  app.innerHTML =
   '<div class="screen">'
  +'<p class="kicker mono">RECRUITMENT APTITUDE TEST — SALES</p>'
  +'<h1>営業職 採用適性検査</h1>'
  +'<p class="lead">全5部、所要時間はおよそ60分です。第1部から第4部までは部ごとに制限時間があり、'
  +'時間になると自動的に次の部へ進みます。<strong>一度進むと前の部には戻れません</strong>ので、'
  +'まとまった時間が取れるときに開始してください。</p>'
  +'<div class="tablewrap" style="margin:0 0 24px"><table><thead><tr>'
  +'<th>部</th><th>領域</th><th class="num">問題数</th><th class="num">制限時間</th></tr></thead><tbody>'
  +DATA.titles.map(function(t,i){
      var n = i<4 ? DATA.parts[i].length+"問" : DATA.items.length+"項目";
      var lim = DATA.limits[i]===null ? "なし（目安10分）" : (DATA.limits[i]/60)+"分";
      return '<tr><td class="mono">第'+(i+1)+'部</td><td>'+t+'</td>'
           + '<td class="num">'+n+'</td><td class="num">'+lim+'</td></tr>'; }).join("")
  +'</tbody></table></div>'

  +'<div class="note"><b>受検にあたってのお願い</b>'
  +'・静かで中断されない環境と、安定したネットワーク接続をご用意ください。<br>'
  +'・<strong>電卓、計算機能付き機器はご使用になれません。</strong>第2部はすべて筆算で解ける水準です。'
  +'計算用の紙と筆記用具をお手元にご用意ください。<br>'
  +'・第5部（性格・行動特性）に正解・不正解はありません。深く考えず、普段のご自身に'
  +'最も近いものをお選びください。<br>'
  +'・誤答による減点はありません。分からない場合も、いずれかを選んでお進みください。</div>'

  +'<div class="note warn"><b>公正な受検のために</b>'
  +'生成AI（ChatGPT、Claude等）、検索、書籍、他の方の助力を用いずに、'
  +'ご自身の力のみで回答してください。本検査は入社後の配属や育成計画の検討にも用いるため、'
  +'実際の力と異なる結果は、ご本人にとっても望ましくありません。</div>'

  +'<div class="note"><b>取得する情報の取り扱い</b>'
  +'ご記入いただく氏名・メールアドレスおよび回答内容は、<strong>採用選考の判断材料としてのみ</strong>'
  +'利用します。本検査の結果は選考の一資料であり、これ単独で合否を決定するものではありません。'
  +'取得した情報は選考終了後1年を目安に、復元できない方法で廃棄します。<br>'
  +'体調・障害等により時間延長や別室受検などの配慮が必要な場合は、受検前に採用ご担当者まで'
  +'お申し出ください。<strong>お申し出の有無が評価に影響することはありません。</strong></div>'

  +'<h2 style="margin:40px 0 4px">受検者情報</h2>'
  +'<p class="lead" style="margin-bottom:20px">回答ファイルに記録され、採用担当者が本人を特定するために使用します。</p>'
  +'<div class="field"><label for="f-name">氏名<span class="req">必須</span></label>'
  +'<input id="f-name" type="text" autocomplete="name" placeholder="山田 太郎"></div>'
  +'<div class="field"><label for="f-mail">メールアドレス<span class="req">必須</span></label>'
  +'<input id="f-mail" type="email" autocomplete="email" placeholder="taro.yamada@example.com"></div>'
  +'<div class="field"><label for="f-code">受験番号（案内メールに記載がある場合）</label>'
  +'<input id="f-code" type="text" placeholder="任意"></div>'

  +'<label class="consent"><input type="checkbox" id="c1"><span>'
  +'生成AI・検索・他者の助力を用いず、自分自身の力のみで回答することに同意します。</span></label>'
  +'<label class="consent"><input type="checkbox" id="c2"><span>'
  +'上記のとおり、氏名・メールアドレスおよび回答内容が採用選考の目的で利用されることに同意します。</span></label>'

  +'<div class="navbar"><span class="status" id="introstat">氏名・メールアドレスの入力と、2つの同意が必要です</span>'
  +'<button class="btn accent" id="start" disabled>第1部を開始する</button></div>'
  +'</div>';

  var f=["f-name","f-mail","c1","c2"].map(el);
  function check(){
    var ok = f[0].value.trim() && /\S+@\S+\.\S+/.test(f[1].value.trim()) && f[2].checked && f[3].checked;
    el("start").disabled = !ok;
    el("introstat").textContent = ok ? "準備ができました。開始すると第1部の計時が始まります。"
                                     : "氏名・メールアドレスの入力と、2つの同意が必要です";
    el("introstat").className = "status" + (ok?"":" miss");
  }
  f.forEach(function(x){ x.addEventListener("input",check); x.addEventListener("change",check); });
  el("start").addEventListener("click", function(){
    S.meta.name=f[0].value.trim(); S.meta.email=f[1].value.trim();
    S.meta.code=el("f-code").value.trim(); S.meta.start=nowIso();
    dirty=true; enterPart(0);
  });
  check();
}

function enterPart(i){
  S.screen="p"+i; save(); render(); window.scrollTo(0,0);
  startTimer(DATA.limits[i], null);
  save();
}

function renderPart(i){
  var app=el("app"), h="";
  var over = S.parts.length && S.parts[S.parts.length-1].over && S.parts.length===i;
  h += '<div class="screen">';
  if(over) h += '<div class="note warn"><b>前の部は制限時間により終了しました</b>'
             +  '未回答のまま終了した問題は無回答として記録されます。この部に集中してください。</div>';
  h += '<p class="kicker mono">PART '+(i+1)+'</p><h2>第'+(i+1)+'部　'+DATA.titles[i]+'</h2>';
  h += '<p class="lead">'+DATA.intros[i]+'</p>';
  var n = i<4 ? DATA.parts[i].length+"問" : DATA.items.length+"項目";
  var lim = DATA.limits[i]===null ? "制限なし（目安10分）" : (DATA.limits[i]/60)+"分";
  h += '<div class="sec-meta"><span>問題数 <b>'+n+'</b></span><span>制限時間 <b>'+lim+'</b></span></div>';

  if(i===4){
    h += '<div class="likert-legend">'
      +  '<div><b>5</b>よくあてはまる</div><div><b>4</b>ややあてはまる</div>'
      +  '<div><b>3</b>どちらともいえない</div><div><b>2</b>あまりあてはまらない</div>'
      +  '<div><b>1</b>まったくあてはまらない</div></div>';
    h += '<div id="items">'+DATA.items.map(function(t,k){
      var lk = [5,4,3,2,1].map(function(v){
        return '<label><input type="radio" name="i'+(k+1)+'" value="'+v+'"><span>'+v+'</span></label>';
      }).join("");
      return '<div class="item" data-i="'+(k+1)+'"><div class="it-no mono">'+(k+1)+'</div>'
           + '<div class="it-t">'+esc(t)+'</div><div class="lk">'+lk+'</div></div>';
    }).join("")+'</div>';
  } else {
    h += DATA.parts[i].map(function(q,k){
      var pre = "";
      if(q.passage && DATA.passage){
        pre = '<div class="passage"><p class="plabel">次の文章を読んで、問7から問9に答えてください。</p>'
            + DATA.passage.map(function(p){ return '<p>'+esc(p)+'</p>'; }).join("")+'</div>';
      }
      var opts = q.opts.map(function(o,j){
        return '<label class="opt"><input type="radio" name="q'+(k+1)+'" value="'+j+'">'
             + '<span class="opt-mk">'+CH[j]+'</span><span class="opt-t">'+esc(o)+'</span></label>';
      }).join("");
      return pre + '<fieldset class="q"><legend class="q-legend"><span class="q-no mono">問 '+(k+1)
           + '</span></legend><p class="q-text">'+q.q+'</p><div class="opts">'+opts+'</div></fieldset>';
    }).join("");
  }

  h += '<div class="navbar"><span class="status" id="stat"></span>'
    +  '<button class="btn accent" id="next">'
    +  (i<4 ? "第"+(i+2)+"部へ進む" : "回答を確定して終了する")+'</button></div></div>';
  app.innerHTML=h;
  var scope=app.firstElementChild;   // 部ごとに作り直される要素。古いリスナーは一緒に破棄される

  // 既存回答の復元
  var saved=S.ans[i]||[];
  var total = i===4 ? DATA.items.length : DATA.parts[i].length;
  for(var k=0;k<total;k++){
    var v=saved[k];
    if(v===undefined || v===null || v<0) continue;
    var nm = (i===4?"i":"q")+(k+1);
    var input=document.querySelector('input[name="'+nm+'"][value="'+v+'"]');
    if(input) input.checked=true;
  }

  function collect(){
    if(S.screen!=="p"+i) return S.ans[i]||[];
    var a=[];
    for(var k=0;k<total;k++){
      var nm=(i===4?"i":"q")+(k+1);
      var c=document.querySelector('input[name="'+nm+'"]:checked');
      a.push(c ? +c.value : (i===4?0:-1));
    }
    S.ans[i]=a; return a;
  }
  function missCount(){ var a=collect();
    return a.filter(function(v){ return i===4 ? v===0 : v<0; }).length; }
  function updateStat(){
    var m=missCount();
    var s=el("stat"); if(!s) return;
    s.textContent = m===0 ? "全"+total+"件に回答済みです" : ("未回答 "+m+" 件 / 全"+total+"件");
    s.className = "status"+(m?" miss":"");
    save();
  }
  scope.addEventListener("change", function(e){
    if(S.screen!=="p"+i) return;                 // 別の部に移った後は何もしない
    if(e.target.type==="radio"){ dirty=true; updateStat(); }
  });
  updateStat();

  el("next").addEventListener("click", function(){
    var m=missCount();
    if(m>0){
      var msg = "未回答が"+m+"件あります。\n"
        + (i<4 ? "このまま進むと、この部には戻れません。" : "このまま終了しますか。")
        + "\n\nよろしいですか？";
      if(!confirm(msg)) return;
    }
    finishPart(false);
  });
}

function finishPart(auto){
  var m=/^p(\d)$/.exec(S.screen); if(!m) return;
  var i=+m[1];
  // 現在の入力を確実に取り込む
  var total = i===4 ? DATA.items.length : DATA.parts[i].length;
  var a=[];
  for(var k=0;k<total;k++){
    var nm=(i===4?"i":"q")+(k+1);
    var c=document.querySelector('input[name="'+nm+'"]:checked');
    a.push(c ? +c.value : (i===4?0:-1));
  }
  S.ans[i]=a;
  var limit = DATA.limits[i];
  var used = limit===null ? null : (deadline===null ? limit : limit - Math.max(0,Math.ceil((deadline-Date.now())/1000)));
  S.parts[i] = { p:i+1, sec: used, over: !!auto };
  stopTimer();
  if(i<4){ enterPart(i+1); }
  else { S.meta.end=nowIso(); go("done"); }
}

/* ---------- 回答ファイル ---------- */
function buildPayload(){
  return { v:1, name:S.meta.name, email:S.meta.email, code:S.meta.code,
           start:S.meta.start, end:S.meta.end, reloads:S.meta.reloads,
           parts:S.parts, a1:S.ans[0], a2:S.ans[1], a3:S.ans[2], a4:S.ans[3], a5:S.ans[4] };
}
function buildFile(){
  var p=buildPayload();
  var js=JSON.stringify(p);
  var sum=fnv1a(js);
  var enc=chunk(b64(js),76);
  var el2=[];
  el2.push("==================================================================");
  el2.push("  営業職 採用適性検査　回答ファイル");
  el2.push("==================================================================");
  el2.push("");
  el2.push("氏名　　　　　： "+p.name);
  el2.push("メールアドレス： "+p.email);
  if(p.code) el2.push("受験番号　　　： "+p.code);
  var ds=jdate(p.start), de=jdate(p.end);
  el2.push("受検日時　　　： "+ds+" 〜 "+(ds.slice(0,10)===de.slice(0,10)?de.slice(11):de));
  el2.push("所要時間　　　： "+dur(new Date(p.end)-new Date(p.start)));
  el2.push("");
  el2.push("回答状況：");
  ["第1部 言語能力","第2部 数的処理","第3部 論理推理","第4部 状況判断"].forEach(function(t,i){
    var a=p["a"+(i+1)], miss=a.filter(function(v){return v<0;}).length;
    el2.push("  "+t+"　"+(a.length-miss)+" / "+a.length+" 問に回答");
  });
  var m5=p.a5.filter(function(v){return v===0;}).length;
  el2.push("  第5部 性格・行動特性　"+(p.a5.length-m5)+" / "+p.a5.length+" 項目に回答");
  el2.push("");
  el2.push("このファイルは編集せず、そのまま採用ご担当者へご返送ください。");
  el2.push("");
  el2.push("------------------------------------------------------------------");
  el2.push(" 以下は採点システムが読み取るためのデータです。編集しないでください。");
  el2.push("------------------------------------------------------------------");
  el2.push("CHECKSUM: "+sum);
  el2.push("-----BEGIN ANSWER DATA-----");
  el2.push(enc);
  el2.push("-----END ANSWER DATA-----");
  el2.push("");
  return el2.join("\n");
}
function fileName(){
  var d=new Date(), safe=(S.meta.name||"回答").replace(/[\\\/:*?"<>|\s]/g,"_");
  return "適性検査回答_"+safe+"_"+d.getFullYear()+two(d.getMonth()+1)+two(d.getDate())+".txt";
}

function renderDone(){
  stopTimer(); dirty=false; clearSaved();
  var text=buildFile(), p=buildPayload();
  var missAll=0;
  [p.a1,p.a2,p.a3,p.a4].forEach(function(a){ missAll+=a.filter(function(v){return v<0;}).length; });
  var miss5=p.a5.filter(function(v){return v===0;}).length;
  el("app").innerHTML =
   '<div class="screen"><p class="kicker mono">COMPLETE</p>'
  +'<h1>お疲れさまでした</h1>'
  +'<p class="lead">回答は以上です。<strong>下のボタンで回答ファイルを保存し、採用ご担当者へ'
  +'メールでご返送ください。</strong>返送が完了するまで、このページを閉じないでください。</p>'
  +'<div class="summary">'
  +'<div><dt>受検者</dt><dd style="font-size:15px;font-family:inherit">'+esc(p.name)+'</dd></div>'
  +'<div><dt>所要時間</dt><dd>'+dur(new Date(p.end)-new Date(p.start))+'</dd></div>'
  +'<div><dt>能力4部 未回答</dt><dd class="'+(missAll?"miss":"")+'">'+missAll+'</dd></div>'
  +'<div><dt>性格 未回答</dt><dd class="'+(miss5?"miss":"")+'">'+miss5+'</dd></div>'
  +'</div>'
  +'<div class="actions">'
  +'<button class="btn accent" id="dl">回答ファイルを保存する</button>'
  +'<button class="btn ghost" id="cp">本文をコピーする</button></div>'
  +'<div class="note"><b>保存できない場合</b>'
  +'「本文をコピーする」を押し、メール本文にそのまま貼り付けてご返送いただいても構いません。'
  +'下の枠内がその内容です。</div>'
  +'<textarea id="outbox" readonly spellcheck="false"></textarea>'
  +'<div class="note warn" style="margin-top:26px"><b>ご返送先</b>'
  +'保存したファイル（または上の本文）を、受検のご案内メールに返信する形でお送りください。'
  +'ご不明な点は採用ご担当者までお問い合わせください。</div></div>';
  el("outbox").value=text;
  el("dl").addEventListener("click", function(){ saveFile(text); });
  el("cp").addEventListener("click", function(){
    var b=el("cp");
    function done(ok){ b.textContent = ok?"コピーしました":"コピーできませんでした";
      setTimeout(function(){ b.textContent="本文をコピーする"; },2200); }
    if(navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(text).then(function(){done(true);},function(){ legacy(); });
    } else legacy();
    function legacy(){ var t=el("outbox"); t.focus(); t.select();
      var ok=false; try{ ok=document.execCommand("copy"); }catch(e){} done(ok); }
  });
}
function saveFile(text){
  var name=fileName();
  try{
    var blob=new Blob([text],{type:"text/plain;charset=utf-8"});
    var url=URL.createObjectURL(blob);
    var a=document.createElement("a");
    a.href=url; a.download=name; a.style.display="none";
    document.body.appendChild(a); a.click();
    setTimeout(function(){ document.body.removeChild(a); URL.revokeObjectURL(url); },1500);
  }catch(e){
    alert("お使いの環境ではファイルを保存できませんでした。\n「本文をコピーする」をご利用ください。");
  }
}

/* ---------- boot ---------- */
window.addEventListener("beforeunload", function(e){
  if(dirty && S && S.screen!=="done" && S.screen!=="intro"){ e.preventDefault(); e.returnValue=""; }
});

(function boot(){
  var saved=load();
  if(saved && saved.s && saved.s.screen && saved.s.screen!=="intro" && saved.s.screen!=="done"){
    S=saved.s;
    S.meta.reloads=(S.meta.reloads||0)+1;
    save();
    paintChrome();
    var m=/^p(\d)$/.exec(S.screen), i=m?+m[1]:0;
    var left = saved.deadline ? Math.ceil((saved.deadline-Date.now())/1000) : null;
    var msg = "前回の受検が途中で中断されています。\n\n"
      + "「OK」で第"+(i+1)+"部から再開します"
      + (DATA.limits[i]!==null && left!==null
          ? "（残り時間 "+(left>0?fmt(left):"0:00")+"）。\n" : "。\n")
      + "「キャンセル」を選ぶと、これまでの回答を破棄して最初からやり直します。";
    if(confirm(msg)){
      dirty=true; render();
      if(DATA.limits[i]!==null){
        if(saved.deadline && saved.deadline>Date.now()) startTimer(DATA.limits[i], saved.deadline);
        else { finishPart(true); }
      }
      return;
    }
    clearSaved();
  }
  S=fresh(); render();
})();
</script>
</body>
</html>
"""


def build_candidate():
    parts = []
    for p in (D.PART1, D.PART2, D.PART3, D.PART4):
        parts.append([{"q": q["q"], "opts": q["opts"], "passage": bool(q.get("passage"))}
                      for q in p])
    intros = [
        "提案書やメールの品質、顧客の要望を正確に読み取る力を測ります。",
        "営業実務で扱う数値処理の正確さと速さを測ります。<strong>電卓は使用できません。</strong>"
        "計算用の紙をお使いください。",
        "条件を整理し、確実に言えることと言えないことを見分ける力を測ります。",
        "営業の現場で実際に起こりうる場面です。<strong>あなたが取る行動として最も適切だと思うもの</strong>"
        "を1つ選んでください。明確な正解が定まらない設問もありますが、必ず1つお選びください。",
        "正解・不正解はありません。深く考えず、普段のあなたに最も近いものを直感でお選びください。"
        "この部に制限時間はありません。",
    ]
    data = {
        "titles": D.PART_TITLES,
        "limits": D.LIMITS,
        "intros": intros,
        "parts": parts,
        "passage": D.PASSAGE,
        "items": D.ITEMS5,
    }
    html = (CANDIDATE_TMPL
            .replace("__CSS__", CSS)
            .replace("__DATA_JSON__", json.dumps(data, ensure_ascii=False)))
    path = os.path.join(OUT, "営業職適性検査_受験用.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path, html


# ================================================================ 採点ツール
GRADER_BODY = r"""<title>適性検査 採点ツール</title>
<style>
__CSS__
.badge{display:inline-block;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:10.5px;
  letter-spacing:.14em;padding:2px 9px;border:1px solid var(--vermilion);color:var(--vermilion);
  background:var(--vermilion-soft);vertical-align:middle;margin-left:12px}
header.top{border-bottom:1px solid var(--rule);background:var(--surface);padding:16px 0}
header.top h1{font-size:20px;margin:0;display:flex;align-items:center;flex-wrap:wrap;gap:4px}
.drop{border:2px dashed var(--rule);background:var(--surface);padding:34px 24px;text-align:center;
  margin:28px 0;transition:border-color .15s,background .15s}
.drop.over{border-color:var(--indigo);background:var(--indigo-soft)}
.drop p{margin:0 0 14px;color:var(--ink-2);font-size:14px}
.drop .sub{font-size:12.5px;color:var(--ink-3);margin:14px 0 0}
#paste{width:100%;min-height:110px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  font-size:11.5px;padding:12px;border:1px solid var(--rule);background:var(--surface);color:var(--ink)}
.sec{padding:34px 0 0}
.sec h2{font-size:19px;margin:0 0 16px}
tbody tr.row{cursor:pointer}
tbody tr.row:hover{background:var(--indigo-soft)}
tbody tr.row.sel{background:var(--indigo-soft);box-shadow:inset 3px 0 0 var(--indigo)}
.g{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-weight:700}
.g.S,.g.A{color:var(--green)} .g.B{color:var(--ink)} .g.C,.g.D{color:var(--vermilion)}
.flagchip{display:inline-block;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:10.5px;
  border:1px solid var(--vermilion);color:var(--vermilion);padding:0 6px;margin:1px 2px 1px 0}
.err{color:var(--vermilion);font-size:13px}
.detail{border:1px solid var(--rule);background:var(--surface);margin:24px 0 0}
.detail-head{padding:18px 22px;border-bottom:1px solid var(--rule);background:var(--surface-2);
  display:flex;justify-content:space-between;align-items:baseline;gap:14px;flex-wrap:wrap}
.detail-head h3{margin:0;font-size:18px}
.detail-head .meta{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;color:var(--ink-3)}
.dbody{padding:22px}
.dgrid{display:grid;gap:22px}
@media(min-width:760px){.dgrid{grid-template-columns:1fr 1fr}}
.block h4{margin:0 0 10px;font-size:12px;letter-spacing:.12em;color:var(--indigo);
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-weight:500}
.bars{display:grid;gap:7px}
.bar{display:grid;grid-template-columns:118px 1fr 42px;gap:10px;align-items:center;font-size:13px}
.bar .track{height:11px;background:var(--surface-2);border:1px solid var(--rule-2);position:relative}
.bar .fill{position:absolute;inset:0 auto 0 0;background:var(--indigo)}
.bar.lo .fill{background:var(--vermilion)}
.bar.l .fill{background:var(--ink-3)}
.bar .v{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px;text-align:right}
.sjt{display:grid;gap:2px}
.sjt .r{display:grid;grid-template-columns:48px 30px 1fr;gap:10px;align-items:baseline;
  padding:7px 10px;background:var(--paper);border:1px solid var(--rule-2);font-size:13px}
.sjt .r.z{border-color:var(--vermilion);background:var(--vermilion-soft)}
.sjt .p{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11.5px;color:var(--ink-3)}
.sjt .r.z .p{color:var(--vermilion);font-weight:700}
.wrongs{display:grid;gap:8px}
.wrong{padding:11px 14px;background:var(--paper);border:1px solid var(--rule-2);
  border-left:3px solid var(--vermilion);font-size:13px;line-height:1.75}
.wrong .h{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11.5px;color:var(--ink-3);
  margin-bottom:3px}
.wrong .h b{color:var(--vermilion)}
.flags{display:grid;gap:8px}
.flag{display:grid;grid-template-columns:auto 1fr;gap:0 12px;padding:11px 14px;
  background:var(--vermilion-soft);border:1px solid var(--vermilion);font-size:13px;line-height:1.7}
.flag .n{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11.5px;color:var(--vermilion)}
.log{display:grid;gap:4px;font-size:12.5px;color:var(--ink-2)}
.log .l{display:grid;grid-template-columns:130px 1fr;gap:10px}
.log .l b{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-weight:500;color:var(--ink-3)}
.log .l.bad span{color:var(--vermilion)}
</style>

<header class="top"><div class="wrap"><h1>適性検査 採点ツール<span class="badge">社外秘</span></h1></div></header>
<div class="wrap">

<div class="sec">
  <p class="lead" style="margin-bottom:0">候補者から返送された回答ファイル（.txt）を読み込むと、
  第1〜4部の採点、SJTの重み付け集計、性格6尺度とライスケールの算出、重点確認事項の判定までを自動で行います。
  複数名をまとめて読み込めます。<strong>ファイルはこのブラウザの中だけで処理され、どこにも送信されません。</strong></p>

  <div class="drop" id="drop">
    <p>回答ファイル（.txt）をここにドラッグ＆ドロップ</p>
    <button class="btn ghost" id="pick">ファイルを選ぶ</button>
    <input type="file" id="file" accept=".txt,text/plain" multiple hidden>
    <p class="sub">メール本文で受け取った場合は、下の枠に貼り付けて「読み込む」を押してください。</p>
  </div>
  <textarea id="paste" spellcheck="false" placeholder="メール本文をここに貼り付け（複数名を続けて貼っても構いません）"></textarea>
  <div style="display:flex;gap:12px;margin:12px 0 0;flex-wrap:wrap">
    <button class="btn ghost" id="loadpaste">貼り付けた内容を読み込む</button>
    <button class="btn ghost" id="clearall">読み込み結果をすべて消去</button>
  </div>
</div>

<div class="sec" id="resultsec" hidden>
  <h2>採点結果</h2>
  <div class="tablewrap"><table id="tbl">
    <thead><tr>
      <th>氏名</th><th class="num">言語</th><th class="num">数的</th><th class="num">論理</th>
      <th class="num">SJT</th><th class="num">合計</th><th>段階</th>
      <th class="num">A</th><th class="num">B</th><th class="num">C</th>
      <th class="num">D</th><th class="num">E</th><th class="num">F</th><th class="num">L</th>
      <th>確認事項</th>
    </tr></thead><tbody id="tbody"></tbody>
  </table></div>
  <p class="lead" style="font-size:13px;margin:12px 0 0">行をクリックすると詳細が表示されます。
  A〜Fは1〜5の段階、Lはライスケールの平均値です。</p>
  <div id="detail"></div>

  <h2 style="margin-top:40px">CSV書き出し</h2>
  <textarea id="csv" readonly spellcheck="false"
    style="width:100%;min-height:120px;font-family:ui-monospace,Menlo,monospace;font-size:11.5px;
    padding:12px;border:1px solid var(--rule);background:var(--surface);color:var(--ink-2)"></textarea>
  <div style="display:flex;gap:12px;margin:12px 0 40px;flex-wrap:wrap">
    <button class="btn ghost" id="copycsv">CSVをコピー</button>
    <button class="btn ghost" id="savecsv">CSVを保存</button>
  </div>
</div>

<div class="note warn" style="margin:0 0 48px"><b>取り扱い</b>
本ツールは解答キー・配点・性格検査の尺度キーを含みます。<strong>候補者に共有しないでください。</strong>
採点結果は選考の一資料であり、これ単独で合否を決定するものではありません。
性格特性に優劣はなく、心身の健康状態や障害の有無を推知する目的で用いてはいけません。</div>
</div>

<script>
"use strict";
var K = __KEY_JSON__;
var CH = ["ア","イ","ウ","エ"];
var results = [], selected = -1;

function el(id){ return document.getElementById(id); }
function esc(s){ return String(s).replace(/[&<>"]/g,function(c){
  return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];}); }
function two(n){ return (n<10?"0":"")+n; }
function fnv1a(str){ var h=0x811c9dc5;
  for(var i=0;i<str.length;i++){ h^=str.charCodeAt(i); h=(h+((h<<1)+(h<<4)+(h<<7)+(h<<8)+(h<<24)))>>>0; }
  return ("0000000"+h.toString(16)).slice(-8); }
function jdate(d){ if(!d) return "—"; var x=new Date(d);
  return x.getFullYear()+"-"+two(x.getMonth()+1)+"-"+two(x.getDate())+" "+two(x.getHours())+":"+two(x.getMinutes()); }
function mmss(s){ if(s===null||s===undefined) return "—"; return Math.floor(s/60)+"分"+two(s%60)+"秒"; }

/* ---------- 解析 ---------- */
function parseOne(text){
  var m=/-----BEGIN ANSWER DATA-----([\s\S]*?)-----END ANSWER DATA-----/.exec(text);
  if(!m) return {err:"回答データのブロックが見つかりません"};
  var raw=m[1].replace(/[^A-Za-z0-9+/=]/g,"");
  var json;
  try{
    var bin=atob(raw), bytes=new Uint8Array(bin.length);
    for(var i=0;i<bin.length;i++) bytes[i]=bin.charCodeAt(i);
    json=new TextDecoder("utf-8").decode(bytes);
  }catch(e){ return {err:"データを復号できません。ファイルが途中で切れている可能性があります"}; }
  var p; try{ p=JSON.parse(json); }catch(e){ return {err:"データの形式が不正です"}; }
  if(!p.a1||!p.a5) return {err:"回答が含まれていません"};
  var cm=/CHECKSUM:\s*([0-9a-f]{8})/i.exec(text);
  var ck = cm ? (fnv1a(json)===cm[1].toLowerCase()) : null;
  return {p:p, checksum:ck};
}
function parseAll(text){
  var out=[], re=/-----BEGIN ANSWER DATA-----[\s\S]*?-----END ANSWER DATA-----/g, m, last=0;
  while((m=re.exec(text))!==null){
    out.push(parseOne(text.slice(last, m.index+m[0].length)));
    last=m.index+m[0].length;
  }
  if(!out.length) out.push({err:"回答データのブロックが見つかりません"});
  return out;
}

/* ---------- 採点 ---------- */
function grade(t){ return t>=72?"S":t>=59?"A":t>=45?"B":t>=32?"C":"D"; }
function stage(mean){ return mean>=4.3?5:mean>=3.8?4:mean>=3.2?3:mean>=2.6?2:1; }

function score(p){
  var r={p:p};
  function pc(ans,key){ var c=0,w=[];
    for(var i=0;i<key.length;i++){ if(ans[i]===key[i]) c++; else w.push(i); }
    return {n:c, wrong:w, miss:ans.filter(function(v){return v<0;}).length}; }
  r.c1=pc(p.a1,K.k1); r.c2=pc(p.a2,K.k2); r.c3=pc(p.a3,K.k3);
  r.s1=r.c1.n*2; r.s2=r.c2.n*2; r.s3=r.c3.n*2;
  r.sjt=[]; r.s4=0;
  for(var i=0;i<K.pts4.length;i++){
    var v=p.a4[i], pt = (v>=0 && v<4) ? K.pts4[i][v] : 0;
    r.s4+=pt; r.sjt.push({i:i, v:v, pt:pt});
  }
  r.total=r.s1+r.s2+r.s3+r.s4;
  r.grade=grade(r.total);
  r.rate=[r.s1/20, r.s2/24, r.s3/16, r.s4/30];
  r.spread=Math.round((Math.max.apply(null,r.rate)-Math.min.apply(null,r.rate))*100);

  r.scales={};
  Object.keys(K.scales).forEach(function(k){
    var items=K.scales[k].items, sum=0, n=0, miss=0;
    items.forEach(function(no){
      var v=p.a5[no-1];
      if(!v){ miss++; return; }
      sum += K.reverse.indexOf(no)>=0 ? (6-v) : v; n++;
    });
    var mean = n ? sum/n : 0;
    r.scales[k]={mean:mean, raw:sum, n:n, miss:miss, stage:n?stage(mean):null};
  });
  r.L=r.scales.L.mean;
  r.Ljudge = r.L>=4.2 ? "要注意" : r.L>=3.5 ? "やや高" : "標準";

  var zeros=r.sjt.filter(function(x){return x.pt===0;});
  var integ=[2,4,5,9].filter(function(i){ return r.sjt[i].pt===0; });
  r.flags=[];
  if(zeros.length>=2) r.flags.push([1,"SJTで0点の選択肢が"+zeros.length+"問（第"
    +zeros.map(function(x){return x.i+1;}).join("・")+"問）。判断の理由を本人に説明してもらい、経験不足か判断傾向かを切り分ける。"]);
  if(integ.length) r.flags.push([2,"SJTの誠実性・コンプライアンス系（第"
    +integ.map(function(i){return i+1;}).join("・")+"問）が0点。過去に「短期の成果」と「正しさ」が対立した場面での判断を聞く。"]);
  if(r.scales.D.stage!==null && r.scales.D.stage<=2) r.flags.push([3,"性格D（誠実性）が段階"
    +r.scales.D.stage+"。上記2と併せて確認し、両方に懸念がある場合は慎重に判断する。"]);
  if(r.L>=4.2) r.flags.push([4,"L尺度平均 "+r.L.toFixed(2)+"。自己呈示が強い可能性。"
    +"他尺度は参考程度にとどめ、面接では「どう考えるか」ではなく「実際に何をしたか」を聞く。"]);
  if(r.total<=44) r.flags.push([5,"能力合計が段階"+r.grade
    +"。弱い領域が担当予定業務に直結するか、ツールや体制で補える範囲かを判断する。"]);
  if(r.spread>=40) r.flags.push([6,"各部の得点率の最大差が"+r.spread
    +"ポイント。特定領域の苦手が業務上のボトルネックになるかを確認する。"]);
  if(r.scales.A.stage===5 && r.scales.D.stage!==null && r.scales.D.stage<=2)
    r.flags.push([7,"達成志向が段階5、誠実性が段階"+r.scales.D.stage
      +"。成果を優先して手続きや顧客利益を軽視する傾向がないか、具体例で確認する。"]);

  r.log=[];
  var missAbility=r.c1.miss+r.c2.miss+r.c3.miss+p.a4.filter(function(v){return v<0;}).length;
  var miss5=p.a5.filter(function(v){return !v;}).length;
  (p.parts||[]).forEach(function(pp,i){
    if(!pp) return;
    r.log.push({k:"第"+(i+1)+"部 所要", v:mmss(pp.sec)+(pp.over?"（制限時間により終了）":""), bad:!!pp.over});
  });
  r.log.push({k:"能力4部 未回答", v:missAbility+"問", bad:missAbility>0});
  r.log.push({k:"性格 未回答", v:miss5+"項目", bad:miss5>0});
  r.log.push({k:"再読み込み", v:(p.reloads||0)+"回", bad:(p.reloads||0)>=2});
  r.missAbility=missAbility; r.miss5=miss5;
  return r;
}

/* ---------- 描画 ---------- */
function addResults(list){
  list.forEach(function(x){
    if(x.err){ results.push({err:x.err}); return; }
    var r=score(x.p); r.checksum=x.checksum; results.push(r);
  });
  paint();
}
function paint(){
  el("resultsec").hidden = results.length===0;
  var tb=el("tbody"); tb.innerHTML="";
  results.forEach(function(r,idx){
    var tr=document.createElement("tr");
    if(r.err){
      tr.innerHTML='<td colspan="15" class="err">読み込めませんでした：'+esc(r.err)+'</td>';
      tb.appendChild(tr); return;
    }
    tr.className="row"+(idx===selected?" sel":"");
    var sc=r.scales;
    function st(k){ return sc[k].stage===null?"—":sc[k].stage; }
    tr.innerHTML='<td>'+esc(r.p.name||"（無記名）")
      +(r.checksum===false?' <span class="flagchip">改変の疑い</span>':'')+'</td>'
      +'<td class="num">'+r.s1+'</td><td class="num">'+r.s2+'</td><td class="num">'+r.s3+'</td>'
      +'<td class="num">'+r.s4+'</td><td class="num"><b>'+r.total+'</b></td>'
      +'<td class="g '+r.grade+'">'+r.grade+'</td>'
      +'<td class="num">'+st("A")+'</td><td class="num">'+st("B")+'</td><td class="num">'+st("C")+'</td>'
      +'<td class="num">'+st("D")+'</td><td class="num">'+st("E")+'</td><td class="num">'+st("F")+'</td>'
      +'<td class="num">'+r.L.toFixed(1)+'</td>'
      +'<td>'+(r.flags.length?r.flags.map(function(f){
          return '<span class="flagchip">'+("0"+f[0]).slice(-2)+'</span>';}).join(""):"—")+'</td>';
    tr.addEventListener("click", function(){ selected=idx; paint(); });
    tb.appendChild(tr);
  });
  renderDetail();
  renderCsv();
}
function bar(label,st,mean,cls){
  var pct = mean ? Math.max(0,Math.min(100,(mean-1)/4*100)) : 0;
  return '<div class="bar '+(cls||"")+'"><span>'+label+'</span>'
    +'<span class="track"><span class="fill" style="width:'+pct.toFixed(1)+'%"></span></span>'
    +'<span class="v">'+(mean?mean.toFixed(2):"—")+'</span></div>';
}
function renderDetail(){
  var d=el("detail");
  if(selected<0 || !results[selected] || results[selected].err){ d.innerHTML=""; return; }
  var r=results[selected], p=r.p, sc=r.scales;
  var h='<div class="detail"><div class="detail-head">'
    +'<h3>'+esc(p.name||"（無記名）")+'</h3>'
    +'<span class="meta">'+esc(p.email||"")+(p.code?"　/　"+esc(p.code):"")
    +'　/　'+jdate(p.start)+'</span></div><div class="dbody">';

  h+='<div class="tablewrap" style="margin:0 0 22px"><table><thead><tr>'
    +'<th>領域</th><th class="num">得点</th><th class="num">満点</th><th class="num">得点率</th>'
    +'</tr></thead><tbody>'
    +[["第1部 言語能力",r.s1,20],["第2部 数的処理",r.s2,24],["第3部 論理推理",r.s3,16],
      ["第4部 状況判断",r.s4,30]].map(function(x){
      return '<tr><td>'+x[0]+'</td><td class="num">'+x[1]+'</td><td class="num">'+x[2]+'</td>'
        +'<td class="num">'+Math.round(x[1]/x[2]*100)+'%</td></tr>';}).join("")
    +'<tr><td><b>能力合計</b></td><td class="num"><b>'+r.total+'</b></td><td class="num">90</td>'
    +'<td class="num">'+Math.round(r.total/90*100)+'%　段階 <span class="g '+r.grade+'">'+r.grade+'</span></td></tr>'
    +'</tbody></table></div>';

  h+='<div class="dgrid">';

  h+='<div class="block"><h4>性格・行動特性</h4><div class="bars">'
    +["A","B","C","D","E","F"].map(function(k){
      return bar(k+"　"+K.scales[k].name, sc[k].stage, sc[k].mean, sc[k].stage<=2?"lo":"");
    }).join("")
    +bar("L　回答態度", null, sc.L.mean, "l")
    +'</div><p style="font-size:12.5px;color:var(--ink-2);margin:12px 0 0">'
    +'L尺度：'+sc.L.mean.toFixed(2)+'（'+r.Ljudge+'）'
    +(r.L>=4.2?'　<span style="color:var(--vermilion)">他尺度の数値は参考程度にとどめてください。</span>':'')
    +'</p></div>';

  h+='<div class="block"><h4>受検ログ</h4><div class="log">'
    +r.log.map(function(l){ return '<div class="l'+(l.bad?" bad":"")+'"><b>'+esc(l.k)+'</b><span>'
      +esc(l.v)+'</span></div>';}).join("")
    +'<div class="l'+(r.checksum===false?" bad":"")+'"><b>データ整合性</b><span>'
    +(r.checksum===true?"検証OK":r.checksum===false?"不一致（改変または破損の疑い）":"検証情報なし")
    +'</span></div></div></div>';

  h+='</div>';

  h+='<div class="block" style="margin-top:26px"><h4>状況判断テスト（SJT）の内訳</h4><div class="sjt">'
    +r.sjt.map(function(x){
      var opt = x.v>=0 ? CH[x.v] : "無回答";
      var txt = x.v>=0 ? K.q4[x.i].opts[x.v] : "―";
      return '<div class="r'+(x.pt===0?" z":"")+'"><span class="p">第'+(x.i+1)+'問</span>'
        +'<span class="p">'+x.pt+'点</span><span>'+esc(opt)+'　'+esc(txt)+'</span></div>';
    }).join("")+'</div>'
    +'<p style="font-size:12.5px;color:var(--ink-2);margin:10px 0 0">'
    +'測定観点は 0点／1点の選択に注目してください：'
    +r.sjt.filter(function(x){return x.pt<=1;}).map(function(x){
        return '第'+(x.i+1)+'問（'+esc(K.q4[x.i].obs)+'）';}).join("、")
    +(r.sjt.every(function(x){return x.pt>=2;})?"該当なし":"")+'</p></div>';

  var wrongs=[];
  [["第1部",r.c1,K.q1,"k1"],["第2部",r.c2,K.q2,"k2"],["第3部",r.c3,K.q3,"k3"]].forEach(function(x){
    x[1].wrong.forEach(function(i){
      var key=K[x[3]][i], given=r.p["a"+(x[3][1])][i];
      wrongs.push('<div class="wrong"><div class="h">'+x[0]+' 問'+(i+1)
        +'　選択 <b>'+(given>=0?CH[given]:"無回答")+'</b>　正解 '+CH[key]+'</div>'
        +esc(x[2][i].q.replace(/<[^>]+>/g,""))+'<br><span style="color:var(--ink-3)">'
        +x[2][i].exp.replace(/<[^>]+>/g,"")+'</span></div>');
    });
  });
  h+='<div class="block" style="margin-top:26px"><h4>誤答（第1〜3部）'
    +(wrongs.length?'　'+wrongs.length+'問':'　なし')+'</h4>'
    +(wrongs.length?'<div class="wrongs">'+wrongs.join("")+'</div>'
      :'<p style="font-size:13px;color:var(--ink-2);margin:0">全問正解です。</p>')+'</div>';

  h+='<div class="block" style="margin-top:26px"><h4>重点確認事項</h4>'
    +(r.flags.length?'<div class="flags">'+r.flags.map(function(f){
       return '<div class="flag"><span class="n">'+("0"+f[0]).slice(-2)+'</span><span>'
         +esc(f[1])+'</span></div>';}).join("")+'</div>'
     :'<p style="font-size:13px;color:var(--ink-2);margin:0">該当なし。'
      +'ただし検査結果は仮説であり、面接で過去の行動事実により検証してください。</p>')
    +'</div>';

  h+='</div></div>';
  d.innerHTML=h;
}
function renderCsv(){
  var head=["氏名","メールアドレス","受験番号","受検日時","所要(分)","再読込",
            "言語","数的","論理","SJT","合計","段階",
            "A","B","C","D","E","F","L平均","L判定","未回答(能力)","未回答(性格)","確認事項"];
  var rows=[head];
  results.forEach(function(r){
    if(r.err) return;
    var p=r.p, sc=r.scales;
    var mins = (p.start&&p.end) ? Math.round((new Date(p.end)-new Date(p.start))/60000) : "";
    rows.push([p.name||"",p.email||"",p.code||"",jdate(p.start),mins,(p.reloads||0),
      r.s1,r.s2,r.s3,r.s4,r.total,r.grade,
      sc.A.stage,sc.B.stage,sc.C.stage,sc.D.stage,sc.E.stage,sc.F.stage,
      sc.L.mean.toFixed(2),r.Ljudge,r.missAbility,r.miss5,
      r.flags.map(function(f){return ("0"+f[0]).slice(-2);}).join(" ")]);
  });
  el("csv").value = rows.map(function(row){
    return row.map(function(c){ c=String(c);
      return /[",\n]/.test(c) ? '"'+c.replace(/"/g,'""')+'"' : c; }).join(",");
  }).join("\n");
}

/* ---------- 入出力 ---------- */
function readFiles(files){
  Array.prototype.forEach.call(files, function(f){
    var fr=new FileReader();
    fr.onload=function(){ addResults(parseAll(String(fr.result))); };
    fr.onerror=function(){ results.push({err:f.name+" を読み込めませんでした"}); paint(); };
    fr.readAsText(f,"utf-8");
  });
}
el("pick").addEventListener("click",function(){ el("file").click(); });
el("file").addEventListener("change",function(e){ readFiles(e.target.files); e.target.value=""; });
var dz=el("drop");
["dragenter","dragover"].forEach(function(ev){ dz.addEventListener(ev,function(e){
  e.preventDefault(); dz.classList.add("over"); }); });
["dragleave","drop"].forEach(function(ev){ dz.addEventListener(ev,function(e){
  e.preventDefault(); dz.classList.remove("over"); }); });
dz.addEventListener("drop",function(e){ if(e.dataTransfer&&e.dataTransfer.files) readFiles(e.dataTransfer.files); });
el("loadpaste").addEventListener("click",function(){
  var t=el("paste").value; if(!t.trim()) return;
  addResults(parseAll(t)); el("paste").value="";
});
el("clearall").addEventListener("click",function(){
  if(results.length && !confirm("読み込んだ結果をすべて消去します。よろしいですか？")) return;
  results=[]; selected=-1; paint();
});
el("copycsv").addEventListener("click",function(){
  var b=el("copycsv"), t=el("csv").value;
  function done(ok){ b.textContent=ok?"コピーしました":"コピーできませんでした";
    setTimeout(function(){ b.textContent="CSVをコピー"; },2200); }
  if(navigator.clipboard&&navigator.clipboard.writeText)
    navigator.clipboard.writeText(t).then(function(){done(true);},function(){done(false);});
  else { el("csv").select(); var ok=false; try{ok=document.execCommand("copy");}catch(e){} done(ok); }
});
el("savecsv").addEventListener("click",function(){
  var name="適性検査_採点結果_"+new Date().toISOString().slice(0,10)+".csv";
  var text="﻿"+el("csv").value;
  if(window.claude&&window.claude.use){
    window.claude.use("downloads").then(function(dl){
      if(!dl) return blobSave(name,text);
      dl.save({filename:name,data:text}).catch(function(){});
    }).catch(function(){ blobSave(name,text); });
  } else blobSave(name,text);
});
function blobSave(name,text){
  try{
    var blob=new Blob([text],{type:"text/csv;charset=utf-8"});
    var url=URL.createObjectURL(blob), a=document.createElement("a");
    a.href=url; a.download=name; a.style.display="none";
    document.body.appendChild(a); a.click();
    setTimeout(function(){ document.body.removeChild(a); URL.revokeObjectURL(url); },1500);
  }catch(e){ alert("保存できませんでした。「CSVをコピー」をご利用ください。"); }
}
</script>
"""


def build_grader():
    key = {
        "k1": [q["ans"] for q in D.PART1],
        "k2": [q["ans"] for q in D.PART2],
        "k3": [q["ans"] for q in D.PART3],
        "pts4": [q["pts"] for q in D.PART4],
        "q1": [{"q": q["q"], "exp": q["exp"]} for q in D.PART1],
        "q2": [{"q": q["q"], "exp": q["exp"]} for q in D.PART2],
        "q3": [{"q": q["q"], "exp": q["exp"]} for q in D.PART3],
        "q4": [{"opts": q["opts"], "obs": q["obs"]} for q in D.PART4],
        "scales": D.SCALES,
        "reverse": D.REVERSE,
        "items": D.ITEMS5,
    }
    body = (GRADER_BODY
            .replace("__CSS__", CSS)
            .replace("__KEY_JSON__", json.dumps(key, ensure_ascii=False)))
    standalone = ('<!doctype html>\n<html lang="ja">\n<head>\n<meta charset="utf-8">\n'
                  '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
                  '<meta name="robots" content="noindex,nofollow">\n</head>\n<body>\n'
                  + body + '\n</body>\n</html>\n')
    p1 = os.path.join(OUT, "営業職適性検査_採点ツール.html")
    with open(p1, "w", encoding="utf-8") as f:
        f.write(standalone)
    bd = os.path.join(ROOT, "build")
    os.makedirs(bd, exist_ok=True)
    p2 = os.path.join(bd, "grader-artifact.html")
    with open(p2, "w", encoding="utf-8") as f:
        f.write(body)
    return p1, p2


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    c, _ = build_candidate()
    g, ga = build_grader()
    for p in (c, g, ga):
        print("%9d bytes  %s" % (os.path.getsize(p), os.path.relpath(p, ROOT)))
