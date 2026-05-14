<!-- 每个回话对应的聊天内容 -->
<script setup lang="ts">
import type { AnyObject } from 'typescript-api-pro';
import type { CSSProperties } from 'vue';
import type { BubbleProps } from 'vue-element-plus-x/types/Bubble';
import type { BubbleListInstance } from 'vue-element-plus-x/types/BubbleList';
import type { FilesCardProps } from 'vue-element-plus-x/types/FilesCard';
import type { ThinkingStatus } from 'vue-element-plus-x/types/Thinking';
import { useHookFetch } from 'hook-fetch/vue';
import { Sender } from 'vue-element-plus-x';
import { useRoute, useRouter } from 'vue-router';
import { send } from '@/api';
import { create_session } from '@/api/session';
import FilesSelect from '@/components/FilesSelect/index.vue';
import ModelSelect from '@/components/ModelSelect/index.vue';
import Popover from '@/components/Popover/index.vue';
import PsychologyPreviewer from '@/components/PsychologyPreviewer/index.vue';
import { useChatStore } from '@/stores/modules/chat';
import { useFilesStore } from '@/stores/modules/files';
import { useModelStore } from '@/stores/modules/model';
import { parsePsychologyPreview, usePsychologyPreviewerStore } from '@/stores/modules/psychologyPreviewer';
import { useSessionStore } from '@/stores/modules/session';
import { useUserStore } from '@/stores/modules/user';

type MessageItem = BubbleProps & {
  key: number;
  role: 'ai' | 'user' | 'system' | 'assistant';
  avatar: string;
  filtered?: boolean;
  filter_reason?: string | null;
  thinkingStatus?: ThinkingStatus;
  thinlCollapse?: boolean;
  reasoning_content?: string;
};

const route = useRoute();
const router = useRouter();
const chatStore = useChatStore();
const modelStore = useModelStore();
const filesStore = useFilesStore();
const userStore = useUserStore();
const sessionStore = useSessionStore();
const previewerStore = usePsychologyPreviewerStore();

// 用户头像
const avatar = computed(() => {
  const userInfo = userStore.userInfo;
  return userInfo?.avatar || 'https://avatars.githubusercontent.com/u/76239030?v=4';
});

const inputValue = ref('');
const senderRef = ref<InstanceType<typeof Sender> | null>(null);
const bubbleItems = ref<MessageItem[]>([]);
const bubbleListRef = ref<BubbleListInstance | null>(null);
const isPreviewerVisible = ref(false);
const previewerPopoverStyle = ref<CSSProperties>({
  width: 'min(360px, calc(100vw - 32px))',
});

function updatePreviewerPopoverStyle() {
  const senderElement = document.querySelector<HTMLElement>('.chat-defaul-sender');
  if (!senderElement)
    return;

  const senderRect = senderElement.getBoundingClientRect();
  previewerPopoverStyle.value = {
    width: 'min(360px, calc(100vw - 32px))',
    left: `${senderRect.left + window.scrollX}px`,
  };
}

function handlePreviewerShow() {
  updatePreviewerPopoverStyle();
  isPreviewerVisible.value = true;
}

function syncSenderHeader() {
  nextTick(() => {
    if (filesStore.filesList.length > 0) {
      senderRef.value?.openHeader();
    }
    else {
      senderRef.value?.closeHeader();
    }
  });
}

const { stream, loading: isLoading, cancel } = useHookFetch({
  request: send,
  onError: (err) => {
    console.warn('测试错误拦截', err);
  },
});
// 记录进入思考中
let isThinking = false;

