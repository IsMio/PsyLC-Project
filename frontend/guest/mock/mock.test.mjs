/* eslint-disable test/no-import-node-test */
import assert from 'node:assert/strict';
import { Buffer } from 'node:buffer';
import test from 'node:test';
import {
  createMockState,
  findMockRoute,
  mockRoutes,
  parseJsonBody,
  streamChat,
} from './index.mjs';

test('covers every frontend API route', () => {
  const routes = mockRoutes.map(route => `${route.method} ${route.path}`);

  assert.deepEqual(routes, [
    'POST /auth/login',
    'POST /resource/email/code',
    'POST /auth/register',
    'POST /auth/logout',
    'GET /system/session/list',
    'POST /system/session',
    'PUT /system/session',
    'GET /system/session/:id',
    'DELETE /system/session/:ids',
    'GET /system/message/list',
    'POST /system/message',
    'GET /system/model/modelList',
    'POST /chat/send',
  ]);
});

test('matches dynamic session routes and exposes params', () => {
  const match = findMockRoute('GET', '/system/session/session-12');

  assert.equal(match?.route.path, '/system/session/:id');
  assert.deepEqual(match?.params, { id: 'session-12' });
});

test('creates a session and returns it from the session detail route', async () => {
  const state = createMockState();
  const createMatch = findMockRoute('POST', '/system/session');
  const detailMatch = findMockRoute('GET', '/system/session/session-3');

  const createResult = await createMatch.route.handler({
    body: { sessionTitle: '新 mock 会话', sessionContent: 'hello mock', userId: 1 },
    params: createMatch.params,
    state,
  });
  const detailResult = await detailMatch.route.handler({
    body: {},
    params: { id: createResult.body.data.id },
    state,
  });

  assert.equal(createResult.body.code, 200);
  assert.equal(createResult.body.data.id, 'session-13');
  assert.equal(detailResult.body.data.sessionTitle, '新 mock 会话');
});

test('mock-session-1 defaults to the consultation dialogue', async () => {
  const state = createMockState();
  const match = findMockRoute('GET', '/system/message/list');

  const result = await match.route.handler({
    body: {},
    params: match.params,
    query: new URLSearchParams('sessionId=session-12'),
    state,
  });

  assert.equal(result.body.rows.length, 24);
  assert.equal(result.body.rows[0].role, 'user');
  assert.equal(
    result.body.rows[0].content,
    '咨询师，你好。我最近感觉心情很矛盾，有些迷茫，不知道怎么和朋友相处了。',
  );
  assert.equal(result.body.rows.at(-1).role, 'assistant');
  assert.equal(
    result.body.rows.at(-1).content,
    '请放心，改变和适应都需要时间。保持耐心，您会慢慢看到改变的。祝您一切顺利，期待听到您的好消息。如果需要，我的门永远为您敞开。',
  );
});

test('parses json request body safely', async () => {
  const body = await parseJsonBody({
    on(event, callback) {
      if (event === 'data')
        callback(Buffer.from('{"username":"demo"}'));
      if (event === 'end')
        callback();
      return this;
    },
  });

  assert.deepEqual(body, { username: 'demo' });
});

test('chat stream simulates delayed reasoning and streamed output', async () => {
  const writes = [];
  let ended = false;
  const res = {
    writeHead(status, headers) {
      this.status = status;
      this.headers = headers;
    },
    write(chunk) {
      writes.push({ chunk, time: Date.now() });
    },
    end() {
      ended = true;
    },
  };

  const startedAt = Date.now();
  await streamChat(res, { messages: [{ content: '测试流式输出' }] });

  const reasoningWrites = writes.filter(({ chunk }) => chunk.includes('reasoning_content'));
  const contentWrites = writes.filter(({ chunk }) => chunk.includes('content'));

  assert.equal(res.status, 200);
  assert.equal(res.headers['Content-Type'], 'text/event-stream; charset=utf-8');
  assert.ok(reasoningWrites.length >= 3);
  assert.ok(contentWrites.length >= 3);
  assert.ok(reasoningWrites.at(-1).time - startedAt >= 1000);
  assert.ok(contentWrites.at(-1).time - contentWrites[0].time >= 200);
  assert.equal(ended, true);
});

function createStreamResponseRecorder() {
  const writes = [];
  return {
    writes,
    res: {
      writeHead(status, headers) {
        this.status = status;
        this.headers = headers;
      },
      write(chunk) {
        writes.push(chunk);
      },
      end() {},
    },
  };
}

