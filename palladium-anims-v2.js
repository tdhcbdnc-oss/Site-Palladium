// Palladium v2 — polished loops: pd2-neural, pd2-core, pd2-orbits, pd2-holo
const TAU2 = Math.PI * 2;
function rng2(seed){ let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }
function rgba2(hex, a){ const n = parseInt(hex.slice(1), 16); return `rgba(${n>>16&255},${n>>8&255},${n&255},${a})`; }
function sq(x){ return x * x; }
function wg2(x, c, s){ let d = Math.abs(x - c); d = Math.min(d, 1 - d); return Math.exp(-sq(d)/(2*sq(s))); }
function bg2(g, w, h){ const gr = g.createLinearGradient(0,0,0,h); gr.addColorStop(0,'#050a1e'); gr.addColorStop(0.5,'#0a1230'); gr.addColorStop(1,'#060b22'); g.fillStyle = gr; g.fillRect(0,0,w,h); }
function glow2(g, x, y, r, hex, a){ if(a<=0) return; const gr = g.createRadialGradient(x,y,0,x,y,r); gr.addColorStop(0, rgba2(hex,a)); gr.addColorStop(1, rgba2(hex,0)); g.fillStyle = gr; g.beginPath(); g.arc(x,y,r,0,TAU2); g.fill(); }
function nebula(g, w, h, tt, cols){ const bl = [[0.3,0.28,0],[0.75,0.6,0.33],[0.42,0.82,0.66]]; bl.forEach((b,i)=>{ const x=b[0]*w+14*Math.sin(TAU2*(tt+b[2])), y=b[1]*h+10*Math.cos(TAU2*(tt+b[2])); glow2(g,x,y,w*0.62,cols[i%cols.length],0.05); }); }
function stars2(g, w, h, seed, n, tt, ymax){ const rn = rng2(seed); for(let i=0;i<n;i++){ const x=rn()*w, y=rn()*h*(ymax||1), ph=rn(), big=rn()>0.8; const a=(big?0.5:0.28)*(0.45+0.55*Math.sin(TAU2*(tt*2+ph))); g.fillStyle=rgba2(big?'#cfe0ff':'#9db8ff',Math.max(a,0.05)); const s2=big?1.5:0.9; g.fillRect(x,y,s2,s2); } }
function vig(g, w, h){ const gr = g.createRadialGradient(w/2,h*0.46,h*0.22,w/2,h*0.5,h*0.72); gr.addColorStop(0,'rgba(2,5,16,0)'); gr.addColorStop(1,'rgba(2,5,16,0.55)'); g.fillStyle=gr; g.fillRect(0,0,w,h); }
function mark2(g, cx, y, size, C, tag){
  g.save(); g.textAlign='center';
  const dv=g.createLinearGradient(cx-size*4.2,0,cx+size*4.2,0); dv.addColorStop(0,rgba2(C.A,0)); dv.addColorStop(0.5,rgba2(C.H,0.75)); dv.addColorStop(1,rgba2(C.A,0));
  g.fillStyle=dv; g.fillRect(cx-size*4.2, y-size*1.42, size*8.4, 1);
  g.letterSpacing=(size*0.36)+'px'; g.font=`600 ${size}px "Space Grotesk", system-ui, sans-serif`;
  g.fillStyle='#f4f7ff'; g.fillText('PALLADIUM', cx+size*0.18, y);
  if(tag){ const ls=tag.length>16?size*0.14:size*0.30; g.letterSpacing=ls+'px'; g.font=`500 ${Math.max(9,Math.round(size*0.36))}px ui-monospace, Menlo, monospace`; g.fillStyle=rgba2('#9db8ff',0.78); g.fillText(tag, cx+ls*0.5, y+size*0.88); }
  g.restore(); g.letterSpacing='0px';
}
document.fonts && document.fonts.load('600 28px "Space Grotesk"').catch(()=>{});

