// Palladium — Orchestration (final 2c), scale- and orientation-aware: <pd-orch>
(function(){
const T = Math.PI * 2;
function R2(seed){ let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }
function ca(hex, a){ const n = parseInt(hex.slice(1), 16); return `rgba(${n>>16&255},${n>>8&255},${n&255},${a})`; }
function sq(x){ return x * x; }
function wgs(x, c, s){ let d = Math.abs(x - c); d = Math.min(d, 1 - d); return Math.exp(-sq(d)/(2*sq(s))); }
function glow(g, x, y, r, hex, a){ if(a<=0||r<=0) return; const gr = g.createRadialGradient(x,y,0,x,y,r); gr.addColorStop(0, ca(hex,a)); gr.addColorStop(1, ca(hex,0)); g.fillStyle = gr; g.beginPath(); g.arc(x,y,r,0,T); g.fill(); }
document.fonts && document.fonts.load('600 28px "Space Grotesk"').catch(()=>{});
if(!customElements.get('pd-orch'))
customElements.define('pd-orch', class extends HTMLElement{
  connectedCallback(){
    if(this._on) return; this._on = true;
    this.style.display='block'; if(!this.style.width) this.style.width='100%'; if(!this.style.height) this.style.height='100%';
    const c = document.createElement('canvas'); c.style.cssText='display:block;width:100%;height:100%'; this.appendChild(c);
    this.cv=c; this.g=c.getContext('2d');
    this.ro = new ResizeObserver(()=>this._size()); this.ro.observe(this); this._size();
    const rn=R2(17); this.orbits=[{rx:80,n:3,rev:2},{rx:124,n:2,rev:-1},{rx:168,n:2,rev:1}].map(o=>({...o, sats:Array.from({length:o.n},()=>({off:rn(), bc:rn()}))}));
    this.t0 = performance.now();
    const loop = () => { this.raf = requestAnimationFrame(loop); if(!this.w) return; const sp = parseFloat(this.getAttribute('speed')) || 1; const t = (performance.now()-this.t0)/1000*sp; this.draw(this.g, this.w, this.h, (t%12)/12, t); };
    loop();
  }
  get C(){ return this.getAttribute('accent')==='cyan' ? {A:'#22d8f5',B:'#3f7cff',H:'#c9f6ff'} : {A:'#2f6bff',B:'#8b5cf6',H:'#8fd8ff'}; }
  _size(){ const r=this.getBoundingClientRect(); const d=Math.min(devicePixelRatio||1,2, 2800/Math.max(r.width,r.height,1)); this.w=r.width; this.h=r.height; this.cv.width=Math.max(2,Math.round(r.width*d)); this.cv.height=Math.max(2,Math.round(r.height*d)); this.g.setTransform(d,0,0,d,0,0); }
  disconnectedCallback(){ this._on=false; cancelAnimationFrame(this.raf); this.ro && this.ro.disconnect(); this.innerHTML=''; }
  draw(g,w,h,tt){
    const C=this.C, land=w>h, S=land?h/460:w/324;
    const gr = g.createLinearGradient(0,0,0,h); gr.addColorStop(0,'#050a1e'); gr.addColorStop(0.5,'#0a1230'); gr.addColorStop(1,'#060b22'); g.fillStyle=gr; g.fillRect(0,0,w,h);
    [[0.3,0.28,0,C.B],[0.75,0.6,0.33,'#1b3a8f'],[0.42,0.82,0.66,C.A]].forEach(b=>{ glow(g, b[0]*w+14*S*Math.sin(T*(tt+b[2])), b[1]*h+10*S*Math.cos(T*(tt+b[2])), Math.max(w,h)*0.5, b[3], 0.05); });
    const rn=R2(3), nS=Math.min(90, Math.round(34*(w*h)/186624));
    for(let i=0;i<nS;i++){ const x=rn()*w, y=rn()*h*0.78, ph=rn(), big=rn()>0.8; const a=(big?0.5:0.28)*(0.45+0.55*Math.sin(T*(tt*2+ph))); g.fillStyle=ca(big?'#cfe0ff':'#9db8ff',Math.max(a,0.05)); const s2=(big?1.5:0.9)*Math.max(1,S*0.75); g.fillRect(x,y,s2,s2); }
    const cx=w/2, cy=h*0.40, tilt=-0.30, cT=Math.cos(tilt), sT=Math.sin(tilt);
    const proj=(o,ry,a)=>{ const lx=o.rx*S*Math.cos(a), ly=ry*S*Math.sin(a); return [cx+lx*cT-ly*sT, cy+lx*sT+ly*cT]; };
    let flash=0; const front=[], back=[];
    for(const o of this.orbits){ const ry=o.rx*0.36;
      g.save(); g.translate(cx,cy); g.rotate(tilt); g.strokeStyle=ca('#7fa2ff',0.15); g.lineWidth=S; g.beginPath(); g.ellipse(0,0,o.rx*S,ry*S,0,0,T); g.stroke(); g.restore();
      o.sats.forEach((s,si)=>{ const a=T*(o.rev*tt+s.off); const [X,Y]=proj(o,ry,a); const dep=(Math.sin(a)+1)/2, isFront=Math.sin(a)>0;
        const trail=[]; const n2=12; for(let q=0;q<n2;q++){ const a2=a-q*0.085*Math.sign(o.rev); trail.push([...proj(o,ry,a2), 1-q/n2]); }
        const bk=wgs(tt, s.bc, 0.014); flash+=bk;
        (isFront?front:back).push({X,Y,trail,bk,dep,isFront});
        if(si===0){ g.lineWidth=1.2*S; for(let q=1;q<10;q++){ const a1=a-0.22-q*0.11*Math.sign(o.rev), a0=a1-0.11*Math.sign(o.rev); const p1=proj(o,ry,a1), p0=proj(o,ry,a0); g.strokeStyle=ca(C.B,0.22*(1-q/10)); g.beginPath(); g.moveTo(p0[0],p0[1]); g.lineTo(p1[0],p1[1]); g.stroke(); } }
      });
    }
    const drawSat=(s)=>{ const al=(s.isFront?1:0.4)*(0.55+0.45*s.dep); const sz=(1.9+1.5*s.dep)*S;
      for(let q=1;q<s.trail.length;q++){ g.strokeStyle=ca(C.A,0.55*s.trail[q][2]*al); g.lineWidth=(2.2*s.trail[q][2]+0.2)*S; g.beginPath(); g.moveTo(s.trail[q-1][0],s.trail[q-1][1]); g.lineTo(s.trail[q][0],s.trail[q][1]); g.stroke(); }
      if(s.bk>0.03){ const gb=g.createLinearGradient(s.X,s.Y,cx,cy); gb.addColorStop(0,ca('#22d8f5',0.9*s.bk)); gb.addColorStop(1,ca('#22d8f5',0)); g.strokeStyle=gb; g.lineWidth=1.4*S; g.beginPath(); g.moveTo(s.X,s.Y); g.lineTo(cx,cy); g.stroke();
        const rp=1-s.bk; g.strokeStyle=ca('#22d8f5',0.5*s.bk); g.lineWidth=S; g.beginPath(); g.arc(cx,cy,(46+rp*16)*S,0,T); g.stroke(); }
      glow(g,s.X,s.Y,(10*s.dep+4)*S,C.H,0.5*al);
      g.strokeStyle=ca('#bcd3ff',0.35*al); g.lineWidth=0.8*S; g.beginPath(); g.arc(s.X,s.Y,sz+2.6*S,0,T); g.stroke();
      g.fillStyle=ca('#ffffff',0.95*al); g.beginPath(); g.arc(s.X,s.Y,sz,0,T); g.fill(); };
    back.forEach(drawSat);
    glow(g,cx,cy,95*S,C.A,0.22+0.12*Math.min(flash,1)+0.04*Math.sin(T*2*tt));
    const orb=g.createRadialGradient(cx-8*S,cy-10*S,2*S,cx,cy,32*S); orb.addColorStop(0,'#f2f7ff'); orb.addColorStop(0.4,C.A); orb.addColorStop(1,C.B); g.fillStyle=orb; g.beginPath(); g.arc(cx,cy,(30+1.1*Math.sin(T*2*tt))*S,0,T); g.fill();
    g.save(); g.beginPath(); g.arc(cx,cy,28*S,0,T); g.clip();
    [[16,2,0.3],[21,-1,0.55],[25,1,0.8]].forEach(b=>{ g.strokeStyle='rgba(255,255,255,0.16)'; g.lineWidth=3*S; g.beginPath(); g.arc(cx,cy,b[0]*S,T*(b[1]*tt+b[2]),T*(b[1]*tt+b[2])+2.2); g.stroke(); });
    g.restore();
    g.strokeStyle=ca('#bcd3ff',0.30); g.lineWidth=S; g.beginPath(); g.arc(cx,cy,44*S,0,T); g.stroke();
    for(let i=0;i<3;i++){ const a=T*(tt+i/3); g.fillStyle=ca(C.H,0.7); g.beginPath(); g.arc(cx+44*S*Math.cos(a),cy+44*S*Math.sin(a),1.5*S,0,T); g.fill(); }
    front.forEach(drawSat);
    const sh=wgs(tt,0.33,0.012); if(sh>0.03){ const p=Math.min(Math.max((tt-0.30)/0.06,0),1); const x=w*0.14+p*w*0.6, y=h*0.13+p*h*0.08; const gb=g.createLinearGradient(x-46*S,y-7*S,x,y); gb.addColorStop(0,ca('#cfe0ff',0)); gb.addColorStop(1,ca('#cfe0ff',0.8*sh)); g.strokeStyle=gb; g.lineWidth=1.2*S; g.beginPath(); g.moveTo(x-46*S,y-7*S); g.lineTo(x,y); g.stroke(); }
    // wordmark
    if(!this.hasAttribute('nomark')){
    const size=27*S, my=land?h*0.86:h*0.845;
    g.save(); g.textAlign='center';
    const dv=g.createLinearGradient(cx-size*4.2,0,cx+size*4.2,0); dv.addColorStop(0,ca(C.A,0)); dv.addColorStop(0.5,ca(C.H,0.75)); dv.addColorStop(1,ca(C.A,0));
    g.fillStyle=dv; g.fillRect(cx-size*4.2, my-size*1.42, size*8.4, Math.max(1,S*0.8));
    g.letterSpacing=(size*0.36)+'px'; g.font=`600 ${size}px "Space Grotesk", system-ui, sans-serif`;
    g.fillStyle='#f4f7ff'; g.fillText('PALLADIUM', cx+size*0.18, my);
    const tag='AI ORCHESTRATED COMPANY', ls=size*0.14;
    g.letterSpacing=ls+'px'; g.font=`500 ${Math.max(9,Math.round(size*0.36))}px ui-monospace, Menlo, monospace`; g.fillStyle=ca('#9db8ff',0.78); g.fillText(tag, cx+ls*0.5, my+size*0.88);
    g.restore(); g.letterSpacing='0px';
    }
    const vg = g.createRadialGradient(w/2,h*0.46,h*0.22,w/2,h*0.5,h*0.72); vg.addColorStop(0,'rgba(2,5,16,0)'); vg.addColorStop(1,'rgba(2,5,16,0.55)'); g.fillStyle=vg; g.fillRect(0,0,w,h);
  }
});
})();
