/* eslint-disable test/no-import-node-test */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

test('psychology previewer component exists with required sections', async () => {
  const content = await readFile('src/components/PsychologyPreviewer/index.vue', 'utf8');

  assert.match(content, /usePsychologyPreviewerStore/);
  assert.match(content, /心理分析器/);
  assert.match(content, /相关文档/);
  assert.match(content, /previewer-shell/);
  assert.match(content, /analysis-code/);
  assert.match(content, /title-accent/);
  assert.match(content, /previewer-doc-body/);
});

test('chat senders include previewer toggle and component', async () => {
  const defaultChat = await readFile('src/pages/chat/layouts/chatDefaul/index.vue', 'utf8');
  const chatWithId = await readFile('src/pages/chat/layouts/chatWithId/index.vue', 'utf8');

  for (const content of [defaultChat, chatWithId]) {
    assert.match(content, /Popover/);
    assert.match(content, /PsychologyPreviewer/);
    assert.match(content, /预览器/);
    assert.match(content, /trigger="click"/);
    assert.match(content, /previewerPopoverStyle/);
    assert.match(content, /min\(360px, calc\(100vw - 32px\)\)/);
    assert.doesNotMatch(content, /width: `\$\{senderRect\.width\}px`/);
    assert.doesNotMatch(content, /<PsychologyPreviewer v-if="isPreviewerVisible" class="mt-12px"/);
    assert.doesNotMatch(content, /function togglePreviewer/);
  }
});

test('chat with id hides thinking chain and updates previewer from reasoning chunks', async () => {
  const content = await readFile('src/pages/chat/layouts/chatWithId/index.vue', 'utf8');

  assert.match(content, /parsePsychologyPreview/);
  assert.match(content, /previewerStore\.setPreviewData/);
  assert.doesNotMatch(content, /<Thinking\b/);
});

test('psychology previewer store parses mock reasoning content', async () => {
  const content = await readFile('src/stores/modules/psychologyPreviewer.ts', 'utf8');

  assert.match(content, /export function parsePsychologyPreview/);
  assert.match(content, /心理分析器：/);
  assert.match(content, /相关文档：/);
  assert.match(content, /usePsychologyPreviewerStore/);
});
