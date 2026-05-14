import { Buffer } from 'node:buffer';

const jsonHeaders = { 'Content-Type': 'application/json; charset=utf-8' };

function success(payload = {}) {
  return {
    status: 200,
    headers: jsonHeaders,
    body: {
      code: 200,
      msg: 'success',
      ...payload,
    },
  };
}

function now(offset = 0) {
  return new Date(Date.now() - offset).toISOString();
}

const consultationDialogueTurns = [
  {
    user: '咨询师，你好。我最近感觉心情很矛盾，有些迷茫，不知道怎么和朋友相处了。',
    assistant: '您好，感谢您的信任，愿意在这里分享您的感受。请问您能详细描述一下，您所谓的“矛盾”和“迷茫”具体指的是什么吗？',
    emotions: ['矛盾', '迷茫'],
  },
  {
    user: '就是我觉得自己最近变得特别自卑，好像总得不到朋友的理解和注意。我想和人接近，但又怕交流起来会变得很尴尬。',
    assistant: '感觉自己在社交中缺乏他人的关注和理解，是不是让您感到挺沮丧的？能分享一下，是什么情况让您觉得会变得尴尬吗？',
    emotions: ['自卑', '担忧'],
  },
  {
    user: '对，沮丧是有的。就比如有时候聊到一半，我就不知道该说些什么好了，心里挺着急的。尤其是和久违的老朋友聊天，感觉没了从前的那股热情。',
    assistant: '看来您是担心找不到合适的话题继续交谈，会让聊天陷入沉默，这可能导致了您与朋友互动时的担忧。您有没有觉得这种担忧影响到您想要主动联系他们的心情呢？',
    emotions: ['沮丧', '着急'],
  },
  {
    user: '是的，有时候想找他们聊聊，但又会担心聊着聊着就冷场了，所以有时候就算很想说点什么，最后也选择了沉默。',
    assistant: '您的感受非常正常，有时候确实会有这种担心。当沟通遇到障碍时，试着作为一个倾听者也是非常好的。您有没有尝试过通过一些肢体语言来表示您的参与感？',
    emotions: ['担心', '退缩'],
  },
  {
    user: '嗯，我有注意到自己在聊天时会点头或者微笑，但有时候觉得这样还是不够。',
    assistant: '您已经在用非言语的方式表达自己，这是很好的一个开始。您可以尝试用简短的回复或者提问来表现出您的参与和关心，比如：“哦，真的吗？”或者“那之后怎样了？”来延续对话，您觉得这样会对您有帮助吗？',
    emotions: ['不安'],
  },
  {
    user: '这个建议听起来不错，我可以试试。但如果聊天内容不在我感兴趣的范围内，我还是很容易感到不自在。',
    assistant: '这很正常，我们总会对一些话题更感兴趣，对另一些则不那么感冒。如果可以，您可以试着扩展一下自己的兴趣范围，比如阅读或探索新事物，这样或许可以在交流中带来更多的话题和自信。您对此怎么看？',
    emotions: ['不自在'],
  },
  {
    user: '我确实可以试试这样做。其实我也有很多感想想和别人分享，但往往不敢说出口，怕他们不感兴趣。',
    assistant: '能够理解您的顾虑。与朋友分享自己的感想和经历其实是增进彼此关系的好方法。记住，朋友之间的交流不是考试，不需要对每次对话都做出完美的表现。您可以慢慢来，先分享一些小事，看看朋友的反应如何？',
    emotions: ['顾虑', '害怕'],
  },
  {
    user: '这倒是真的，我可能对自己要求太高了。我会尝试着先从一些小话题开始。',
    assistant: '对自己的宽容也是很重要的，无论是在社交上还是在其他方面。当您有机会时，尝试着分享一些自己舒适的话题，您可能会发现朋友们比您想象的要更加接纳和支持。',
    emotions: ['自责'],
  },
  {
    user: '我觉得我可以按您说的方法试一试。但，要是没有效果，我该怎么办呢？我怕这样会让我更失望。',
    assistant: '我能理解您对尝试新事物的担心。我们无法预测每一步的结果，但尝试本身就是一个积极的过程。无论结果如何，您都可以从中学到一些东西，并且用这些经验来改进未来的尝试。您认为这样是否可以减轻一些尝试时的压力？',
    emotions: ['担心', '失望'],
  },
  {
    user: '确实，我应该更加开放一点，看待尝试的过程，而不是只看结果。',
    assistant: '非常棒，这种开放的态度会让您在生活中有更多积极的体验。我们每个人都在学习如何更好地与人交流，这是一个不断进步的过程。您现在已经开始关注和改进自己的社交技巧了。',
    emotions: ['开放'],
  },
  {
    user: '嗯，谈话让我感觉好多了。我会尝试用您给的建议和朋友们交流，希望能有所改变。',
    assistant: '很高兴能听到您感觉好一些了。记得，每一个小步骤都是进步的一部分。如果您在尝试的过程中遇到困难或者想要分享进展，随时欢迎您回来交流。我们一直在这里支持您。',
    emotions: ['缓解', '期待'],
  },
  {
    user: '谢谢您的鼓励，我也许需要一点时间来逐渐适应，但我会记住您的建议，并尝试去实践它们。',
    assistant: '请放心，改变和适应都需要时间。保持耐心，您会慢慢看到改变的。祝您一切顺利，期待听到您的好消息。如果需要，我的门永远为您敞开。',
    emotions: ['感谢', '期待'],
  },
];

