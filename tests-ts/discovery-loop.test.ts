/**
 * Regression test for DiscoveryLoop.start() leaving a dangling setInterval
 * handle when maxIterations is satisfied on the very first (immediate) run.
 *
 * Run with: node tests-ts/discovery-loop.test.ts
 * (Node >= 22 strips TypeScript types natively — no build step needed.)
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import { DiscoveryLoop } from '../src/intelligence.ts';

function spyOnTimers() {
  const originalSetInterval = global.setInterval;
  const originalClearInterval = global.clearInterval;
  const created: any[] = [];
  const cleared: any[] = [];

  (global as any).setInterval = (fn: any, ms: any) => {
    const handle = originalSetInterval(fn, ms);
    created.push(handle);
    return handle;
  };
  (global as any).clearInterval = (handle: any) => {
    cleared.push(handle);
    return originalClearInterval(handle);
  };

  const restore = () => {
    global.setInterval = originalSetInterval;
    global.clearInterval = originalClearInterval;
    // Best-effort cleanup regardless of pass/fail so the test process exits.
    for (const handle of created) originalClearInterval(handle);
  };

  return { created, cleared, restore };
}

test('maxIterations satisfied on the immediate run must not leave an uncleared interval', async () => {
  const { created, cleared, restore } = spyOnTimers();
  try {
    const loop = new DiscoveryLoop();
    let calls = 0;

    await loop.start(async () => { calls++; }, 50, 1);

    assert.equal(calls, 1, 'callback should have run exactly once');
    assert.equal(loop.isRunning(), false, 'loop should report stopped');

    for (const handle of created) {
      assert.ok(
        cleared.includes(handle),
        'every interval armed by start() must be cleared once maxIterations stops the loop — ' +
        'otherwise the process never exits and the timer keeps firing no-op ticks forever'
      );
    }
  } finally {
    restore();
  }
});

test('maxIterations satisfied on a later interval tick still clears its own interval (no regression)', async () => {
  const { created, cleared, restore } = spyOnTimers();
  try {
    const loop = new DiscoveryLoop();
    let calls = 0;

    await loop.start(async () => { calls++; }, 20, 2);
    // Wait long enough for the second (interval-driven) tick to fire and stop.
    await new Promise((resolve) => setTimeout(resolve, 150));

    assert.equal(calls, 2, 'callback should have run exactly twice');
    assert.equal(loop.isRunning(), false, 'loop should report stopped');
    assert.equal(created.length, 1, 'exactly one interval should have been armed');
    assert.ok(cleared.includes(created[0]), 'the armed interval must be cleared when the bound is hit');
  } finally {
    restore();
  }
});

test('maxIterations = 0 (infinite) keeps running until stop() is called explicitly', async () => {
  const { created, cleared, restore } = spyOnTimers();
  try {
    const loop = new DiscoveryLoop();
    let calls = 0;

    await loop.start(async () => { calls++; }, 20, 0);
    assert.equal(loop.isRunning(), true, 'loop should still be running after the immediate tick');
    assert.equal(created.length, 1, 'an interval should have been armed for continued polling');

    await new Promise((resolve) => setTimeout(resolve, 70));
    assert.ok(calls >= 2, 'interval should have fired at least once more');

    loop.stop();
    assert.equal(loop.isRunning(), false);
    assert.ok(cleared.includes(created[0]), 'stop() must clear the armed interval');
  } finally {
    restore();
  }
});