class Pd2Base extends HTMLElement{
  connectedCallback(){
    if(this._on) return; this._on = true;
    this.style.display='block'; if(!this.style.width) this.style.width='100%'; if(!this.style.height) this.style.height='100%';
    const c = document.createElement('canvas'); c.style.cssText='display:block;width:100%;height:100%'; this.appendChild(c);
    this.cv=c; this.g=c.getContext('2d');
    this.ro = new ResizeObserver(()=>this._size()); this.ro.observe(this); this._size();
    this.init && this.init();
    this.t0 = performance.now();
    const loop = () => { this.raf = requestAnimationFrame(loop); if(!this.w) return; const sp = parseFloat(this.getAttribute('speed')) || 1; const t = (performance.now()-this.t0)/1000*sp; const P = this.period||8; this.draw(this.g, this.w, this.h, (t%P)/P, t); };
    loop();
  }
  get C(){ return this.getAttribute('accent')==='cyan' ? {A:'#22d8f5',B:'#3f7cff',H:'#c9f6ff'} : {A:'#2f6bff',B:'#8b5cf6',H:'#8fd8ff'}; }
  _size(){ const r=this.getBoundingClientRect(); const d=Math.min(devicePixelRatio||1,2); this.w=r.width; this.h=r.height; this.cv.width=Math.max(2,Math.round(r.width*d)); this.cv.height=Math.max(2,Math.round(r.height*d)); this.g.setTransform(d,0,0,d,0,0); }
  disconnectedCallback(){ this._on=false; cancelAnimationFrame(this.raf); this.ro && this.ro.disconnect(); this.innerHTML=''; }
}

/* 2a — Neural Core II */
customElements.define('pd2-neural', class extends Pd2Base{
  period = 12;
  init(){
    const N=170, pts=[]; for(let i=0;i<N;i++){ const y=1-2*(i+0.5)/N, r=Math.sqrt(1-y*y), th=i*2.399963; pts.push([r*Math.cos(th), y, r*Math.sin(th)]); }
    this.pts=pts; this.edges=[];
    for(let i=0;i<N;i++) for(let j=i+1;j<N;j++){ const a=pts[i],b=pts[j]; if(a[0]*b[0]+a[1]*b[1]+a[2]*b[2] > 0.918) this.edges.push([i,j]); }
    const rn=rng2(42); this.pulses=[]; for(let k=0;k<30;k++) this.pulses.push({e:Math.floor(rn()*this.edges.length), ph:rn()});
    this.dust=[]; for(let k=0;k<26;k++) this.dust.push({rr:1.13+rn()*0.34, ph:rn(), tw:rn()});
  }
  draw(g,w,h,tt){
    bg2(g,w,h); const C=this.C;
    nebula(g,w,h,tt,[C.B,C.A,'#1b3a8f']); stars2(g,w,h,7,30,tt,0.62);
    const cx=w/2, cy=h*0.42+4*Math.sin(TAU2*2*tt), R=w*0.34;
    const rot=TAU2*tt, tilt=0.42+0.03*Math.sin(TAU2*tt);
    const cr=Math.cos(rot), sr=Math.sin(rot), ct=Math.cos(tilt), st=Math.sin(tilt);
    glow2(g,cx,cy,R*1.7,C.A,0.11); glow2(g,cx,cy-R*0.3,R*1.05,C.B,0.09);
    const P=this.pts.map(p=>{ const x1=p[0]*cr+p[2]*sr, z1=-p[0]*sr+p[2]*cr; const y1=p[1]*ct-z1*st, z2=p[1]*st+z1*ct; const d=(z2+1)/2; return [cx+x1*R, cy+y1*R, d]; });
    const eCol=[]; for(let i=0;i<=6;i++) eCol.push(rgba2('#4a7dff',0.035+0.32*sq(i/6)));
    // dust behind
    const ery=R*0.30;
    const dustPos=this.dust.map(d2=>{ const a=TAU2*(tt+d2.ph); return {x:cx+Math.cos(a)*R*d2.rr, y:cy+Math.sin(a)*ery*d2.rr, front:Math.sin(a)>0, tw:d2.tw}; });
    for(const d2 of dustPos) if(!d2.front){ g.fillStyle=rgba2('#8fb4ff',0.14+0.14*Math.sin(TAU2*(tt*2+d2.tw))); g.fillRect(d2.x,d2.y,1.3,1.3); }
    // ring with ticks
    g.strokeStyle=rgba2(C.B,0.16); g.lineWidth=1; g.beginPath(); g.ellipse(cx,cy,R*1.18,ery*1.18,0,0,TAU2); g.stroke();
    for(let i=0;i<24;i++){ const a=TAU2*(i/24 - tt); const x1=Math.cos(a), y1=Math.sin(a); const behind=Math.sin(a)<=0; g.strokeStyle=rgba2(C.B,behind?0.10:0.26); g.beginPath(); g.moveTo(cx+x1*R*1.15, cy+y1*ery*1.15); g.lineTo(cx+x1*R*1.22, cy+y1*ery*1.22); g.stroke(); }
    g.strokeStyle=rgba2(C.H,0.5); g.lineWidth=1.3; g.beginPath(); g.ellipse(cx,cy,R*1.18,ery*1.18,0,TAU2*tt,TAU2*tt+0.7); g.stroke();
    g.lineWidth=0.7;
    for(const [i,j] of this.edges){ const a=P[i],b=P[j], dp=(a[2]+b[2])/2; g.strokeStyle=eCol[Math.round(dp*6)]; g.beginPath(); g.moveTo(a[0],a[1]); g.lineTo(b[0],b[1]); g.stroke(); }
    for(const p of P){ const d=p[2], s2=0.6+2.1*sq(d); g.fillStyle=rgba2(d>0.72?'#eef4ff':'#cdddff',0.12+0.75*sq(d)); g.beginPath(); g.arc(p[0],p[1],s2,0,TAU2); g.fill(); }
    g.globalCompositeOperation='lighter';
    for(const pu of this.pulses){ const [i,j]=this.edges[pu.e]; const a=P[i],b=P[j], d=(a[2]+b[2])/2; if(d<0.4) continue; for(let k=0;k<3;k++){ const f=((tt*3+pu.ph)%1)-k*0.022; if(f<0||f>1) continue; const x=a[0]+(b[0]-a[0])*f, y=a[1]+(b[1]-a[1])*f; const al=(1-k/3)*d; if(k===0){ glow2(g,x,y,8,C.H,0.55*al); g.fillStyle=rgba2('#ffffff',0.9*al); } else g.fillStyle=rgba2(C.H,0.5*al); g.beginPath(); g.arc(x,y,k===0?1.5:1.1,0,TAU2); g.fill(); } }
    g.globalCompositeOperation='source-over';
    for(const d2 of dustPos) if(d2.front){ g.fillStyle=rgba2('#bcd3ff',0.22+0.2*Math.sin(TAU2*(tt*2+d2.tw))); g.fillRect(d2.x,d2.y,1.5,1.5); }
    mark2(g,cx,h*0.862,Math.max(21,w*0.088),C,'AI INTEGRATOR');
    vig(g,w,h);
  }
});