function collectStreamContent(writes) {
  return writes
    .join('')
    .split('\n\n')
    .filter(Boolean)
    .map(line => JSON.parse(line.replace(/^data:/u, '')))
    .map(chunk => chunk.choices?.[0].delta.content || '')
    .join('');
}

function collectStreamReasoning(writes) {
  return writes
    .join('')
    .split('\n\n')
    .filter(Boolean)
    .map(line => JSON.parse(line.replace(/^data:/u, '')))
    .map(chunk => chunk.choices?.[0].delta.reasoning_content || '')
    .join('');
}

function collectContentChunks(writes) {
  return writes
    .join('')
    .split('\n\n')
    .filter(Boolean)
    .map(line => JSON.parse(line.replace(/^data:/u, '')))
    .map(chunk => chunk.choices?.[0].delta.content)
    .filter(content => content != null && content !== '');
}

test('chat stream uses neutral preset for unclear input', async () => {
  const { writes, res } = createStreamResponseRecorder();

  await streamChat(res, { messages: [{ content: '1' }] });
  const streamText = writes.join('');
  const content = collectStreamContent(writes);

  assert.equal(content, '无法识别你的意思');
  assert.match(streamText, /心理分析器/);
  assert.match(streamText, /\\"sentiment\\":\\"neutral\\"/);
  assert.match(streamText, /\\"intensity\\":0/);
  assert.match(streamText, /相关文档：\[\]/);
});

test('chat preset waits before first reasoning output', async () => {
  const writes = [];
  const res = {
    writeHead(status, headers) {
      this.status = status;
      this.headers = headers;
    },
    write(chunk) {
      writes.push({ chunk, time: Date.now() });
    },
    end() {},
  };

  const startedAt = Date.now();
  await streamChat(res, { messages: [{ content: '1' }] });

  assert.match(writes[0].chunk, /reasoning_content/);
  assert.ok(writes[0].time - startedAt >= 750);
});

test('chat preset streams reply one character at a time', async () => {
  const { writes, res } = createStreamResponseRecorder();

  await streamChat(res, { messages: [{ content: '1' }] });
  const contentChunks = collectContentChunks(writes);

  assert.deepEqual(contentChunks.slice(0, 3), ['无', '法', '识']);
  assert.equal(contentChunks.join(''), '无法识别你的意思');
});

test('chat stream uses self harm preset and triggers replacement', async () => {
  const { writes, res } = createStreamResponseRecorder();

  await streamChat(res, { messages: [{ content: '我不想活了' }] });
  const streamText = writes.join('');

  assert.match(streamText, /如果你现在有伤害自己或他人的想法/);
  assert.match(streamText, /\\"sentiment\\":\\"negative\\"/);
  assert.match(streamText, /\\"intensity\\":10/);
  assert.match(streamText, /\\"emotions\\":\[\\"愤怒\\",\\"悲伤\\"\]/);
  assert.match(streamText, /"filtered":true/);
  assert.match(streamText, /"replace":true/);
});
test('chat 1', async () => {
  const { writes, res } = createStreamResponseRecorder();

  await streamChat(res, { messages: [{ content: '我很焦虑' }] });
  const streamText = writes.join('');

  assert.match(streamText, /您好，感谢您的信任，愿意在这里分享您的感受。请问您能详细描述一下，您为何焦虑吗？/);
  assert.match(streamText, /\\"sentiment\\":\\"negative\\"/);
  assert.match(streamText, /\\"intensity\\":10/);
  assert.match(streamText, /\\"emotions\\":\[,\\"悲伤\\"\]/);
});