watch(
  () => route.params?.id,
  async (_id_) => {
    if (_id_) {
      if (_id_ !== 'not_login') {
        // 判断的当前会话id是否有聊天记录，有缓存则直接赋值展示
        if (chatStore.chatMap[`${_id_}`] && chatStore.chatMap[`${_id_}`].length) {
          bubbleItems.value = chatStore.chatMap[`${_id_}`] as MessageItem[];
          // 滚动到底部
          setTimeout(() => {
            bubbleListRef.value!.scrollToBottom();
          }, 350);
          return;
        }

        // 无缓存则请求聊天记录
        await chatStore.requestChatList(`${_id_}`);
        // 请求聊天记录后，赋值回显，并滚动到底部
        bubbleItems.value = chatStore.chatMap[`${_id_}`] as MessageItem[];

        // 滚动到底部
        setTimeout(() => {
          bubbleListRef.value!.scrollToBottom();
        }, 350);
      }

      // 如果本地有发送内容 ，则直接发送
      const v = localStorage.getItem('chatContent');
      if (v) {
        // 发送消息
        console.log('发送消息 v', v);
        setTimeout(() => {
          startSSE(v);
        }, 350);

        localStorage.removeItem('chatContent');
      }
    }
  },
  { immediate: true, deep: true },
);

// 封装数据处理逻辑
function handleDataChunk(chunk: AnyObject) {
  try {
    const currentMessage = bubbleItems.value[bubbleItems.value.length - 1];
    if (!currentMessage) {
      return;
    }

    const reasoningChunk = chunk.choices?.[0].delta.reasoning_content;
    if (reasoningChunk) {
      currentMessage.loading = true;
      if (bubbleItems.value.length) {
        const reasoningContent = `${currentMessage.reasoning_content || ''}${reasoningChunk}`;
        currentMessage.reasoning_content = reasoningContent;
        const previewData = parsePsychologyPreview(reasoningContent);
        if (previewData) {
          previewerStore.setPreviewData(previewData);
        }
      }
    }

    // 另一种思考中形式，content中有 <think></think> 的格式
    // 一开始匹配到 <think> 开始，匹配到 </think> 结束，并处理标签中的内容为思考内容
    const parsedChunk = chunk.choices?.[0].delta.content;
    if (parsedChunk) {
      const thinkStart = parsedChunk.includes('<think>');
      const thinkEnd = parsedChunk.includes('</think>');
      if (thinkStart) {
        isThinking = true;
      }
      if (thinkEnd) {
        isThinking = false;
      }
      if (isThinking) {
        currentMessage.loading = true;
        if (bubbleItems.value.length) {
          currentMessage.reasoning_content += parsedChunk
            .replace('<think>', '')
            .replace('</think>', '');
        }
      }
      else {
        // 结束 思考链状态
        currentMessage.thinkingStatus = 'end';
        currentMessage.loading = false;
        if (bubbleItems.value.length) {
          currentMessage.content += parsedChunk;
        }
      }
    }

    if (chunk.filtered) {
      currentMessage.filtered = true;
      currentMessage.filter_reason = String(chunk.filter_reason || 'output_filter');
      if (chunk.replace) {
        currentMessage.content = String(parsedChunk || '');
      }
      currentMessage.content = chatStore.normalizeFilteredContent(currentMessage.content || '');
    }
  }
  catch (err) {
    // 这里如果使用了中断，会有报错，可以忽略不管
    console.error('解析数据时出错:', err);
  }
}

// 封装错误处理逻辑
function handleError(err: any) {
  console.error('Fetch error:', err);
}

function parseSessionId(payload: unknown): string {
  if (payload == null) {
    return '';
  }
  if (typeof payload === 'string' || typeof payload === 'number') {
    return String(payload).trim();
  }
  if (typeof payload === 'object') {
    const candidate = (payload as Record<string, unknown>).id ?? (payload as Record<string, unknown>).sessionId;
    if (typeof candidate === 'string' || typeof candidate === 'number') {
      return String(candidate).trim();
    }
  }
  return '';
}