/* 2b — Data Core II */
customElements.define('pd2-core', class extends Pd2Base{
  period = 9;
  init(){ const rn=rng2(5); this.cols=[]; for(let i=0;i<17;i++){ const chars=[]; for(let j=0;j<52;j++){ const r2=rn(); chars.push({c:r2<0.42?'0':r2<0.84?'1':'·', a:0.2+rn()*0.8}); } this.cols.push({x:(i+0.5)/17, k:1+Math.floor(rn()*2), ph:rn(), al:0.09+rn()*0.15, chars}); }
    this.sparks=[]; for(let i=0;i<9;i++) this.sparks.push({ph:rn(), ang:rn()*TAU2});
    this.ticks=[]; for(let i=0;i<12;i++) if(rn()>0.25) this.ticks.push(i); }
  hex(g,cx,cy,r,rot){ g.beginPath(); for(let i=0;i<6;i++){ const a=rot+i*TAU2/6-Math.PI/2; const x=cx+r*Math.cos(a), y=cy+r*Math.sin(a); i?g.lineTo(x,y):g.moveTo(x,y); } g.closePath(); }
  draw(g,w,h,tt){
    bg2(g,w,h); const C=this.C, cx=w/2, cy=h*0.46;
    const cellH=15, total=52*cellH;
    g.font='10px ui-monospace, Menlo, monospace'; g.textAlign='center';
    for(const col of this.cols){ const x=col.x*w; const off=((tt*col.k+col.ph)%1)*total;
      for(let j=0;j<52;j++){ let y=(j*cellH+off)%total - cellH; if(y<-cellH||y>h+cellH) continue; const ch=col.chars[j]; g.fillStyle=rgba2(j%9===0?'#22d8f5':'#5d8bff', col.al*ch.a); g.fillText(ch.c,x,y); }
      const hy2=((tt*col.k+col.ph*1.7)%1)*(h+140)-70; const st2=g.createLinearGradient(0,hy2-80,0,hy2); st2.addColorStop(0,rgba2('#22d8f5',0)); st2.addColorStop(1,rgba2('#22d8f5',0.12)); g.fillStyle=st2; g.fillRect(x-4,hy2-80,8,80);
    }
    const dim=g.createRadialGradient(cx,cy,18,cx,cy,210); dim.addColorStop(0,'rgba(7,12,34,0.95)'); dim.addColorStop(1,'rgba(7,12,34,0)'); g.fillStyle=dim; g.fillRect(0,0,w,h);
    // expanding hex rings
    const ringC=['#22d8f5','#3f7cff','#8b5cf6'];
    for(let k=0;k<3;k++){ const p=(tt*2+k/3)%1; const r=58+p*140, a=(1-p)*0.34*Math.min(p*6,1); this.hex(g,cx,cy,r,tt*TAU2/6); g.strokeStyle=rgba2(ringC[k],a); g.lineWidth=1.1; g.stroke(); }
    // orbit ticks
    for(const i of this.ticks){ const a=TAU2*(i/12+tt); const x=cx+Math.cos(a)*88, y=cy+Math.sin(a)*88; g.strokeStyle=rgba2('#7fa2ff',0.32); g.lineWidth=1.4; g.beginPath(); g.moveTo(x,y); g.lineTo(cx+Math.cos(a)*95, cy+Math.sin(a)*95); g.stroke(); }
    g.globalCompositeOperation='lighter';
    for(const s of this.sparks){ const p=(tt*2+s.ph)%1; for(let k=0;k<3;k++){ const p2=p-k*0.012; if(p2<0) continue; const r=(1-p2)*225+8, ang=s.ang+p2*2.4; const x=cx+Math.cos(ang)*r, y=cy+Math.sin(ang)*r*1.28; const al=Math.sin(Math.PI*p2)*(1-k/3); if(k===0) glow2(g,x,y,6,C.H,0.55*al); g.fillStyle=rgba2(k?C.A:'#ffffff',0.7*al); g.beginPath(); g.arc(x,y,k?1:1.6,0,TAU2); g.fill(); } }
    g.globalCompositeOperation='source-over';
    glow2(g,cx,cy,120,C.A,0.17+0.05*Math.sin(TAU2*2*tt));
    // outer thin hex + vertex dots
    this.hex(g,cx,cy,66,tt*TAU2/6); g.strokeStyle=rgba2(C.B,0.22); g.lineWidth=1; g.stroke();
    for(let i=0;i<6;i++){ const a=tt*TAU2/6+i*TAU2/6-Math.PI/2; g.fillStyle=rgba2(C.H,0.5); g.beginPath(); g.arc(cx+66*Math.cos(a),cy+66*Math.sin(a),1.6,0,TAU2); g.fill(); }
    // glass hex core
    const br=50+1.6*Math.sin(TAU2*2*tt);
    this.hex(g,cx,cy,br,0); const glass=g.createRadialGradient(cx-14,cy-18,4,cx,cy,br*1.3); glass.addColorStop(0,'rgba(38,56,120,0.95)'); glass.addColorStop(0.5,'rgba(14,22,54,0.93)'); glass.addColorStop(1,'rgba(9,14,38,0.95)'); g.fillStyle=glass; g.fill();
    const gr=g.createLinearGradient(cx-50,cy-50,cx+50,cy+50); gr.addColorStop(0,C.A); gr.addColorStop(1,C.B); g.strokeStyle=gr; g.lineWidth=2; g.stroke();
    g.save(); this.hex(g,cx,cy,br,0); g.clip(); const hl=g.createLinearGradient(cx-40,cy-br,cx+10,cy); hl.addColorStop(0,'rgba(255,255,255,0.10)'); hl.addColorStop(1,'rgba(255,255,255,0)'); g.fillStyle=hl; g.fillRect(cx-br,cy-br,br*2,br); g.restore();
    for(let i=0;i<6;i++){ const a=i*TAU2/6-Math.PI/2; g.strokeStyle=rgba2('#7fa2ff',0.08); g.lineWidth=1; g.beginPath(); g.moveTo(cx,cy); g.lineTo(cx+br*Math.cos(a),cy+br*Math.sin(a)); g.stroke(); }
    glow2(g,cx,cy,34,'#ffffff',0.10);
    g.font='700 42px "Space Grotesk", system-ui, sans-serif'; g.textAlign='center'; g.textBaseline='middle'; g.fillStyle='#ffffff'; g.fillText('P',cx,cy+3); g.textBaseline='alphabetic';
    mark2(g,cx,cy+124,16,C,'');
    g.textAlign='center'; g.letterSpacing='3px'; g.font='500 9.5px ui-monospace, Menlo, monospace'; g.fillStyle=rgba2('#9db8ff',0.6); g.fillText('12 PRODUCTS · ONE CORE', cx, cy+150); g.letterSpacing='0px';
    vig(g,w,h);
  }
});

