import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import api from '@/lib/api'
import { Upload, Loader2, CheckCircle2, XCircle, FileText } from 'lucide-react'

export default function KnowledgeBase() {
  const [frameworks, setFrameworks] = useState([])
  const [selectedFramework, setSelectedFramework] = useState('')
  const [title, setTitle] = useState('')
  const [version, setVersion] = useState('')
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [success, setSuccess] = useState(null)
  const [error, setError] = useState(null)
  const [loadingFrameworks, setLoadingFrameworks] = useState(true)

  // Fetch frameworks on component mount
  useEffect(() => {
    const fetchFrameworks = async () => {
      try {
        const res = await api.get('/frameworks')
        setFrameworks(res.data || [])
      } catch (err) {
        console.error('Error fetching frameworks:', err)
        setError('Failed to load frameworks. Please refresh the page.')
      } finally {
        setLoadingFrameworks(false)
      }
    }
    fetchFrameworks()
  }, [])

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0]
    if (selectedFile) {
      // Validate file type
      const fileExt = selectedFile.name.split('.').pop().toLowerCase()
      if (!['pdf', 'docx'].includes(fileExt)) {
        setError('Only PDF and DOCX files are allowed.')
        setFile(null)
        return
      }
      setFile(selectedFile)
      setError(null)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)

    // Validation
    if (!file || !selectedFramework || !title.trim()) {
      setError('Please fill all required fields.')
      return
    }

    setUploading(true)

    try {
      // Create FormData
      const formData = new FormData()
      formData.append('file', file)
      formData.append('framework_id', selectedFramework)
      formData.append('title', title.trim())
      if (version.trim()) {
        formData.append('version', version.trim())
      }

      // Upload to API
      const res = await api.post('/knowledge-base/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      // Success
      setSuccess({
        message: res.data.message || 'Knowledge Base document uploaded and indexed successfully',
        documentId: res.data.document_id,
        chunksIndexed: res.data.chunks_indexed,
      })

      // Reset form
      setSelectedFramework('')
      setTitle('')
      setVersion('')
      setFile(null)
      // Reset file input
      const fileInput = document.getElementById('file-input')
      if (fileInput) {
        fileInput.value = ''
      }
    } catch (err) {
      console.error('Knowledge Base upload failed:', err)
      const errorMessage =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        'Upload failed. Please check backend logs.'
      setError(errorMessage)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Knowledge Base Upload</h1>
        <p className="text-muted-foreground">
          Upload authoritative compliance documents (e.g., ISO 27001 PDFs) to be used as ground truth in gap analysis.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Upload Knowledge Base Document
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Framework Selection */}
            <div>
              <label htmlFor="framework" className="block text-sm font-medium mb-2">
                Framework <span className="text-red-500">*</span>
              </label>
              {loadingFrameworks ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Loading frameworks...
                </div>
              ) : (
                <select
                  id="framework"
                  value={selectedFramework}
                  onChange={(e) => setSelectedFramework(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                  required
                >
                  <option value="">Select a framework</option>
                  {frameworks.map((fw) => (
                    <option key={fw.id} value={fw.id}>
                      {fw.name}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Document Title */}
            <div>
              <label htmlFor="title" className="block text-sm font-medium mb-2">
                Document Title <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="e.g., ISO 27001:2022 Standard"
                required
              />
            </div>

            {/* Version (Optional) */}
            <div>
              <label htmlFor="version" className="block text-sm font-medium mb-2">
                Version <span className="text-gray-500 text-xs">(Optional)</span>
              </label>
              <input
                type="text"
                id="version"
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="e.g., 2022, v1.0"
              />
            </div>

            {/* File Upload */}
            <div>
              <label htmlFor="file-input" className="block text-sm font-medium mb-2">
                Document File <span className="text-red-500">*</span>
              </label>
              <div className="flex items-center gap-4">
                <input
                  type="file"
                  id="file-input"
                  accept=".pdf,.docx"
                  onChange={handleFileChange}
                  className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-white hover:file:bg-primary/90"
                  required
                />
              </div>
              {file && (
                <p className="mt-2 text-sm text-muted-foreground">
                  Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
                </p>
              )}
              <p className="mt-1 text-xs text-muted-foreground">
                Supported formats: PDF, DOCX
              </p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
                <XCircle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium text-red-800">Error</p>
                  <p className="text-sm text-red-600 mt-1">{error}</p>
                </div>
              </div>
            )}

            {/* Success Message */}
            {success && (
              <div className="flex items-start gap-3 p-4 bg-green-50 border border-green-200 rounded-lg">
                <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium text-green-800">Success</p>
                  <p className="text-sm text-green-600 mt-1">{success.message}</p>
                  {success.chunksIndexed !== undefined && (
                    <p className="text-xs text-green-600 mt-1">
                      Document ID: {success.documentId} | Chunks indexed: {success.chunksIndexed}
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Submit Button */}
            <Button
              type="submit"
              disabled={uploading || loadingFrameworks}
              className="w-full sm:w-auto"
              size="lg"
            >
              {uploading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Uploading and Indexing...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Upload Knowledge Base Document
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Information Card */}
      <Card>
        <CardHeader>
          <CardTitle>About Knowledge Base</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm text-muted-foreground">
            <p>
              Knowledge Base documents are authoritative compliance standards (e.g., ISO 27001, NIST) that serve as
              ground truth for gap analysis.
            </p>
            <p>
              When you upload a document, it will be:
            </p>
            <ul className="list-disc list-inside space-y-1 ml-4">
              <li>Stored securely in the system</li>
              <li>Extracted and chunked into searchable segments</li>
              <li>Indexed in Pinecone for semantic search</li>
              <li>Used as reference during gap analysis</li>
            </ul>
            <p className="mt-4 text-xs">
              <strong>Note:</strong> Only SUPER_ADMIN and COMPLIANCE_ADMIN users can upload knowledge base documents.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

