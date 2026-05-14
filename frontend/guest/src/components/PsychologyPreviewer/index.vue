<script setup lang="ts">
import { usePsychologyPreviewerStore } from '@/stores/modules/psychologyPreviewer';

const previewerStore = usePsychologyPreviewerStore();
</script>

<template>
  <section class="psychology-previewer" aria-label="心理预览器">
    <div class="previewer-shell">
      <article class="previewer-card">
        <h3>
          <span class="title-accent" />
          心理分析器
        </h3>
        <pre class="analysis-code">{{ previewerStore.analysisText }}</pre>
      </article>

      <article class="previewer-card doc-card">
        <h3>
          <span class="title-accent" />
          相关文档
        </h3>
        <div class="previewer-doc-body">
          <pre class="documents-code">{{ previewerStore.documentsText }}</pre>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped lang="scss">
.psychology-previewer {
  width: min(100%, 360px);
  padding: 0 0 8px;
}

.previewer-shell {
  display: grid;
  gap: 12px;
  padding: 10px;
  background:
    radial-gradient(circle at top left, rgba(90, 141, 238, 0.12), transparent 34%),
    linear-gradient(180deg, #f8fbff 0%, #f4f7fb 100%);
  border: 1px solid #e7eef8;
  border-radius: 16px;
}

.previewer-card {
  position: relative;
  padding: 14px;
  color: #5f6f86;
  background: #fff;
  border: 1px solid rgba(220, 229, 241, 0.92);
  border-radius: 14px;
  box-shadow: 0 8px 24px rgba(31, 45, 61, 0.06);

  h3 {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0 0 12px;
    font-size: 15px;
    font-weight: 700;
    line-height: 1.35;
    color: #2f3e52;
  }
}

.title-accent {
  width: 4px;
  height: 15px;
  background: linear-gradient(180deg, #5b8def 0%, #7bd3ff 100%);
  border-radius: 999px;
}

.analysis-code {
  margin: 0;
  padding: 12px;
  overflow: hidden;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
  font-size: 14px;
  line-height: 1.78;
  color: #465872;
  white-space: pre-wrap;
  background: linear-gradient(180deg, #f6f9ff 0%, #f1f6fd 100%);
  border: 1px solid #e8f0fb;
  border-radius: 11px;
}

.doc-card {
  padding-bottom: 10px;
}

.previewer-doc-body {
  max-height: 206px;
  padding: 2px 12px 2px 0;
  overflow-y: auto;
  font-size: 15px;
  font-weight: 500;
  line-height: 1.78;
  color: #667b96;
  scrollbar-width: thin;
  scrollbar-color: #a2abb8 transparent;

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }

  &::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #b8c1cf 0%, #8f98a6 100%);
    border-radius: 999px;
  }
}

.documents-code {
  margin: 0;
  font: inherit;
  color: inherit;
  white-space: pre-wrap;
}

@media (max-width: 520px) {
  .psychology-previewer {
    width: 100%;
  }

  .previewer-shell {
    padding: 8px;
    border-radius: 14px;
  }
}
</style>