/* 2c — Orchestration II */
customElements.define('pd2-orbits', class extends Pd2Base{
  period = 12;
  init(){ const rn=rng2(17); this.orbits=[{rx:80,n:3,rev:2},{rx:124,n:2,rev:-1},{rx:168,n:2,rev:1}].map(o=>({...o, sats:Array.from({length:o.n},()=>({off:rn(), bc:rn()}))})); }
  draw(g,w,h,tt){
    bg2(g,w,h); const C=this.C;
    nebula(g,w,h,tt,[C.B,'#1b3a8f',C.A]); stars2(g,w,h,3,34,tt,0.75);
    const cx=w/2, cy=h*0.40, tilt=-0.30, cT=Math.cos(tilt), sT=Math.sin(tilt);
    const proj=(o,ry,a)=>{ const lx=o.rx*Math.cos(a), ly=ry*Math.sin(a); return [cx+lx*cT-ly*sT, cy+lx*sT+ly*cT]; };
    let flash=0; const front=[], back=[];
    for(const o of this.orbits){ const ry=o.rx*0.36;
      g.save(); g.translate(cx,cy); g.rotate(tilt); g.strokeStyle=rgba2('#7fa2ff',0.15); g.lineWidth=1; g.beginPath(); g.ellipse(0,0,o.rx,ry,0,0,TAU2); g.stroke(); g.restore();
      o.sats.forEach((s,si)=>{ const a=TAU2*(o.rev*tt+s.off); const [X,Y]=proj(o,ry,a); const dep=(Math.sin(a)+1)/2, isFront=Math.sin(a)>0;
        const trail=[]; const n2=12; for(let q=0;q<n2;q++){ const a2=a-q*0.085*Math.sign(o.rev); trail.push([...proj(o,ry,a2), 1-q/n2]); }
        const bk=wg2(tt, s.bc, 0.014); flash+=bk;
        (isFront?front:back).push({X,Y,trail,bk,dep,isFront});
        if(si===0){ // echo arc behind lead satellite
          g.lineWidth=1.2; for(let q=1;q<10;q++){ const a1=a-0.22-q*0.11*Math.sign(o.rev), a0=a1-0.11*Math.sign(o.rev); const p1=proj(o,ry,a1), p0=proj(o,ry,a0); g.strokeStyle=rgba2(C.B,0.22*(1-q/10)); g.beginPath(); g.moveTo(p0[0],p0[1]); g.lineTo(p1[0],p1[1]); g.stroke(); }
        }
      });
    }
    const drawSat=(s)=>{ const al=(s.isFront?1:0.4)*(0.55+0.45*s.dep); const sz=1.9+1.5*s.dep;
      for(let q=1;q<s.trail.length;q++){ g.strokeStyle=rgba2(C.A,0.55*s.trail[q][2]*al); g.lineWidth=2.2*s.trail[q][2]+0.2; g.beginPath(); g.moveTo(s.trail[q-1][0],s.trail[q-1][1]); g.lineTo(s.trail[q][0],s.trail[q][1]); g.stroke(); }
      if(s.bk>0.03){ const gr=g.createLinearGradient(s.X,s.Y,cx,cy); gr.addColorStop(0,rgba2('#22d8f5',0.9*s.bk)); gr.addColorStop(1,rgba2('#22d8f5',0)); g.strokeStyle=gr; g.lineWidth=1.4; g.beginPath(); g.moveTo(s.X,s.Y); g.lineTo(cx,cy); g.stroke();
        const rp=1-s.bk; g.strokeStyle=rgba2('#22d8f5',0.5*s.bk); g.lineWidth=1; g.beginPath(); g.arc(cx,cy,46+rp*16,0,TAU2); g.stroke(); }
      glow2(g,s.X,s.Y,10*s.dep+4,C.H,0.5*al);
      g.strokeStyle=rgba2('#bcd3ff',0.35*al); g.lineWidth=0.8; g.beginPath(); g.arc(s.X,s.Y,sz+2.6,0,TAU2); g.stroke();
      g.fillStyle=rgba2('#ffffff',0.95*al); g.beginPath(); g.arc(s.X,s.Y,sz,0,TAU2); g.fill(); };
    back.forEach(drawSat);
    glow2(g,cx,cy,95,C.A,0.22+0.12*Math.min(flash,1)+0.04*Math.sin(TAU2*2*tt));
    const orb=g.createRadialGradient(cx-8,cy-10,2,cx,cy,32); orb.addColorStop(0,'#f2f7ff'); orb.addColorStop(0.4,C.A); orb.addColorStop(1,C.B); g.fillStyle=orb; g.beginPath(); g.arc(cx,cy,30+1.1*Math.sin(TAU2*2*tt),0,TAU2); g.fill();
    g.save(); g.beginPath(); g.arc(cx,cy,28,0,TAU2); g.clip();
    [[16,2,0.3],[21,-1,0.55],[25,1,0.8]].forEach((b,i)=>{ g.strokeStyle='rgba(255,255,255,0.16)'; g.lineWidth=3; g.beginPath(); g.arc(cx,cy,b[0],TAU2*(b[1]*tt+b[2]),TAU2*(b[1]*tt+b[2])+2.2); g.stroke(); });
    g.restore();
    g.strokeStyle=rgba2('#bcd3ff',0.30); g.lineWidth=1; g.beginPath(); g.arc(cx,cy,44,0,TAU2); g.stroke();
    for(let i=0;i<3;i++){ const a=TAU2*(tt+i/3); g.fillStyle=rgba2(C.H,0.7); g.beginPath(); g.arc(cx+44*Math.cos(a),cy+44*Math.sin(a),1.5,0,TAU2); g.fill(); }
    front.forEach(drawSat);
    const sh=wg2(tt,0.33,0.012); if(sh>0.03){ const p=Math.min(Math.max((tt-0.30)/0.06,0),1); const x=w*0.14+p*w*0.6, y=h*0.13+p*h*0.08; const gr=g.createLinearGradient(x-46,y-7,x,y); gr.addColorStop(0,rgba2('#cfe0ff',0)); gr.addColorStop(1,rgba2('#cfe0ff',0.8*sh)); g.strokeStyle=gr; g.lineWidth=1.2; g.beginPath(); g.moveTo(x-46,y-7); g.lineTo(x,y); g.stroke(); }
    mark2(g,cx,h*0.845,Math.max(21,w*0.088),C,'AI ORCHESTRATED COMPANY');
    vig(g,w,h);
  }
});

