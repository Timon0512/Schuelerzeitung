const fs = require('node:fs');
const path = require('node:path');
const lock = JSON.parse(fs.readFileSync('package-lock.json', 'utf8'));
const notices = [];
for (const [directory, info] of Object.entries(lock.packages)) {
  if (!directory || info.dev || info.optional) continue;
  const license = fs.readdirSync(directory).find(name => /^licen[sc]e(?:\..*)?$/i.test(name));
  if (!license) throw new Error(`Missing license for ${directory}`);
  notices.push(`${directory.replace(/^node_modules\//, '')} ${info.version}\n${fs.readFileSync(path.join(directory, license), 'utf8')}`);
}
fs.writeFileSync('news/static/news/THIRD-PARTY-LICENSES.txt', notices.join('\n\n----------------\n\n'));
