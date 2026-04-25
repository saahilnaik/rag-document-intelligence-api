import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { useAppStore } from '@/lib/store'

beforeEach(() => {
  useAppStore.setState({
    messages: [],
    sessionId: 'test-session',
    isStreaming: false,
    documents: [],
    selectedDocId: null,
    isPolling: false,
    theme: 'dark',
  })
  document.documentElement.className = ''
})

describe('ThemeProvider', () => {
  it('adds dark class to html element when theme is dark', async () => {
    const { ThemeProvider } = await import('@/components/ThemeProvider')
    render(<ThemeProvider><div /></ThemeProvider>)
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('removes dark class when theme is light', async () => {
    useAppStore.setState({ theme: 'light' })
    const { ThemeProvider } = await import('@/components/ThemeProvider')
    render(<ThemeProvider><div /></ThemeProvider>)
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })
})

describe('ThemeToggle', () => {
  it('renders a button', async () => {
    const { ThemeToggle } = await import('@/components/ThemeToggle')
    render(<ThemeToggle />)
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('calls toggleTheme when clicked', async () => {
    const { ThemeToggle } = await import('@/components/ThemeToggle')
    render(<ThemeToggle />)
    fireEvent.click(screen.getByRole('button'))
    expect(useAppStore.getState().theme).toBe('light')
  })
})

describe('DocumentCard', () => {
  const onDelete = vi.fn()

  it('renders filename', async () => {
    const { DocumentCard } = await import('@/components/DocumentCard')
    render(
      <DocumentCard
        doc={{ doc_id: 'd1', filename: 'report.pdf', status: 'ready', created_at: '', chunk_count: 5 }}
        onDelete={onDelete}
      />
    )
    expect(screen.getByText(/report\.pdf/)).toBeInTheDocument()
  })

  it('shows chunk count when ready', async () => {
    const { DocumentCard } = await import('@/components/DocumentCard')
    render(
      <DocumentCard
        doc={{ doc_id: 'd1', filename: 'doc.pdf', status: 'ready', created_at: '', chunk_count: 12 }}
        onDelete={onDelete}
      />
    )
    expect(screen.getByText(/12 chunks/)).toBeInTheDocument()
  })

  it('calls onDelete when delete button clicked', async () => {
    const { DocumentCard } = await import('@/components/DocumentCard')
    render(
      <DocumentCard
        doc={{ doc_id: 'd1', filename: 'doc.pdf', status: 'ready', created_at: '' }}
        onDelete={onDelete}
      />
    )
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    expect(onDelete).toHaveBeenCalledWith('d1')
  })

  it('shows processing indicator for processing status', async () => {
    const { DocumentCard } = await import('@/components/DocumentCard')
    render(
      <DocumentCard
        doc={{ doc_id: 'd1', filename: 'doc.pdf', status: 'processing', created_at: '' }}
        onDelete={onDelete}
      />
    )
    expect(screen.getByText(/processing/i)).toBeInTheDocument()
  })
})

describe('SourcesExpander', () => {
  const sources: import('@/types').SourceChunk[] = [
    { doc_id: 'd1', filename: 'report.pdf', page_number: 3, text: 'some text here', score: 0.92 },
    { doc_id: 'd2', filename: 'notes.txt', text: 'other text', score: 0.85 },
  ]

  it('renders a toggle button with source count', async () => {
    const { SourcesExpander } = await import('@/components/SourcesExpander')
    render(<SourcesExpander sources={sources} />)
    expect(screen.getByText(/2 sources/i)).toBeInTheDocument()
  })

  it('hides source details by default', async () => {
    const { SourcesExpander } = await import('@/components/SourcesExpander')
    render(<SourcesExpander sources={sources} />)
    expect(screen.queryByText('some text here')).not.toBeInTheDocument()
  })

  it('shows source details after clicking toggle', async () => {
    const { SourcesExpander } = await import('@/components/SourcesExpander')
    render(<SourcesExpander sources={sources} />)
    fireEvent.click(screen.getByText(/2 sources/i))
    expect(screen.getByText('some text here')).toBeInTheDocument()
    expect(screen.getByText(/report\.pdf/)).toBeInTheDocument()
  })

  it('shows singular label for one source', async () => {
    const { SourcesExpander } = await import('@/components/SourcesExpander')
    render(<SourcesExpander sources={[sources[0]]} />)
    expect(screen.getByText(/1 source/i)).toBeInTheDocument()
    expect(screen.queryByText(/1 sources/i)).not.toBeInTheDocument()
  })
})