const consultationDialogueMessages = consultationDialogueTurns.flatMap(turn => [
  { role: 'user', content: turn.user },
  { role: 'assistant', content: turn.assistant },
]);

export function createMockState() {
  return {
    nextSessionId: 3,
    nextMessageId: 27,
    sessions: [
      {
        id: 'session-12',
        sessionTitle: '社交咨询',
        sessionContent: consultationDialogueTurns[0].user,
        remark: consultationDialogueTurns[0].user,
        userId: 1,
        createTime: now(1000 * 60 * 5),
      },

    ],
    messages: [
      ...consultationDialogueMessages.map((message, index) => ({
        id: index + 1,
        sessionId: 'session-12',
        userId: 1,
        role: message.role,
        content: message.content,
        modelName: 'deepseek-chat',
        totalTokens: Math.ceil(message.content.length / 2),
      })),
      {
        id: 25,
        sessionId: 'mock-session-2',
        userId: 1,
        role: 'user',
        content: '帮我生成一个按钮组件',
        modelName: 'qwen-plus',
        totalTokens: 10,
      },
      {
        id: 26,
        sessionId: 'mock-session-2',
        userId: 1,
        role: 'assistant',
        content: '<think>先确认组件的职责和交互状态。</think>可以从 Element Plus 的按钮样式扩展，保持项目现有视觉风格。',
        modelName: 'qwen-plus',
        totalTokens: 58,
      },
    ],
    models: [
      {
        id: 1,
        category: 'chat',
        modelName: 'deepseek-chat',
        modelDescribe: '通用对话模型',
        modelPrice: 0,
        modelType: 'text',
        modelShow: 'DeepSeek Chat',
        systemPrompt: 'You are a helpful assistant.',
      },
      {
        id: 2,
        category: 'chat',
        modelName: 'qwen-plus',
        modelDescribe: '中文场景优化模型',
        modelPrice: 0,
        modelType: 'text',
        modelShow: 'Qwen Plus',
        systemPrompt: '你是一个中文 AI 助手。',
      },
    ],
  };
}

function pathToRegexp(path) {
  const keys = [];
  const pattern = path
    .split('/')
    .map((part) => {
      if (!part.startsWith(':'))
        return part.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      keys.push(part.slice(1));
      return '([^/]+)';
    })
    .join('/');

  return { keys, regexp: new RegExp(`^${pattern}$`) };
}

export function findMockRoute(method, pathname) {
  const normalizedMethod = method.toUpperCase();

  // mockRoutes is declared below to keep helper functions grouped before route data.
  // eslint-disable-next-line no-use-before-define
  for (const route of mockRoutes) {
    if (route.method !== normalizedMethod)
      continue;

    const { keys, regexp } = pathToRegexp(route.path);
    const matched = pathname.match(regexp);
    if (!matched)
      continue;

    return {
      route,
      params: Object.fromEntries(keys.map((key, index) => [key, decodeURIComponent(matched[index + 1])])),
    };
  }

  return null;
}

export function parseJsonBody(req) {
  return new Promise((resolve) => {
    const chunks = [];
    req.on('data', chunk => chunks.push(chunk));
    req.on('end', () => {
      const raw = Buffer.concat(chunks).toString('utf8').trim();
      if (!raw) {
        resolve({});
        return;
      }

      try {
        resolve(JSON.parse(raw));
      }
      catch {
        resolve({});
      }
    });
  });
}