test('chat stream supports exact continuous consultation dialogue inputs', async () => {
  const dialogueCases = [
    [
      '咨询师，你好。我最近感觉心情很矛盾，有些迷茫，不知道怎么和朋友相处了。',
      '您好，感谢您的信任，愿意在这里分享您的感受。请问您能详细描述一下，您所谓的“矛盾”和“迷茫”具体指的是什么吗？',
    ],
    [
      '就是我觉得自己最近变得特别自卑，好像总得不到朋友的理解和注意。我想和人接近，但又怕交流起来会变得很尴尬。',
      '感觉自己在社交中缺乏他人的关注和理解，是不是让您感到挺沮丧的？能分享一下，是什么情况让您觉得会变得尴尬吗？',
    ],
    [
      '对，沮丧是有的。就比如有时候聊到一半，我就不知道该说些什么好了，心里挺着急的。尤其是和久违的老朋友聊天，感觉没了从前的那股热情。',
      '看来您是担心找不到合适的话题继续交谈，会让聊天陷入沉默，这可能导致了您与朋友互动时的担忧。您有没有觉得这种担忧影响到您想要主动联系他们的心情呢？',
    ],
    [
      '是的，有时候想找他们聊聊，但又会担心聊着聊着就冷场了，所以有时候就算很想说点什么，最后也选择了沉默。',
      '您的感受非常正常，有时候确实会有这种担心。当沟通遇到障碍时，试着作为一个倾听者也是非常好的。您有没有尝试过通过一些肢体语言来表示您的参与感？',
    ],
    [
      '嗯，我有注意到自己在聊天时会点头或者微笑，但有时候觉得这样还是不够。',
      '您已经在用非言语的方式表达自己，这是很好的一个开始。您可以尝试用简短的回复或者提问来表现出您的参与和关心，比如：“哦，真的吗？”或者“那之后怎样了？”来延续对话，您觉得这样会对您有帮助吗？',
    ],
    [
      '这个建议听起来不错，我可以试试。但如果聊天内容不在我感兴趣的范围内，我还是很容易感到不自在。',
      '这很正常，我们总会对一些话题更感兴趣，对另一些则不那么感冒。如果可以，您可以试着扩展一下自己的兴趣范围，比如阅读或探索新事物，这样或许可以在交流中带来更多的话题和自信。您对此怎么看？',
    ],
    [
      '我确实可以试试这样做。其实我也有很多感想想和别人分享，但往往不敢说出口，怕他们不感兴趣。',
      '能够理解您的顾虑。与朋友分享自己的感想和经历其实是增进彼此关系的好方法。记住，朋友之间的交流不是考试，不需要对每次对话都做出完美的表现。您可以慢慢来，先分享一些小事，看看朋友的反应如何？',
    ],
    [
      '这倒是真的，我可能对自己要求太高了。我会尝试着先从一些小话题开始。',
      '对自己的宽容也是很重要的，无论是在社交上还是在其他方面。当您有机会时，尝试着分享一些自己舒适的话题，您可能会发现朋友们比您想象的要更加接纳和支持。',
    ],
    [
      '我觉得我可以按您说的方法试一试。但，要是没有效果，我该怎么办呢？我怕这样会让我更失望。',
      '我能理解您对尝试新事物的担心。我们无法预测每一步的结果，但尝试本身就是一个积极的过程。无论结果如何，您都可以从中学到一些东西，并且用这些经验来改进未来的尝试。您认为这样是否可以减轻一些尝试时的压力？',
    ],
    [
      '确实，我应该更加开放一点，看待尝试的过程，而不是只看结果。',
      '非常棒，这种开放的态度会让您在生活中有更多积极的体验。我们每个人都在学习如何更好地与人交流，这是一个不断进步的过程。您现在已经开始关注和改进自己的社交技巧了。',
    ],
    [
      '嗯，谈话让我感觉好多了。我会尝试用您给的建议和朋友们交流，希望能有所改变。',
      '很高兴能听到您感觉好一些了。记得，每一个小步骤都是进步的一部分。如果您在尝试的过程中遇到困难或者想要分享进展，随时欢迎您回来交流。我们一直在这里支持您。',
    ],
    [
      '谢谢您的鼓励，我也许需要一点时间来逐渐适应，但我会记住您的建议，并尝试去实践它们。',
      '请放心，改变和适应都需要时间。保持耐心，您会慢慢看到改变的。祝您一切顺利，期待听到您的好消息。如果需要，我的门永远为您敞开。',
    ],
  ];

  for (const [input, reply] of dialogueCases) {
    const { writes, res } = createStreamResponseRecorder();

    await streamChat(res, { messages: [{ content: input }] });
    const streamText = writes.join('');
    const content = collectStreamContent(writes);
    const reasoning = collectStreamReasoning(writes);

    assert.equal(content, reply);
    assert.match(streamText, /心理分析器/);
    assert.match(reasoning, /相关文档：\[/);
    assert.match(reasoning, /用户: 咨询师，你好。我最近感觉心情很矛盾/);
    assert.match(reasoning, /助手: 请放心，改变和适应都需要时间/);
  }
});
