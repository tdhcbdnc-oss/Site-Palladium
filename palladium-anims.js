// Palladium — 7 looping 9:16 animations as web components
const TAU = Math.PI * 2;
function rng(seed){ let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }
function rgba(hex, a){ const n = parseInt(hex.slice(1), 16); return `rgba(${n>>16&255},${n>>8&255},${n&255},${a})`; }
function wgauss(x, c, s){ let d = Math.abs(x - c); d = Math.min(d, 1 - d); return Math.exp(-d*d/(2*s*s)); }
function bgFill(g, w, h){ const gr = g.createLinearGradient(0,0,0,h); gr.addColorStop(0,'#060c22'); gr.addColorStop(0.55,'#0a1330'); gr.addColorStop(1,'#070d24'); g.fillStyle = gr; g.fillRect(0,0,w,h); }
function glowDot(g, x, y, r, hex, a){ const gr = g.createRadialGradient(x,y,0,x,y,r); gr.addColorStop(0, rgba(hex,a)); gr.addColorStop(1, rgba(hex,0)); g.fillStyle = gr; g.beginPath(); g.arc(x,y,r,0,TAU); g.fill(); }
function stars(g, w, h, seed, n, tt, ymax){ const rn = rng(seed); for(let i=0;i<n;i++){ const x=rn()*w, y=rn()*h*(ymax||1), ph=rn(), s2=0.6+rn()*1.1; const a=0.12+0.35*(0.5+0.5*Math.sin(TAU*(tt*2+ph))); g.fillStyle=rgba('#9db8ff',a); g.fillRect(x,y,s2,s2); } }
function wordmark(g, cx, y, size, alpha, C, tag){
  g.save(); g.textAlign='center'; g.textBaseline='alphabetic';
  g.letterSpacing = (size*0.34)+'px';
  g.font = `600 ${size}px "Space Grotesk", system-ui, sans-serif`;
  g.fillStyle = rgba('#ffffff', alpha);
  g.fillText('PALLADIUM', cx + size*0.17, y);
  if(tag){ g.letterSpacing=(size*0.28)+'px'; g.font=`500 ${Math.round(size*0.37)}px ui-monospace, Menlo, monospace`; g.fillStyle=rgba('#9db8ff',alpha*0.8); g.fillText(tag, cx + size*0.14, y + size*0.82); }
  g.restore();
}
document.fonts && document.fonts.load('600 28px "Space Grotesk"').catch(()=>{});