async function ensureSessionId(chatContent: string) {
  const currentId = String(route.params?.id ?? '').trim();
  const hasValidSessionId = currentId !== '' && currentId !== 'not_login' && currentId !== 'undefined' && currentId !== 'null';
  if (hasValidSessionId) {
    return currentId;
  }
  if (!userStore.userInfo?.userId) {
    return undefined;
  }

  try {
    const trimmed = chatContent.trim();
    const title = trimmed ? trimmed.slice(0, 10) : '新对话';
    const res = await create_session({
      userId: userStore.userInfo.userId,
      sessionTitle: title,
      sessionContent: chatContent,
      remark: title,
    });
    const newId = parseSessionId(res.data);
    if (!newId) {
      throw new Error('create_session 返回的 sessionId 无效');
    }
    router.replace({ name: 'chatWithId', params: { id: newId } });
    await sessionStore.requestSessionList(1, true);
    return newId;
  }
  catch (error) {
    console.error('ensureSessionId error:', error);
    return undefined;
  }
}

async function startSSE(chatContent: string) {
  try {
    const sessionId = await ensureSessionId(chatContent);
    if (!sessionId) {
      throw new Error('无法获取会话 ID');
    }
    // 添加用户输入的消息
    // console.log('chatContent', chatContent);
    // 清空输入框
    inputValue.value = '';
    addMessage(chatContent, true);
    addMessage('', false);

    // 这里有必要调用一下 BubbleList 组件的滚动到底部 手动触发 自动滚动
    bubbleListRef.value?.scrollToBottom();

    for await (const chunk of stream({
      messages: [
        {
          role: 'user',
          content: chatContent,
        },
      ],
      sessionId,
      userId: userStore.userInfo?.userId,
      model: modelStore.currentModelInfo.modelName ?? '',
    })) {
      handleDataChunk(chunk.result as AnyObject);
    }
  }
  catch (err) {
    handleError(err);
  }
  finally {
    console.log('数据接收完毕');
    // 停止打字器状态
    if (bubbleItems.value.length) {
      bubbleItems.value[bubbleItems.value.length - 1].typing = false;
    }
  }
}

// 中断请求
async function cancelSSE() {
  cancel();
  // 结束最后一条消息打字状态
  if (bubbleItems.value.length) {
    bubbleItems.value[bubbleItems.value.length - 1].typing = false;
  }
}

// 添加消息 - 维护聊天记录
function addMessage(message: string, isUser: boolean) {
  const i = bubbleItems.value.length;
  const obj: MessageItem = {
    key: i,
    avatar: isUser
      ? avatar.value
      : 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png',
    avatarSize: '32px',
    role: isUser ? 'user' : 'assistant',
    placement: isUser ? 'end' : 'start',
    isMarkdown: !isUser,
    loading: !isUser,
    content: message || '',
    filtered: false,
    filter_reason: null,
    reasoning_content: '',
    thinkingStatus: 'start',
    thinlCollapse: false,
    noStyle: !isUser,
  };
  bubbleItems.value.push(obj);
}

function handleDeleteCard(_item: FilesCardProps, index: number) {
  filesStore.deleteFileByIndex(index);
}

watch(
  () => filesStore.filesList.length,
  syncSenderHeader,
);
</script>

