import type { DocumentStatus, SourceChunk, UploadResponse } from '@/types'

const API_URL =
  (typeof process !== 'undefined' && process.env.NEXT_PUBLIC_API_URL) ||
  'http://localhost:8000'

export async function fetchDocuments(): Promise<DocumentStatus[]> {
  try {
    const res = await fetch(`${API_URL}/documents`)
    if (!res.ok) return []
    return res.json()
  } catch {
    return []
  }
}

export async function uploadDocument(file: File): Promise<UploadResponse> {
  const body = new FormData()
  body.append('file', file)
  const res = await fetch(`${API_URL}/upload`, { method: 'POST', body })
  if (!res.ok) {
    throw new Error(`Upload failed: ${res.status}`)
  }
  return res.json()
}

export async function deleteDocument(docId: string): Promise<void> {
  try {
    await fetch(`${API_URL}/documents/${docId}`, { method: 'DELETE' })
  } catch {
    // silent — best-effort delete
  }
}

export interface StreamPayload {
  question: string
  session_id: string
  doc_id?: string
}

export async function streamAnswer(
  payload: StreamPayload,
  onToken: (token: string) => void,
  onSources: (sources: SourceChunk[]) => void,
  onDone: () => void,
  onError: (error: string) => void
): Promise<void> {
  // Implemented in Task 7
  void payload; void onToken; void onSources; void onDone; void onError
}
