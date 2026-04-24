import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { fetchDocuments, uploadDocument, deleteDocument } from '@/lib/api'
import type { DocumentStatus } from '@/types'

const API = 'http://localhost:8000'

beforeEach(() => {
  vi.resetAllMocks()
})

afterEach(() => {
  vi.restoreAllMocks()
})

const mockDoc: DocumentStatus = {
  doc_id: 'doc-1',
  filename: 'test.pdf',
  status: 'ready',
  created_at: '2026-01-01T00:00:00Z',
  chunk_count: 10,
}

describe('fetchDocuments', () => {
  it('returns parsed document list on success', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([mockDoc]),
    })
    const result = await fetchDocuments()
    expect(result).toEqual([mockDoc])
    expect(fetch).toHaveBeenCalledWith(`${API}/documents`)
  })

  it('returns empty array when fetch throws', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'))
    const result = await fetchDocuments()
    expect(result).toEqual([])
  })

  it('returns empty array on non-ok response', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 500 })
    const result = await fetchDocuments()
    expect(result).toEqual([])
  })
})

describe('uploadDocument', () => {
  it('sends file as FormData and returns response', async () => {
    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ doc_id: 'doc-1', filename: 'test.pdf', status: 'processing' }),
    })
    const result = await uploadDocument(file)
    expect(result).toEqual({ doc_id: 'doc-1', filename: 'test.pdf', status: 'processing' })
    const call = (fetch as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(call[0]).toBe(`${API}/upload`)
    expect(call[1].method).toBe('POST')
    expect(call[1].body).toBeInstanceOf(FormData)
  })

  it('throws on upload failure', async () => {
    const file = new File(['x'], 'bad.exe')
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 415,
      text: () => Promise.resolve('Unsupported'),
    })
    await expect(uploadDocument(file)).rejects.toThrow('Upload failed: 415')
  })
})

describe('deleteDocument', () => {
  it('sends DELETE request to correct URL', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: true })
    await deleteDocument('doc-1')
    expect(fetch).toHaveBeenCalledWith(`${API}/documents/doc-1`, { method: 'DELETE' })
  })

  it('does not throw on failure (silent delete)', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 404 })
    await expect(deleteDocument('missing')).resolves.toBeUndefined()
  })
})
