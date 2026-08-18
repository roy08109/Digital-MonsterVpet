const fs = require('fs');
const zlib = require('zlib');

// 简易 PNG 解码（支持 8-bit RGB/RGBA + 1/2/4/8-bit 索引色，无隔行）
function decodePng(path){
  const buf = fs.readFileSync(path);
  if(buf.readUInt32BE(0) !== 0x89504e47) throw new Error('not png');
  let pos = 8;
  let width=0, height=0, bitDepth=0, colorType=0, interlace=0;
  const idat = [];
  let plte = null, trns = null;
  while(pos < buf.length){
    const len = buf.readUInt32BE(pos);
    const type = buf.toString('ascii', pos+4, pos+8);
    const data = buf.slice(pos+8, pos+8+len);
    if(type === 'IHDR'){
      width = data.readUInt32BE(0);
      height = data.readUInt32BE(4);
      bitDepth = data[8];
      colorType = data[9];
      interlace = data[12];
    } else if(type === 'PLTE'){
      plte = data;
    } else if(type === 'tRNS'){
      trns = data;
    } else if(type === 'IDAT'){
      idat.push(data);
    } else if(type === 'IEND'){
      break;
    }
    pos += 12 + len;
  }
  if(interlace !== 0) throw new Error('unsupported interlace');
  const raw = zlib.inflateSync(Buffer.concat(idat));

  const out = Buffer.alloc(width*height*4); // RGBA

  if(colorType === 3){ // 索引色
    const pal = [];
    for(let i=0; i<plte.length; i+=3){
      pal.push([plte[i], plte[i+1], plte[i+2], 255]);
    }
    if(trns){
      for(let i=0; i<trns.length; i++){ if(pal[i]) pal[i][3] = trns[i]; }
    }
    const bits = bitDepth;
    const pixelsPerByte = 8 / bits;
    const stride = Math.ceil(width * bits / 8);
    const bpp = Math.max(1, Math.ceil(bits / 8)); // 滤波单位：bitDepth<8 时 bpp=1
    let prev = Buffer.alloc(stride);
    let rp = 0;
    const mask = (1<<bits) - 1;
    for(let y=0; y<height; y++){
      const filter = raw[rp++];
      const row = Buffer.alloc(stride);
      raw.copy(row, 0, rp, rp+stride);
      rp += stride;
      for(let x=0; x<stride; x++){
        const a = x >= bpp ? row[x-bpp] : 0;
        const b = prev[x];
        const c = x >= bpp ? prev[x-bpp] : 0;
        let val = row[x];
        if(filter === 1) val = (val + a) & 0xff;
        else if(filter === 2) val = (val + b) & 0xff;
        else if(filter === 3) val = (val + ((a+b)>>1)) & 0xff;
        else if(filter === 4){
          const p = a + b - c;
          const pa = Math.abs(p-a), pb = Math.abs(p-b), pc = Math.abs(p-c);
          const pr = (pa<=pb && pa<=pc) ? a : (pb<=pc ? b : c);
          val = (val + pr) & 0xff;
        }
        row[x] = val;
      }
      for(let x=0; x<width; x++){
        const byteIdx = (x * bits) >> 3;
        const bitShift = bits === 1 ? (7 - (x & 7)) : (bits === 2 ? (6 - ((x & 3)*2)) : (bits === 4 ? (4 - ((x & 1)*4)) : 0));
        const idx = (row[byteIdx] >> bitShift) & mask;
        const di = (y*width + x)*4;
        const c = pal[idx] || [0,0,0,0];
        out[di]=c[0]; out[di+1]=c[1]; out[di+2]=c[2]; out[di+3]=c[3];
      }
      prev = row;
    }
  } else {
    const channels = colorType === 6 ? 4 : (colorType === 2 ? 3 : 1);
    if(bitDepth !== 8) throw new Error('unsupported bitDepth for truecolor '+bitDepth);
    const stride = width * channels;
    const bpp = channels;
    let prev = Buffer.alloc(stride);
    let rp = 0;
    for(let y=0; y<height; y++){
      const filter = raw[rp++];
      const row = Buffer.alloc(stride);
      raw.copy(row, 0, rp, rp+stride);
      rp += stride;
      for(let x=0; x<stride; x++){
        const a = x >= bpp ? row[x-bpp] : 0;
        const b = prev[x];
        const c = x >= bpp ? prev[x-bpp] : 0;
        let val = row[x];
        if(filter === 1) val = (val + a) & 0xff;
        else if(filter === 2) val = (val + b) & 0xff;
        else if(filter === 3) val = (val + ((a+b)>>1)) & 0xff;
        else if(filter === 4){
          const p = a + b - c;
          const pa = Math.abs(p-a), pb = Math.abs(p-b), pc = Math.abs(p-c);
          const pr = (pa<=pb && pa<=pc) ? a : (pb<=pc ? b : c);
          val = (val + pr) & 0xff;
        }
        row[x] = val;
      }
      for(let x=0; x<width; x++){
        const si = x*channels;
        const di = (y*width + x)*4;
        if(channels === 4){ out[di]=row[si]; out[di+1]=row[si+1]; out[di+2]=row[si+2]; out[di+3]=row[si+3]; }
        else if(channels === 3){ out[di]=row[si]; out[di+1]=row[si+1]; out[di+2]=row[si+2]; out[di+3]=255; }
        else { out[di]=row[si]; out[di+1]=row[si]; out[di+2]=row[si]; out[di+3]=255; }
      }
      prev = row;
    }
  }
  return {width, height, data: out};
}

