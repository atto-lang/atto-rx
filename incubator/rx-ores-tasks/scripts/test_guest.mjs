// Explicit guest-only test runner. This is NOT run by stable rx-ores CI.
// Example after building an *approved* exact-source Task compiler:
// ORES_CLASSPATH='...' node incubator/rx-ores-tasks/scripts/test_guest.mjs
//
// Success requires actual compiler --check AND guest execution. It is not
// inferred from a host model, a zero-step Actions run, or a reference trace.
import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const cp = process.env.ORES_CLASSPATH;
if (!cp) {
  console.error('NOT_EXECUTED: ORES_CLASSPATH missing (requires an exact Task-enabled compiler).');
  process.exit(2);
}
const java = process.env.JAVA || 'java';
const prefix = ['--enable-native-access=ALL-UNNAMED',
  '-Dpolyglot.engine.WarnInterpreterOnly=false', '-cp', cp,
  'dev.oreslang.launcher.OresMain'];
const src = resolve(root, 'src/rx.ores');
const cases = ['task_single', 'task_cancel_before'];

function run(args, expected) {
  const result = spawnSync(java, [...prefix, ...args], {
    encoding: 'utf8', timeout: 30000, maxBuffer: 1024 * 1024,
    shell: false
  });
  if (result.error || result.status !== 0 || /: error:/.test(result.stderr || '')) {
    console.error('FAIL guest', args, result.error || result.stderr || result.stdout);
    process.exit(1);
  }
  if (expected !== undefined && (result.stdout || '').trimEnd() !== expected) {
    console.error('FAIL guest expected', JSON.stringify(expected),
      'actual', JSON.stringify((result.stdout || '').trimEnd()));
    process.exit(1);
  }
}

run(['--check', src]);
for (const name of cases) {
  const fixture = resolve(root, 'tests', name + '.ores');
  const oracle = readFileSync(resolve(root, 'tests', name + '.out'), 'utf8').trimEnd();
  run(['--check', fixture]);
  run([fixture], oracle);
}
console.log('PASS guest Task candidate fixtures=' + cases.length +
  ' (compiler SHA/provenance NOT_ATTESTED; no backend parity claim)');
