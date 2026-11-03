const fs = require('fs');
const path = require('path');
const {minify} = require('terser');
const root = path.resolve(__dirname, '..');
async function build() {
  const files = [
    ['souwers-formulary.js', 'souwers-formulary-v2.7.0.js', 'SOUWERS Formulary 2.7.0'],
    ['souwers-account-formulary.js', 'souwers-account-formulary-v1.0.3.js', 'SOUWERS account formulary bridge 1.0.3']
  ];
  fs.mkdirSync(path.join(root, 'scripts'), {recursive: true});
  for (const [input, output, banner] of files) {
    const result = await minify(fs.readFileSync(path.join(root, 'src', input), 'utf8'), {
      compress: false, mangle: false, format: {comments: false, preamble: '/* ' + banner + ' */'}
    });
    fs.writeFileSync(path.join(root, 'scripts', output), result.code + '\n');
  }
  fs.copyFileSync(path.join(root, 'src/souwers-formulary.css'), path.join(root, 'scripts/souwers-formulary-v2.7.0.css'));
}
build().catch(error => {console.error(error); process.exitCode = 1;});
