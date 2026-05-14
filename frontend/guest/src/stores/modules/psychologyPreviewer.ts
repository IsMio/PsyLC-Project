import { defineStore } from 'pinia';

export interface PsychologyAnalysis {
  sentiment: string;
  intensity: number;
  emotions: string[];
  confidence: number;
  reasoning: string;
}

export interface PsychologyPreviewData {
  analysis: PsychologyAnalysis | null;
  documents: unknown[];
}

const DEFAULT_PREVIEW_DATA: PsychologyPreviewData = {
  analysis: null,
  documents: [],
};

export function parsePsychologyPreview(content: string): PsychologyPreviewData | null {
  const analysisMatch = content.match(/心理分析器：([\s\S]*?)\n相关文档：/u);
  const documentsMatch = content.match(/相关文档：([\s\S]*)$/u);
  if (!analysisMatch || !documentsMatch) {
    return null;
  }

  try {
    const analysis = JSON.parse(analysisMatch[1].trim()) as PsychologyAnalysis;
    const documents = JSON.parse(documentsMatch[1].trim()) as unknown[];
    return { analysis, documents };
  }
  catch {
    return null;
  }
}

export const usePsychologyPreviewerStore = defineStore('psychologyPreviewer', () => {
  const previewData = ref<PsychologyPreviewData>({ ...DEFAULT_PREVIEW_DATA });

  const analysisText = computed(() => {
    if (!previewData.value.analysis) {
      return '{}';
    }
    return JSON.stringify(previewData.value.analysis, null, 2);
  });

  const documentsText = computed(() => JSON.stringify(previewData.value.documents, null, 2));

  function setPreviewData(data: PsychologyPreviewData) {
    previewData.value = data;
  }

  function clearPreviewData() {
    previewData.value = { ...DEFAULT_PREVIEW_DATA };
  }

  return {
    previewData,
    analysisText,
    documentsText,
    setPreviewData,
    clearPreviewData,
  };
});
