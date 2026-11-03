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
  const delivery = path.join(root, 'files');
  fs.mkdirSync(delivery, {recursive: true});
  for (const name of ['souwers-formulary-v2.7.0.js', 'souwers-formulary-v2.7.0.css', 'souwers-account-formulary-v1.0.3.js']) {
    fs.copyFileSync(path.join(root, 'scripts', name), path.join(delivery, name));
  }
  for (const [input, output] of [
    ['archive/input-2026-11-03/souwers-premium-navigation-v1.0.0.js', 'souwers-premium-navigation-v1.0.0.js'],
    ['tilda/01-formulary-template.html', 'T123-account-formulary-block-1-v2.7.0.txt'],
    ['tilda/02-formulary-loader.html', 'T123-account-formulary-block-2-v2.7.0.txt'],
    ['tilda/T123-global-premium-navigation-v1.0.0.txt', 'T123-global-premium-navigation-v1.0.0.txt']
  ]) {
    fs.copyFileSync(path.join(root, input), path.join(delivery, output));
  }
}
build().catch(error => {console.error(error); process.exitCode = 1;});