function paginate(items, query) {
  const pageNum = Number(query.get('pageNum') || 1);
  const pageSize = Number(query.get('pageSize') || items.length || 10);
  const start = (pageNum - 1) * pageSize;
  return items.slice(start, start + pageSize);
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function randomDelay(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function createTextChunks(text) {
  return Array.from(text).map(content => ({
    delay: randomDelay(20, 70),
    payload: { choices: [{ delta: { content } }] },
  }));
}

const consultationDialogueDocument = consultationDialogueMessages
  .map(message => `${message.role === 'user' ? '用户' : '助手'}: ${message.content}`)
  .join('\n\n');

function createConsultationRule(input, reply, emotions = ['迷茫']) {
  return {
    input,
    analysis: {
      sentiment: 'negative',
      intensity: 5,
      emotions,
      confidence: 0.8,
      reasoning: '用户正在进行连续心理咨询模拟对话，需要以支持性提问和共情回应推进交流',
    },
    documents: [consultationDialogueDocument],
    reply,
  };
}

const consultationDialogueRules = consultationDialogueTurns.map(turn => createConsultationRule(
  turn.user,
  turn.assistant,
  turn.emotions,
));

const chatPresetRules = [
  {
    input: '1',
    analysis: {
      sentiment: 'neutral',
      intensity: 0,
      emotions: [],
      confidence: 0.8,
      reasoning: '无明确输入',
    },
    reply: '无法识别你的意思',
  },
  {
    input: '我不想活了',
    analysis: {
      sentiment: 'negative',
      intensity: 10,
      emotions: ['愤怒', '悲伤'],
      confidence: 0.8,
      reasoning: '用户表达自杀风险，需要优先进行安全干预',
    },
    reply: '如果你现在有伤害自己或他人的想法，并且觉得可能会付诸行动，请立即联系当地紧急救助电话、最近的急诊机构，或立刻联系你身边可信任的人陪伴你。你不需要一个人扛着。如果你愿意，也可以马上告诉我你当前是否处于紧急危险中。',
    filtered: true,
  },
  {
    input: '我很焦虑',
    analysis: {
      sentiment: 'negative',
      intensity: 10,
      emotions: ['迷茫', '悲伤'],
      confidence: 0.8,
      reasoning: '暂不清楚用户因何而感到悲伤，需要反问用户',
    },
    documents: [consultationDialogueDocument],
    reply: '您好，感谢您的信任，愿意在这里分享您的感受。请问您能详细描述一下，您为何焦虑吗？',
  },
  {
    input: '你好。我最近感觉心情很矛盾，有些迷茫，不知道怎么和朋友相处了。',
    analysis: {
      sentiment: 'neutral',
      intensity: 5,
      emotions: ['矛盾', '迷茫'],
      confidence: 0.8,
      reasoning: '暂不理解“矛盾”和“迷茫”具体指的是什么，进行对用户进行反问',
    },
    reply: '您好，感谢您的信任，愿意在这里分享您的感受。请问您能详细描述一下，您所谓的“矛盾”和“迷茫”具体指的是什么吗？',
  },
  ...consultationDialogueRules,
];

function createPresetChunks(rule) {
  const analysisText = `心理分析器：${JSON.stringify(rule.analysis)}\n相关文档：${JSON.stringify(rule.documents || [])}`;
  const chunks = [
    { delay: randomDelay(800, 1600), payload: { choices: [{ delta: { reasoning_content: analysisText } }] } },
    ...createTextChunks(rule.reply),
  ];

  if (rule.filtered) {
    chunks.push({
      delay: 0,
      payload: {
        choices: [{ delta: { content: rule.reply } }],
        filtered: true,
        filter_reason: 'self_harm_risk',
        replace: true,
      },
    });
  }

  chunks.push({ delay: 0, payload: { choices: [{ delta: { content: '' } }], finish_reason: 'stop' } });
  return chunks;
}

export async function streamChat(res, body) {
  const prompt = String(body?.messages?.at?.(-1)?.content || '这是一条 mock 回复。').trim();
  const presetRule = chatPresetRules.find(rule => rule.input === prompt);
  const chunks = presetRule
    ? createPresetChunks(presetRule)
    : [
        { delay: randomDelay(350, 900), payload: { choices: [{ delta: { reasoning_content: '读取用户输入，准备生成 mock 回复。' } }] } },
        { delay: randomDelay(350, 900), payload: { choices: [{ delta: { reasoning_content: '识别问题意图，提取关键上下文。' } }] } },
        { delay: randomDelay(350, 900), payload: { choices: [{ delta: { reasoning_content: '组织回答结构，准备流式输出。' } }] } },
        ...createTextChunks(`已收到：${prompt}。我会基于你的输入生成一段模拟回答，并按流式方式逐段返回。`),
        { delay: 0, payload: { choices: [{ delta: { content: '' } }], finish_reason: 'stop' } },
      ];

  res.writeHead(200, {
    'Content-Type': 'text/event-stream; charset=utf-8',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
  });

  for (const chunk of chunks) {
    if (chunk.delay > 0) {
      await delay(chunk.delay);
    }
    res.write(`data:${JSON.stringify({ code: 200, msg: 'success', data: null, ...chunk.payload })}\n\n`);
  }

  res.end();
}

export const mockRoutes = [
  {
    method: 'POST',
    path: '/auth/login',
    handler: ({ body }) => success({
      data: {
        access_token: 'mock-token',
        token: 'mock-token',
        userInfo: {
          userId: 1,
          username: body.username || 'mock-user',
          nickName: 'Mock 用户',
          avatar: 'https://avatars.githubusercontent.com/u/76239030?v=4',
          rolePermission: ['admin'],
          menuPermission: ['*:*:*'],
          token: 'mock-token',
        },
      },
    }),
  },
  {
    method: 'POST',
    path: '/resource/email/code',
    handler: () => success({ data: true }),
  },
  {
    method: 'POST',
    path: '/auth/register',
    handler: ({ body }) => success({ data: { username: body.username } }),
  },
  {
    method: 'POST',
    path: '/auth/logout',
    handler: () => success({ data: true }),
  },
  {
    method: 'GET',
    path: '/system/session/list',
    handler: ({ query, state }) => success({ rows: paginate([...state.sessions], query), total: state.sessions.length }),
  },
  {
    method: 'POST',
    path: '/system/session',
    handler: ({ body, state }) => {
      const session = {
        id: `session-${12 + state.nextSessionId++}`,
        sessionTitle: body.sessionTitle || '新对话',
        sessionContent: body.sessionContent || '',
        remark: body.remark || body.sessionTitle || '新对话',
        userId: body.userId || 1,
        createTime: now(),
      };
      state.sessions.unshift(session);
      return success({ data: { id: session.id, sessionId: session.id } });
    },
  },
  {
    method: 'PUT',
    path: '/system/session',
    handler: ({ body, state }) => {
      const index = state.sessions.findIndex(item => item.id === body.id);
      if (index >= 0)
        state.sessions[index] = { ...state.sessions[index], ...body };
      return success({ data: true });
    },
  },
  {
    method: 'GET',
    path: '/system/session/:id',
    handler: ({ params, state }) => success({ data: state.sessions.find(item => item.id === params.id) || null }),
  },
  {
    method: 'DELETE',
    path: '/system/session/:ids',
    handler: ({ params, state }) => {
      const ids = params.ids.split(',');
      state.sessions = state.sessions.filter(item => !ids.includes(item.id));
      state.messages = state.messages.filter(item => !ids.includes(String(item.sessionId)));
      return success({ data: true });
    },
  },
  {
    method: 'GET',
    path: '/system/message/list',
    handler: ({ query, state }) => {
      const sessionId = query.get('sessionId');
      const rows = state.messages.filter(item => !sessionId || String(item.sessionId) === String(sessionId));
      return success({ rows, total: rows.length });
    },
  },
  {
    method: 'POST',
    path: '/system/message',
    handler: ({ body, state }) => {
      const message = { id: state.nextMessageId++, userId: 1, totalTokens: 0, ...body };
      state.messages.push(message);
      return success({ data: message });
    },
  },
  {
    method: 'GET',
    path: '/system/model/modelList',
    handler: ({ state }) => success({ data: state.models }),
  },
  {
    method: 'POST',
    path: '/chat/send',
    stream: true,
    handler: ({ body, res }) => streamChat(res, body),
  },
];

export function createMockPlugin({ base = '/dev-api' } = {}) {
  const state = createMockState();

  return {
    name: 'local-mock-api',
    configureServer(server) {
      server.middlewares.use(base, async (req, res, next) => {
        const url = new URL(req.url || '/', 'http://mock.local');
        const matched = findMockRoute(req.method || 'GET', url.pathname);

        if (!matched) {
          next();
          return;
        }

        const body = await parseJsonBody(req);
        const result = await matched.route.handler({
          body,
          params: matched.params,
          query: url.searchParams,
          req,
          res,
          state,
        });

        if (matched.route.stream)
          return;

        res.writeHead(result.status, result.headers);
        res.end(JSON.stringify(result.body));
      });
    },
  };
}