<template>
  <div class="chat-with-id-container">
    <div class="chat-warp">
      <BubbleList ref="bubbleListRef" :list="bubbleItems" max-height="calc(100vh - 240px)">
        <template #content="{ item }">
          <!-- chat 内容走 markdown -->
          <div class="el-bubble-content el-bubble-content-filled">
            <div v-if="item.filtered" class="filtered-tip">
              回答已按安全规范调整
            </div>
            <XMarkdown v-if="item.content && (item.role === 'system' || item.role === 'assistant')" :markdown="item.content" class="markdown-body" :themes="{ light: 'github-light', dark: 'github-dark' }" default-theme-mode="dark" />
          </div>
          <!-- user 内容 纯文本 -->
          <div v-if="item.content && item.role === 'user'" class="user-content">
            {{ item.content }}
          </div>
        </template>
      </BubbleList>

      <Sender
        ref="senderRef" v-model="inputValue" class="chat-defaul-sender" :auto-size="{
          maxRows: 6,
          minRows: 2,
        }" variant="updown" clearable allow-speech :loading="isLoading" @submit="startSSE" @cancel="cancelSSE"
      >
        <template #header>
          <div class="sender-header p-12px pt-6px pb-0px">
            <Attachments :items="filesStore.filesList" :hide-upload="true" @delete-card="handleDeleteCard">
              <template #prev-button="{ show, onScrollLeft }">
                <div
                  v-if="show"
                  class="prev-next-btn left-8px flex-center w-22px h-22px rounded-8px border-1px border-solid border-[rgba(0,0,0,0.08)] c-[rgba(0,0,0,.4)] hover:bg-#f3f4f6 bg-#fff font-size-10px"
                  @click="onScrollLeft"
                >
                  <el-icon>
                    <ArrowLeftBold />
                  </el-icon>
                </div>
              </template>

              <template #next-button="{ show, onScrollRight }">
                <div
                  v-if="show"
                  class="prev-next-btn right-8px flex-center w-22px h-22px rounded-8px border-1px border-solid border-[rgba(0,0,0,0.08)] c-[rgba(0,0,0,.4)] hover:bg-#f3f4f6 bg-#fff font-size-10px"
                  @click="onScrollRight"
                >
                  <el-icon>
                    <ArrowRightBold />
                  </el-icon>
                </div>
              </template>
            </Attachments>
          </div>
        </template>
        <template #prefix>
          <div class="flex-1 flex items-center gap-8px flex-none w-fit overflow-hidden">
            <FilesSelect />
            <ModelSelect />
            <Popover
              trigger="click"
              placement="top-start"
              :offset="[10, 0]"
              popover-class="previewer-popover"
              :popover-style="previewerPopoverStyle"
              @show="handlePreviewerShow"
              @hide="isPreviewerVisible = false"
            >
              <template #trigger>
                <button
                  type="button"
                  class="previewer-toggle"
                  :class="{ 'is-active': isPreviewerVisible }"
                >
                  预览器
                </button>
              </template>
              <PsychologyPreviewer />
            </Popover>
          </div>
        </template>
      </Sender>
    </div>
  </div>
</template>

<style scoped lang="scss">
.chat-with-id-container {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 800px;
  height: 100%;
  .chat-warp {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    width: 100%;
    height: calc(100vh - 60px);
    .thinking-chain-warp {
      margin-bottom: 12px;
    }
  }
  :deep() {
    .el-bubble-list {
      padding-top: 24px;
    }
    .el-bubble {
      padding: 0 12px;
      padding-bottom: 24px;
    }
    .el-typewriter {
      overflow: hidden;
      border-radius: 12px;
    }
    .user-content {
      // 换行
      white-space: pre-wrap;
    }
    .markdown-body {
      color: var(--chat-text-color);
      background-color: var(--el-fill-color);
      border-radius: calc(var(--el-border-radius-base) + 4px);
    }
    .filtered-tip {
      margin-bottom: 6px;
      font-size: 12px;
      color: var(--el-color-warning);
    }
    .markdown-elxLanguage-header-div {
      top: -25px !important;
    }

    // xmarkdown 样式
    .elx-xmarkdown-container {
      padding: 8px 4px;
    }
  }
  .chat-defaul-sender {
    width: 100%;
    margin-bottom: 22px;
  }
}

.previewer-toggle {
  height: 34px;
  padding: 0 12px;
  font-size: 12px;
  color: var(--el-text-color-regular);
  cursor: pointer;
  background: var(--el-bg-color);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 15px;

  &:hover,
  &.is-active {
    color: var(--el-color-primary);
    border-color: var(--el-color-primary);
  }
}
</style>
