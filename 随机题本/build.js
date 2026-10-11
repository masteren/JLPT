// 合成随机题本网页：node 随机题本/build.js
// 读 data/*.js（每场一个 X("YYYY-MM",[[题号,题干,[选项×4],正解,要点],…])），
// 塞进 template.html 的 /*__DATA__*/ 处，输出 n1-random.html，并做三项校验。
const fs = require('fs'), path = require('path');
const dir = __dirname;
const files = fs.readdirSync(path.join(dir, 'data')).filter(f => f.endsWith('.js')).sort();
const data = files.map(f => fs.readFileSync(path.join(dir, 'data', f), 'utf8').trim()).join('\n');

// 校验：每场 40 题、题号连续、4 个选项、正解 1-4、★题语序与★位置一致
const all = []; const X = (e, a) => all.push([e, a]);
eval(data);
let bad = 0;
for (const [e, a] of all) {
  if (a.length !== 40) { console.log(e, '题数', a.length); bad++; }
  a.forEach((r, i) => {
    const [q, stem, opts, ans, note] = r;
    if (q !== i + 1) { console.log(e, '题号', q, '应为', i + 1); bad++; }
    if (opts.length !== 4 || !(ans >= 1 && ans <= 4)) { console.log(e, q, '选项/正解'); bad++; }
    if (q >= 36) {
      const m = note.match(/语序 (\d)-(\d)-(\d)-(\d)/);
      const pos = (stem.split('<b>★</b>')[0].match(/＿＿/g) || []).length;
      if (!m || +m[pos + 1] !== ans) { console.log(e, q, '★语序与正解不符'); bad++; }
    }
  });
}
if (bad) { console.error(`校验失败 ${bad} 处，未输出`); process.exit(1); }

// 第一次做真题时错的题：从 错题笔记/YYYY-MM.md 的「### 题号 ／ 我选 X ／ 正解 Y」标题读出
const firstNg = [];
for (const [e] of all) {
  const f = path.join(dir, '..', '错题笔记', e + '.md');
  if (!fs.existsSync(f)) { console.log(e, '没有错题笔记，第一次作答按「未知」处理'); continue; }
  const md = fs.readFileSync(f, 'utf8');
  for (const m of md.matchAll(/^###\s*(\d+)\s*／\s*我选/gm)) if (+m[1] <= 40) firstNg.push(e + '-' + m[1]);
}
const firstExams = all.map(([e]) => e).filter(e => fs.existsSync(path.join(dir, '..', '错题笔记', e + '.md')));

const out = fs.readFileSync(path.join(dir, 'template.html'), 'utf8')
  .replace('/*__DATA__*/', () => data)
  .replace('/*__FIRST__*/', () => `const FIRST_NG=new Set(${JSON.stringify(firstNg)});const FIRST_EXAMS=new Set(${JSON.stringify(firstExams)});`);
new Function(out.split('<script>')[1].split('</script>')[0]); // 语法检查
fs.writeFileSync(path.join(dir, 'n1-random.html'), out);
console.log(`OK：${all.length} 场 ${all.reduce((n, [, a]) => n + a.length, 0)} 题（第一次做错 ${firstNg.length} 题）→ 随机题本/n1-random.html`);