class PdBase extends HTMLElement{
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

/* 1a — Neural Core: rotating node-sphere brain */
customElements.define('pd-neural-core', class extends PdBase{
  period = 10;
  init(){
    const N=150, pts=[]; for(let i=0;i<N;i++){ const y=1-2*(i+0.5)/N, r=Math.sqrt(1-y*y), th=i*2.399963; pts.push([r*Math.cos(th), y, r*Math.sin(th)]); }
    this.pts=pts; this.edges=[];
    for(let i=0;i<N;i++) for(let j=i+1;j<N;j++){ const a=pts[i],b=pts[j]; if(a[0]*b[0]+a[1]*b[1]+a[2]*b[2] > 0.913) this.edges.push([i,j]); }
    const rn=rng(42); this.pulses=[]; for(let k=0;k<26;k++) this.pulses.push({e:Math.floor(rn()*this.edges.length), ph:rn()});
  }
  draw(g,w,h,tt){
    bgFill(g,w,h); stars(g,w,h,7,22,tt,0.55);
    const C=this.C, cx=w/2, cy=h*0.44, R=w*0.36, rot=TAU*tt, tilt=0.42;
    const cr=Math.cos(rot), sr=Math.sin(rot), ct=Math.cos(tilt), st=Math.sin(tilt);
    glowDot(g,cx,cy,R*1.5,C.A,0.10+0.03*Math.sin(TAU*2*tt));
    const P=this.pts.map(p=>{ const x1=p[0]*cr+p[2]*sr, z1=-p[0]*sr+p[2]*cr; const y1=p[1]*ct-z1*st, z2=p[1]*st+z1*ct; const d=(z2+1)/2; return [cx+x1*R, cy+y1*R, d]; });
    g.lineWidth=0.7;
    for(const [i,j] of this.edges){ const a=P[i],b=P[j], dp=(a[2]+b[2])/2; g.strokeStyle=rgba(C.A,0.05+0.30*dp*dp); g.beginPath(); g.moveTo(a[0],a[1]); g.lineTo(b[0],b[1]); g.stroke(); }
    for(const p of P){ const s2=0.8+1.8*p[2]; g.fillStyle=rgba('#dfe9ff',0.15+0.7*p[2]*p[2]); g.beginPath(); g.arc(p[0],p[1],s2,0,TAU); g.fill(); }
    g.globalCompositeOperation='lighter';
    for(const pu of this.pulses){ const [i,j]=this.edges[pu.e]; const a=P[i],b=P[j], f=(tt*3+pu.ph)%1; const x=a[0]+(b[0]-a[0])*f, y=a[1]+(b[1]-a[1])*f, d=(a[2]+b[2])/2; if(d<0.35) continue; glowDot(g,x,y,7,C.H,0.5*d); g.fillStyle=rgba('#ffffff',0.85*d); g.beginPath(); g.arc(x,y,1.4,0,TAU); g.fill(); }
    g.globalCompositeOperation='source-over';
    g.strokeStyle=rgba(C.B,0.15); g.lineWidth=1; g.beginPath(); g.arc(cx,cy,R*1.13,0,TAU); g.stroke();
    g.strokeStyle=rgba(C.B,0.55); g.lineWidth=1.4; g.beginPath(); g.arc(cx,cy,R*1.13,-TAU*tt,-TAU*tt+0.9); g.stroke();
    wordmark(g,cx,h*0.865,Math.max(20,w*0.082),0.95,C,'AI INTEGRATOR');
  }
});

/* 1b — Plexus mesh with scanline, pure abstraction */
customElements.define('pd-plexus', class extends PdBase{
  period = 8;
  init(){ const rn=rng(9), N=44; this.nodes=[]; for(let i=0;i<N;i++) this.nodes.push({bx:0.05+rn()*0.9, by:0.04+rn()*0.92, fx:1+Math.floor(rn()*2), fy:1+Math.floor(rn()*2), amp:20+rn()*18, p1:rn(), p2:rn(), fp:rn()}); }
  draw(g,w,h,tt){
    bgFill(g,w,h); const C=this.C;
    g.strokeStyle=rgba('#9db8ff',0.22); g.lineWidth=1;
    for(const [qx,qy] of [[0.14,0.1],[0.86,0.1],[0.14,0.9],[0.86,0.9]]){ const x=qx*w,y=qy*h; g.beginPath(); g.moveTo(x-4,y); g.lineTo(x+4,y); g.moveTo(x,y-4); g.lineTo(x,y+4); g.stroke(); }
    const pos=this.nodes.map(n=>[n.bx*w+n.amp*Math.sin(TAU*(n.fx*tt+n.p1)), n.by*h+n.amp*Math.cos(TAU*(n.fy*tt+n.p2))]);
    const scans=[0,0.5].map(o=>{ const p=(tt+o)%1; return {y:p*h, a:Math.sin(Math.PI*p)}; });
    g.lineWidth=0.8;
    for(let i=0;i<pos.length;i++) for(let j=i+1;j<pos.length;j++){ const dx=pos[i][0]-pos[j][0], dy=pos[i][1]-pos[j][1], d=Math.hypot(dx,dy); if(d<115){ g.strokeStyle=rgba(C.A,(1-d/115)*0.42); g.beginPath(); g.moveTo(pos[i][0],pos[i][1]); g.lineTo(pos[j][0],pos[j][1]); g.stroke(); } }
    for(const s of scans){ if(s.a<0.03) continue; const gr=g.createLinearGradient(0,s.y-55,0,s.y+55); gr.addColorStop(0,rgba(C.A,0)); gr.addColorStop(0.5,rgba('#22d8f5',0.09*s.a)); gr.addColorStop(1,rgba(C.A,0)); g.fillStyle=gr; g.fillRect(0,s.y-55,w,110); g.fillStyle=rgba('#22d8f5',0.55*s.a); g.fillRect(0,s.y,w,1.2); }
    this.nodes.forEach((n,i)=>{ const [x,y]=pos[i]; let boost=0; for(const s of scans) boost=Math.max(boost, s.a*Math.exp(-(((y-s.y)/70)**2))); const fl=wgauss(tt, n.fp, 0.018); const r=1.8+3*boost+2.5*fl; if(boost>0.35||fl>0.3) glowDot(g,x,y,r*4,'#22d8f5',0.35*(boost+fl)); g.fillStyle=rgba(boost>0.4?'#c9f6ff':'#dfe9ff',0.45+0.5*Math.max(boost,fl)); g.beginPath(); g.arc(x,y,r,0,TAU); g.fill(); });
  }
});

/* 1c — Digital Twin: org scheme mirrored as wireframe */
customElements.define('pd-twin-mirror', class extends PdBase{
  period = 8;
  init(){
    this.blocks=[{x:0.5,y:0.22,root:1},{x:0.28,y:0.5},{x:0.72,y:0.5},{x:0.16,y:0.78},{x:0.5,y:0.78},{x:0.84,y:0.78}];
    this.links=[[0,1],[0,2],[1,3],[1,4],[2,4],[2,5]];
  }
  path(i,j,w,hy){ const A=this.blocks[i], B=this.blocks[j]; const ax=A.x*w, ay=A.y*hy+17, bx=B.x*w, by=B.y*hy-17, my=(ay+by)/2; return [[ax,ay],[ax,my],[bx,my],[bx,by]]; }
  drawScheme(g,w,hy,tt,wire,C){
    const bw=66,bh=34;
    g.lineWidth=1.1; if(wire) g.setLineDash([3,4]);
    this.links.forEach((L,k)=>{ const pts=this.path(L[0],L[1],w,hy); g.strokeStyle=wire?rgba('#22d8f5',0.30):rgba(C.A,0.40); g.beginPath(); pts.forEach((p,i)=>i?g.lineTo(p[0],p[1]):g.moveTo(p[0],p[1])); g.stroke(); });
    g.setLineDash([]);
    // traveling pulses
    this.links.forEach((L,k)=>{ const pts=this.path(L[0],L[1],w,hy); const segs=[]; let tot=0; for(let i=0;i<3;i++){ const l=Math.hypot(pts[i+1][0]-pts[i][0],pts[i+1][1]-pts[i][1]); segs.push(l); tot+=l; } let f=((wire?tt-0.06:tt)*2+k/6)%1; if(f<0) f+=1; let dRem=f*tot, x=pts[0][0], y=pts[0][1]; for(let i=0;i<3;i++){ if(dRem<=segs[i]||i===2){ const r2=segs[i]?dRem/segs[i]:0; x=pts[i][0]+(pts[i+1][0]-pts[i][0])*Math.min(r2,1); y=pts[i][1]+(pts[i+1][1]-pts[i][1])*Math.min(r2,1); break;} dRem-=segs[i]; }
      glowDot(g,x,y,8,wire?'#22d8f5':C.H,wire?0.4:0.6); g.fillStyle=rgba('#ffffff',wire?0.5:0.9); g.beginPath(); g.arc(x,y,1.5,0,TAU); g.fill();
      const arr=f>0.9?Math.sin(Math.PI*(f-0.9)/0.1):0; if(arr>0){ const B=this.blocks[L[1]]; glowDot(g,B.x*w,B.y*hy,26,wire?'#22d8f5':C.H,0.3*arr); }
    });
    this.blocks.forEach((b)=>{ const x=b.x*w-bw/2, y=b.y*hy-bh/2; g.beginPath(); g.roundRect(x,y,bw,bh,9);
      if(!wire){ g.fillStyle=b.root?rgba(C.B,0.18):rgba(C.A,0.14); g.fill(); }
      g.strokeStyle=wire?rgba('#22d8f5',0.5):(b.root?rgba('#a78bfa',0.9):rgba('#6d9aff',0.85)); g.lineWidth=1.2; g.stroke();
      if(!wire){ g.fillStyle=rgba('#dfe9ff',0.55); g.fillRect(x+10,y+11,b.root?30:24,3); g.fillStyle=rgba('#9db8ff',0.4); g.fillRect(x+10,y+20,16,3); }
    });
  }
  draw(g,w,h,tt){
    bgFill(g,w,h); const C=this.C, hy=h*0.52;
    this.drawScheme(g,w,hy,tt,false,C);
    g.save(); g.translate(0,2*hy); g.scale(1,-1); this.drawScheme(g,w,hy,tt,true,C); g.restore();
    const fade=g.createLinearGradient(0,hy,0,h); fade.addColorStop(0,'rgba(8,13,36,0.25)'); fade.addColorStop(1,'rgba(7,13,36,0.96)'); g.fillStyle=fade; g.fillRect(0,hy,w,h-hy);
    const gl=g.createLinearGradient(0,0,w,0); gl.addColorStop(0,rgba('#22d8f5',0)); gl.addColorStop(0.5,rgba('#22d8f5',0.7)); gl.addColorStop(1,rgba('#22d8f5',0)); g.fillStyle=gl; g.fillRect(w*0.06,hy-0.5,w*0.88,1.4);
    glowDot(g,w/2,hy,60,C.A,0.10+0.04*Math.sin(TAU*2*tt));
    const rn=rng(31); for(let i=0;i<14;i++){ const px=rn()*w, sp2=1+Math.floor(rn()*2), ph=rn(); const p=(tt*sp2+ph)%1; const py=hy+p*(h-hy)*0.9; g.fillStyle=rgba('#7fb2ff',0.35*Math.sin(Math.PI*p)); g.fillRect(px,py,1.5,1.5); }
    g.textAlign='center'; g.letterSpacing='3px'; g.font='500 10px ui-monospace, Menlo, monospace'; g.fillStyle=rgba('#9db8ff',0.6); g.fillText('PALLADIUM · DIGITAL TWIN', w/2, h*0.955); g.letterSpacing='0px';
  }
});

/* 1d — Data Core: matrix rain converging on P monogram */
customElements.define('pd-data-core', class extends PdBase{
  period = 8;
  init(){ const rn=rng(5); this.cols=[]; for(let i=0;i<13;i++){ const chars=[]; for(let j=0;j<48;j++){ const r2=rn(); chars.push({c:r2<0.4?'0':r2<0.8?'1':'·', a:0.25+rn()*0.75}); } this.cols.push({x:(i+0.5)/13, k:1+Math.floor(rn()*2), ph:rn(), al:0.10+rn()*0.17, chars}); } this.sparks=[]; for(let i=0;i<8;i++) this.sparks.push({ph:rn(), ang:rn()*TAU}); }
  draw(g,w,h,tt){
    bgFill(g,w,h); const C=this.C, cx=w/2, cy=h*0.48;
    const cellH=16, total=48*cellH;
    g.font='11px ui-monospace, Menlo, monospace'; g.textAlign='center';
    for(const col of this.cols){ const x=col.x*w; const off=((tt*col.k+col.ph)%1)*total; for(let j=0;j<48;j++){ let y=(j*cellH+off)%total - cellH; if(y<-cellH||y>h+cellH) continue; const ch=col.chars[j]; g.fillStyle=rgba(j%7===0?'#22d8f5':'#6d9aff', col.al*ch.a); g.fillText(ch.c,x,y); } }
    const dim=g.createRadialGradient(cx,cy,20,cx,cy,190); dim.addColorStop(0,'rgba(8,14,38,0.92)'); dim.addColorStop(1,'rgba(8,14,38,0)'); g.fillStyle=dim; g.fillRect(0,0,w,h);
    for(let k=0;k<3;k++){ const p=(tt*2+k/3)%1; const r=54+p*150, a=(1-p)*0.35*Math.min(p*5,1); g.strokeStyle=rgba('#22d8f5',a); g.lineWidth=1.2; g.beginPath(); g.arc(cx,cy,r,0,TAU); g.stroke(); }
    g.globalCompositeOperation='lighter';
    for(const s of this.sparks){ const p=(tt*2+s.ph)%1; const r=(1-p)*220+8; const ang=s.ang+p*2.2; const x=cx+Math.cos(ang)*r, y=cy+Math.sin(ang)*r*1.25; glowDot(g,x,y,6,C.H,0.6*Math.sin(Math.PI*p)); }
    g.globalCompositeOperation='source-over';
    glowDot(g,cx,cy,110,C.A,0.16+0.05*Math.sin(TAU*2*tt));
    const hex=(r,rot)=>{ g.beginPath(); for(let i=0;i<6;i++){ const a2=rot+i*TAU/6-Math.PI/2; i?g.lineTo(cx+r*Math.cos(a2),cy+r*Math.sin(a2)):g.moveTo(cx+r*Math.cos(a2),cy+r*Math.sin(a2)); } g.closePath(); };
    const gr=g.createLinearGradient(cx-60,cy-60,cx+60,cy+60); gr.addColorStop(0,C.A); gr.addColorStop(1,C.B);
    hex(58,tt*TAU/6); g.strokeStyle=rgba(C.B,0.28); g.lineWidth=1; g.stroke();
    const br=48+2*Math.sin(TAU*2*tt); hex(br,0); g.fillStyle='rgba(10,17,44,0.88)'; g.fill(); g.strokeStyle=gr; g.lineWidth=2; g.stroke();
    g.font='700 40px "Space Grotesk", system-ui, sans-serif'; g.textAlign='center'; g.textBaseline='middle'; g.fillStyle='#ffffff'; g.fillText('P',cx,cy+2); g.textBaseline='alphabetic';
    wordmark(g,cx,cy+112,17,0.9,C,'');
    g.textAlign='center'; g.letterSpacing='3px'; g.font='500 9.5px ui-monospace, Menlo, monospace'; g.fillStyle=rgba('#9db8ff',0.55); g.fillText('12 PRODUCTS · ONE CORE', cx, cy+140); g.letterSpacing='0px';
  }
});

/* 1e — Orchestration: orbits around an AI core */
customElements.define('pd-orbits', class extends PdBase{
  period = 10;
  init(){ const rn=rng(17); this.orbits=[{rx:80,n:3,rev:2},{rx:124,n:2,rev:-1},{rx:168,n:2,rev:1}].map(o=>({...o, sats:Array.from({length:o.n},()=>({off:rn(), bc:rn()}))})); }
  draw(g,w,h,tt){
    bgFill(g,w,h); stars(g,w,h,3,26,tt,0.7);
    const C=this.C, cx=w/2, cy=h*0.40, tilt=-0.30, cT=Math.cos(tilt), sT=Math.sin(tilt);
    let flash=0; const front=[], back=[];
    for(const o of this.orbits){ const ry=o.rx*0.36;
      g.save(); g.translate(cx,cy); g.rotate(tilt); g.strokeStyle=rgba('#7fa2ff',0.20); g.lineWidth=1; g.beginPath(); g.ellipse(0,0,o.rx,ry,0,0,TAU); g.stroke(); g.restore();
      for(const s of o.sats){ const a=TAU*(o.rev*tt+s.off); const lx=o.rx*Math.cos(a), ly=ry*Math.sin(a); const X=cx+lx*cT-ly*sT, Y=cy+lx*sT+ly*cT; const isFront=Math.sin(a)>0;
        const trail=[]; for(let q=0;q<9;q++){ const a2=a-q*0.075*Math.sign(o.rev); const tx=o.rx*Math.cos(a2), ty2=ry*Math.sin(a2); trail.push([cx+tx*cT-ty2*sT, cy+tx*sT+ty2*cT, 1-q/9]); }
        const bk=wgauss(tt, s.bc, 0.016); flash+=bk;
        (isFront?front:back).push({X,Y,trail,bk,isFront});
      }
    }
    const drawSat=(s)=>{ const al=s.isFront?1:0.42; g.lineWidth=1.6; for(let q=1;q<s.trail.length;q++){ g.strokeStyle=rgba(C.A,0.5*s.trail[q][2]*al); g.beginPath(); g.moveTo(s.trail[q-1][0],s.trail[q-1][1]); g.lineTo(s.trail[q][0],s.trail[q][1]); g.stroke(); }
      if(s.bk>0.03){ const gr=g.createLinearGradient(s.X,s.Y,cx,cy); gr.addColorStop(0,rgba('#22d8f5',0.85*s.bk)); gr.addColorStop(1,rgba('#22d8f5',0)); g.strokeStyle=gr; g.lineWidth=1.4; g.beginPath(); g.moveTo(s.X,s.Y); g.lineTo(cx,cy); g.stroke(); }
      glowDot(g,s.X,s.Y,9,C.H,0.5*al); g.fillStyle=rgba('#ffffff',0.95*al); g.beginPath(); g.arc(s.X,s.Y,2.6,0,TAU); g.fill(); };
    back.forEach(drawSat);
    glowDot(g,cx,cy,90,C.A,0.22+0.12*Math.min(flash,1)+0.04*Math.sin(TAU*2*tt));
    const orb=g.createRadialGradient(cx-8,cy-10,2,cx,cy,32); orb.addColorStop(0,'#eaf2ff'); orb.addColorStop(0.4,C.A); orb.addColorStop(1,C.B); g.fillStyle=orb; g.beginPath(); g.arc(cx,cy,30+1.2*Math.sin(TAU*2*tt),0,TAU); g.fill();
    g.strokeStyle=rgba('#bcd3ff',0.35); g.lineWidth=1; g.beginPath(); g.arc(cx,cy,44,0,TAU); g.stroke();
    g.strokeStyle=rgba('#22d8f5',0.7); g.lineWidth=1.5; g.beginPath(); g.arc(cx,cy,44,TAU*tt,TAU*tt+0.7); g.stroke();
    front.forEach(drawSat);
    wordmark(g,cx,h*0.845,Math.max(20,w*0.082),0.95,C,'AI ORCHESTRATED COMPANY');
  }
});

/* 1f — Synapse wave: minimal living signal */
customElements.define('pd-synapse', class extends PdBase{
  period = 7;
  init(){ const rn=rng(23); this.branches=[]; for(let i=0;i<7;i++) this.branches.push({fx:0.14+i*0.12+rn()*0.04, dir:i%2?1:-1, len:55+rn()*55, ph:rn(), j1:(rn()-0.5)*40, j2:(rn()-0.5)*30}); this.riders=[{ph:0.1,sp:1},{ph:0.45,sp:1},{ph:0.7,sp:2},{ph:0.9,sp:1}]; }
  waveY(x,w,h,tt){ const ym=h*0.5, E=Math.exp(-(((x-w/2)/(w*0.34))**2)); return ym + E*26*Math.sin(TAU*(x/(w/3) - 2*tt)) + E*10*Math.sin(TAU*(x/(w/1.5) + tt)); }
  draw(g,w,h,tt){
    bgFill(g,w,h);
    const C=this.C;
    glowDot(g,w/2,h*0.5,w*0.75,C.B,0.06+0.03*Math.sin(TAU*tt));
    g.globalCompositeOperation='lighter';
    g.lineWidth=2; g.strokeStyle=rgba(C.A,0.85); g.beginPath();
    for(let i=0;i<=96;i++){ const x=i/96*w, y=this.waveY(x,w,h,tt); i?g.lineTo(x,y):g.moveTo(x,y); } g.stroke();
    g.lineWidth=1.2; g.strokeStyle=rgba(C.B,0.5); g.beginPath();
    for(let i=0;i<=96;i++){ const x=i/96*w; const E=Math.exp(-(((x-w/2)/(w*0.3))**2)); const y=h*0.5+14+E*16*Math.sin(TAU*(x/(w/2)+tt)); i?g.lineTo(x,y):g.moveTo(x,y); } g.stroke();
    g.globalCompositeOperation='source-over';
    for(const b of this.branches){ const gp=(tt+b.ph)%1; let ext=0, tip=0;
      if(gp<0.22) ext=gp/0.22; else if(gp<0.58){ ext=1; tip=1; } else if(gp<0.8) ext=1-(gp-0.58)/0.22; else continue;
      ext=ext*ext*(3-2*ext);
      const x0=b.fx*w, y0=this.waveY(x0,w,h,tt); const p1=[x0+b.j1*0.4, y0+b.dir*b.len*0.5], p2=[x0+b.j1, y0+b.dir*b.len], p3=[x0+b.j1+b.j2, y0+b.dir*(b.len+34)];
      const pts=[[x0,y0],p1,p2,p3]; const totalSegs=3, drawTo=ext*totalSegs;
      g.strokeStyle=rgba(C.A,0.6); g.lineWidth=1.1; g.beginPath(); g.moveTo(x0,y0);
      for(let s2=0;s2<totalSegs;s2++){ const f=Math.min(Math.max(drawTo-s2,0),1); if(f<=0) break; const A=pts[s2],B=pts[s2+1]; g.lineTo(A[0]+(B[0]-A[0])*f, A[1]+(B[1]-A[1])*f); } g.stroke();
      if(tip){ const beat=0.6+0.4*Math.sin(TAU*(tt*7+b.ph)); glowDot(g,p3[0],p3[1],10*beat,'#22d8f5',0.45); g.fillStyle=rgba('#c9f6ff',0.9); g.beginPath(); g.arc(p3[0],p3[1],2.2,0,TAU); g.fill(); }
    }
    for(const r of this.riders){ const x=((tt*r.sp+r.ph)%1)*w, y=this.waveY(x,w,h,tt); const E=Math.exp(-(((x-w/2)/(w*0.4))**2)); glowDot(g,x,y,9,C.H,0.5*E+0.1); g.fillStyle=rgba('#ffffff',0.8); g.beginPath(); g.arc(x,y,1.8,0,TAU); g.fill(); }
    const rn=rng(11); for(let i=0;i<18;i++){ const x=rn()*w, y2=rn()*h, a=rn(); g.fillStyle=rgba('#7fa2ff',0.10+0.08*Math.sin(TAU*(tt+a))); g.fillRect(x+6*Math.sin(TAU*(tt+a)), y2, 1.4,1.4); }
  }
});

/* 1g — Holo Twin: wireframe company assembling from light */
customElements.define('pd-holo-build', class extends PdBase{
  period = 9;
  init(){ this.bl=[[0,0,54],[1,0,84],[2,0,46],[0,1,110],[1,1,64],[2,1,80],[3,1,44],[1,2,52],[2,2,98],[3,2,60]].map((b,i)=>({gx:b[0],gy:b[1],hgt:b[2],o:i})); }
  draw(g,w,h,tt,t){
    bgFill(g,w,h); const C=this.C;
    const cx=w/2-18, by=h*0.62, s=38;
    const px=(gx,gy)=>[cx+(gx-gy)*s, by-(gx+gy)*s*0.5];
    g.lineWidth=0.8;
    for(let i=-2;i<=5;i++){ const a=px(i,-2), b=px(i,5); g.strokeStyle=rgba(C.A,0.10); g.beginPath(); g.moveTo(a[0],a[1]); g.lineTo(b[0],b[1]); g.stroke(); const c2=px(-2,i), d2=px(5,i); g.beginPath(); g.moveTo(c2[0],c2[1]); g.lineTo(d2[0],d2[1]); g.stroke(); }
    const sw=(tt*1.4)%1.4-0.2; const swX=sw*w*1.4-w*0.2;
    const swGr=g.createLinearGradient(swX-70,0,swX+70,0); swGr.addColorStop(0,rgba('#22d8f5',0)); swGr.addColorStop(0.5,rgba('#22d8f5',0.05)); swGr.addColorStop(1,rgba('#22d8f5',0)); g.fillStyle=swGr; g.fillRect(swX-70,by-s*3.6,140,s*3.8);
    const blocks=[...this.bl].sort((a,b)=>(a.gx+a.gy)-(b.gx+b.gy));
    for(const b of blocks){
      const st=0.04+b.o*0.028, e=Math.min(Math.max((tt-st)/0.1,0),1), ee=e*e*(3-2*e);
      const ds=0.76+b.o*0.009, q=Math.min(Math.max((tt-ds)/0.09,0),1);
      const A=ee*(1-q); if(A<=0.001) continue;
      const rise=(1-ee)*26;
      const [bx0,by0]=px(b.gx,b.gy); const yb=by0+rise;
      const hh=b.hgt*ee;
      const top=yb-hh, hw=s*0.86, hd=s*0.43;
      const flick=0.8+0.2*Math.sin(TAU*(tt*27)+b.o*2.1);
      const al=A*flick;
      const P0=[bx0-hw,top-0+hd*0], Pl=[bx0-hw,top+hd], Pr=[bx0+hw,top+hd], Pt=[bx0,top], Pb=[bx0,top+hd*2];
      g.strokeStyle=rgba('#4fd7f5',0.75*al); g.lineWidth=1.1;
      g.beginPath(); g.moveTo(Pt[0],Pt[1]); g.lineTo(Pl[0],Pl[1]); g.lineTo(Pb[0],Pb[1]); g.lineTo(Pr[0],Pr[1]); g.closePath();
      g.fillStyle=rgba(C.A,0.10*al); g.fill(); g.stroke();
      g.beginPath(); g.moveTo(Pl[0],Pl[1]); g.lineTo(Pl[0],Pl[1]+hh-hd); g.moveTo(Pr[0],Pr[1]); g.lineTo(Pr[0],Pr[1]+hh-hd); g.moveTo(Pb[0],Pb[1]); g.lineTo(Pb[0],Pb[1]+hh-hd); g.stroke();
      g.beginPath(); g.moveTo(Pl[0],Pl[1]+hh-hd); g.lineTo(Pb[0],Pb[1]+hh-hd); g.lineTo(Pr[0],Pr[1]+hh-hd); g.strokeStyle=rgba('#4fd7f5',0.45*al); g.stroke();
      const pu=wgauss(tt,0.5+b.o*0.024,0.014); if(pu>0.05){ glowDot(g,bx0,top+hd,34,'#22d8f5',0.35*pu*A); }
      if(e>0&&e<1){ g.fillStyle=rgba('#c9f6ff',0.9); g.fillRect(bx0-hw,yb-hh*1.04,hw*2,1.4); }
      if(q>0&&q<1){ const rn2=rng(b.o*7+1); for(let k2=0;k2<6;k2++){ const ox=(rn2()-0.5)*hw*2, oy=rn2()*hh; g.fillStyle=rgba('#9beaff',0.7*(1-q)); g.fillRect(bx0+ox, top+oy-q*40, 1.6,1.6); } }
      if(tt>0.45&&tt<0.76&&b.hgt>80){ const p=(tt*3+b.o*0.3)%1; g.fillStyle=rgba('#c9f6ff',0.7*Math.sin(Math.PI*p)); g.fillRect(bx0-0.8, top-8-p*36, 1.6,1.6); }
    }
    const scy=((tt*2)%1)*h; g.fillStyle=rgba('#7fd7ff',0.05); g.fillRect(0,scy,w,26);
    g.textAlign='left'; g.letterSpacing='2.5px'; g.font='500 10px ui-monospace, Menlo, monospace';
    g.fillStyle=rgba('#c9d9ff',0.7); g.fillText('PALLADIUM', 18, 30);
    g.fillStyle=rgba('#9db8ff',0.45); g.fillText('DIGITAL TWIN · BUILD', 18, 46); g.letterSpacing='0px';
    const blink=Math.sin(TAU*tt*4)>0; if(blink){ g.fillStyle=rgba('#22d8f5',0.8); g.fillRect(w-26,22,6,6); }
  }
});