/* 2d — Holo Twin II */
customElements.define('pd2-holo', class extends Pd2Base{
  period = 10;
  init(){ this.bl=[[0,0,54],[1,0,84],[2,0,46],[0,1,110],[1,1,64],[2,1,80],[3,1,44],[1,2,52],[2,2,98],[3,2,60]].map((b,i)=>({gx:b[0],gy:b[1],hgt:b[2],o:i})); this.sorted=[...this.bl].sort((a,b)=>(a.gx+a.gy)-(b.gx+b.gy)); }
  block(g,b,tt,C,refl){
    const w=this.w, h=this.h, cx=w/2-16, by=h*0.60, s=37;
    const st=0.05+b.o*0.026, e=Math.min(Math.max((tt-st)/0.1,0),1);
    const c1=1.70158, c3=c1+1, ee=e>=1?1:1+c3*Math.pow(e-1,3)+c1*Math.pow(e-1,2);
    const ds=0.76+b.o*0.008, q=Math.min(Math.max((tt-ds)/0.09,0),1);
    const A=(e<=0?0:Math.min(e*2,1))*(1-q); if(A<=0.002) return;
    const bx0=cx+(b.gx-b.gy)*s, yb0=by-(b.gx+b.gy)*s*0.5;
    const rise=(1-Math.min(ee,1))*26, yb=yb0+rise;
    const hh=b.hgt*Math.min(ee,1.06), top=yb-hh, hw=s*0.84, hd=s*0.42;
    const flick=refl?1:0.85+0.15*Math.sin(TAU2*(tt*27)+b.o*2.1);
    const al=A*flick*(refl?0.16:1);
    const Pl=[bx0-hw,top+hd], Pr=[bx0+hw,top+hd], Pt=[bx0,top], Pb=[bx0,top+hd*2];
    g.strokeStyle=rgba2('#4fd7f5',0.8*al); g.lineWidth=1.1;
    g.beginPath(); g.moveTo(Pt[0],Pt[1]); g.lineTo(Pl[0],Pl[1]); g.lineTo(Pb[0],Pb[1]); g.lineTo(Pr[0],Pr[1]); g.closePath();
    g.fillStyle=rgba2(C.A,0.12*al); g.fill(); g.stroke();
    const vh=hh-hd;
    g.beginPath(); g.moveTo(Pl[0],Pl[1]); g.lineTo(Pl[0],Pl[1]+vh); g.moveTo(Pr[0],Pr[1]); g.lineTo(Pr[0],Pr[1]+vh); g.moveTo(Pb[0],Pb[1]); g.lineTo(Pb[0],Pb[1]+vh); g.stroke();
    g.strokeStyle=rgba2('#4fd7f5',0.45*al); g.beginPath(); g.moveTo(Pl[0],Pl[1]+vh); g.lineTo(Pb[0],Pb[1]+vh); g.lineTo(Pr[0],Pr[1]+vh); g.stroke();
    if(refl) return;
    // lit windows
    const rows=Math.floor((vh-8)/14); const rn=rng2(b.o*13+3);
    for(let ri=0;ri<rows;ri++) for(let ci=0;ci<2;ci++){
      const fq=2+Math.floor(rn()*3), ph=rn(); const on=Math.sin(TAU2*(tt*fq+ph))>0.1?1:0.15;
      const lx=bx0-hw+6+ci*9; const ly=top+hd+7+ri*14+(lx-(bx0-hw))*0.5;
      g.fillStyle=rgba2('#9beaff',0.4*on*A); g.fillRect(lx,ly,2.2,3);
      const rx2=bx0+hw-6-ci*9; const ry2=top+hd+7+ri*14+((bx0+hw)-rx2)*0.5;
      const on2=Math.sin(TAU2*(tt*fq+ph+0.4))>0.1?1:0.15;
      g.fillStyle=rgba2('#9beaff',0.32*on2*A); g.fillRect(rx2,ry2,2.2,3);
    }
    const pu=wg2(tt,0.5+b.o*0.023,0.013); if(pu>0.05) glow2(g,bx0,top+hd,36,'#22d8f5',0.35*pu*A);
    if(e>0&&e<1){ g.fillStyle=rgba2('#c9f6ff',0.95); g.fillRect(bx0-hw,yb-hh,hw*2,1.4); glow2(g,bx0,yb-hh,20,'#22d8f5',0.4); }
    if(q>0&&q<1){ const rn2=rng2(b.o*7+1); for(let k2=0;k2<7;k2++){ const ox=(rn2()-0.5)*hw*2, oy=rn2()*hh; g.fillStyle=rgba2('#9beaff',0.75*(1-q)); g.fillRect(bx0+ox, top+oy-q*46, 1.6,1.6); } }
    if(b.hgt>90&&tt>0.42&&tt<0.78){ const bp=0.5+0.5*Math.sin(TAU2*(tt*2+b.o*0.3)); const bm=g.createLinearGradient(0,top-120,0,top); bm.addColorStop(0,rgba2('#22d8f5',0)); bm.addColorStop(1,rgba2('#22d8f5',0.14*bp)); g.fillStyle=bm; g.fillRect(bx0-4,top-120,8,120);
      const p=(tt*3+b.o*0.3)%1; g.fillStyle=rgba2('#c9f6ff',0.8*Math.sin(Math.PI*p)); g.fillRect(bx0-0.8, top-8-p*70, 1.6,1.6); }
  }
  draw(g,w,h,tt){
    bg2(g,w,h); const C=this.C; this.w=w; this.h=h;
    const cx=w/2-16, by=h*0.60, s=37;
    const px=(gx,gy)=>[cx+(gx-gy)*s, by-(gx+gy)*s*0.5];
    glow2(g,cx+s*1.2,by-s*0.2,w*0.42,C.A,0.10);
    g.lineWidth=0.8;
    for(let i=-2;i<=5;i++){ const a=px(i,-2), b=px(i,5); g.strokeStyle=rgba2(C.A,0.10); g.beginPath(); g.moveTo(a[0],a[1]); g.lineTo(b[0],b[1]); g.stroke(); const c2=px(-2,i), d2=px(5,i); g.beginPath(); g.moveTo(c2[0],c2[1]); g.lineTo(d2[0],d2[1]); g.stroke(); }
    // reflections then bodies (back → front)
    for(const b of this.sorted){ const yb0=by-(b.gx+b.gy)*s*0.5; g.save(); g.translate(0,yb0); g.scale(1,-0.7); g.translate(0,-yb0); this.block(g,b,tt,C,true); g.restore(); }
    const fadeR=g.createLinearGradient(0,by,0,by+s*3); fadeR.addColorStop(0,'rgba(6,11,34,0)'); fadeR.addColorStop(1,'rgba(6,11,34,0.9)'); g.fillStyle=fadeR; g.fillRect(0,by,w,s*3.2);
    for(const b of this.sorted) this.block(g,b,tt,C,false);
    const scy=((tt*2)%1)*h; g.fillStyle=rgba2('#7fd7ff',0.045); g.fillRect(0,scy,w,24);
    // HUD
    g.textAlign='left'; g.letterSpacing='2.5px'; g.font='500 10px ui-monospace, Menlo, monospace';
    g.fillStyle=rgba2('#e4edff',0.8); g.fillText('PALLADIUM', 20, 32);
    g.fillStyle=rgba2('#9db8ff',0.5); g.fillText('DIGITAL TWIN · BUILD 12', 20, 48);
    if(Math.sin(TAU2*tt*4)>0){ g.fillStyle=rgba2('#22d8f5',0.85); g.fillRect(w-28,24,6,6); }
    g.textAlign='right'; g.fillStyle=rgba2('#9db8ff',0.45); g.fillText('SYNC', w-38, 32); g.textAlign='left';
    const prog=Math.min(Math.max((tt-0.05)/0.34,0),1)*(1-Math.min(Math.max((tt-0.76)/0.17,0),1));
    const bw2=w*0.42, bx2=w/2-bw2/2, by2=h*0.885;
    g.fillStyle=rgba2('#7fa2ff',0.16); g.fillRect(bx2,by2,bw2,2);
    const pf=g.createLinearGradient(bx2,0,bx2+bw2,0); pf.addColorStop(0,C.A); pf.addColorStop(1,'#22d8f5'); g.fillStyle=pf; g.fillRect(bx2,by2,bw2*prog,2);
    g.textAlign='center'; g.letterSpacing='3px'; g.font='500 9px ui-monospace, Menlo, monospace'; g.fillStyle=rgba2('#9db8ff',0.5); g.fillText('TWIN SYNC', w/2, by2+18); g.letterSpacing='0px';
    // corner brackets
    g.strokeStyle=rgba2('#9db8ff',0.25); g.lineWidth=1;
    const br2=14, m=14; [[m,m,1,1],[w-m,m,-1,1],[m,h-m,1,-1],[w-m,h-m,-1,-1]].forEach(([x,y,dx,dy])=>{ g.beginPath(); g.moveTo(x+dx*br2,y); g.lineTo(x,y); g.lineTo(x,y+dy*br2); g.stroke(); });
    vig(g,w,h);
  }
});
