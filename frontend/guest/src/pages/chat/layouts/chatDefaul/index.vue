<!-- 默认消息列表页 -->
<script setup lang="ts">
import type { CSSProperties } from 'vue';
import type { FilesCardProps } from 'vue-element-plus-x/types/FilesCard';
import FilesSelect from '@/components/FilesSelect/index.vue';
import ModelSelect from '@/components/ModelSelect/index.vue';
import Popover from '@/components/Popover/index.vue';
import PsychologyPreviewer from '@/components/PsychologyPreviewer/index.vue';
import WelecomeText from '@/components/WelecomeText/index.vue';
import { useUserStore } from '@/stores';
import { useFilesStore } from '@/stores/modules/files';
import { useSessionStore } from '@/stores/modules/session';

const userStore = useUserStore();
const sessionStore = useSessionStore();
const filesStore = useFilesStore();

const senderValue = ref('');
const senderRef = ref();
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

async function handleSend() {
  localStorage.setItem('chatContent', senderValue.value);
  await sessionStore.createSessionList({
    userId: userStore.userInfo?.userId as number,
    sessionContent: senderValue.value,
    sessionTitle: senderValue.value.slice(0, 10),
    remark: senderValue.value.slice(0, 10),
  });
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
  <div class="chat-defaul-wrap">
    <WelecomeText />
    <Sender
      ref="senderRef"
      v-model="senderValue"
      class="chat-defaul-sender"
      :auto-size="{
        maxRows: 9,
        minRows: 3,
      }"
      variant="updown"
      clearable
      allow-speech
      @submit="handleSend"
    >
      <template #header>
        <div class="sender-header p-12px pt-6px pb-0px">
          <Attachments
            :items="filesStore.filesList"
            :hide-upload="true"
            @delete-card="handleDeleteCard"
          >
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
</template>

<style scoped lang="scss">
.chat-defaul-wrap {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 800px;
  min-height: 450px;
  .chat-defaul-sender {
    width: 100%;
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