function bbox(png, sx, sy, w, h){
  let minX=1e9,minY=1e9,maxX=-1,maxY=-1,count=0;
  for(let y=0;y<h;y++) for(let x=0;x<w;x++){
    const px=sx+x, py=sy+y;
    const di=(py*png.width+px)*4;
    if(png.data[di+3] > 16){ count++; if(x<minX)minX=x; if(x>maxX)maxX=x; if(y<minY)minY=y; if(y>maxY)maxY=y; }
  }
  return {minX,minY,maxX,maxY,count};
}

const sprites = 'c:/Users/roy/CodeBuddy/Digital-MonsterVpet/Digital-MonsterVpet/sprites/';

for(const f of ['V1_Attack/V1_00_at.png']){
  const p = decodePng(sprites+f);
  console.log('火球图', f, '尺寸', p.width+'x'+p.height, 'bitDepth(见上)');
  const b = bbox(p,0,0,p.width,p.height);
  console.log('  非透明包围盒 x:', b.minX+'-'+b.maxX, ' y:', b.minY+'-'+b.maxY, ' 像素数', b.count);
  let rows=[];
  for(let y=0;y<p.height;y++){ let c=0; for(let x=0;x<p.width;x++){ const di=(y*p.width+x)*4; if(p.data[di+3]>16)c++; } rows.push(y+':'+c); }
  console.log('  行非透明计数:', rows.join(' '));
}

const dragon = decodePng(sprites+'V1/V1_00.png');
console.log('\n龙 sprite sheet V1_00.png 尺寸', dragon.width+'x'+dragon.height);
const PITCH = 17;
for(const frm of [0, 11]){
  const sx=frm*PITCH, sy=0;
  const b=bbox(dragon,sx,sy,16,16);
  console.log('  frame', frm, '(x='+sx+') 非透明包围盒 x:', b.minX+'-'+b.maxX, ' y:', b.minY+'-'+b.maxY, ' 像素数', b.count);
  let rows=[];
  for(let y=0;y<16;y++){ let c=0; for(let x=0;x<16;x++){ const di=((sy+y)*dragon.width+(sx+x))*4; if(dragon.data[di+3]>16)c++; } rows.push(y+':'+c); }
  console.log('   行非透明计数:', rows.join(' '));
}
