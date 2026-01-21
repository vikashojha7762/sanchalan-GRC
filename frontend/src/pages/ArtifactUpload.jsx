import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import api from '@/lib/api'
import { Upload, FileText, Eye, Download, X, Clock, CheckCircle } from 'lucide-react'

export default function ArtifactUpload() {
  const [file, setFile] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    artifact_type: 'document',
    policy_id: '',
    gap_id: '',
    control_id: ''
  })
  const [uploading, setUploading] = useState(false)
  const [uploadedArtifacts, setUploadedArtifacts] = useState([])
  const [loadingArtifacts, setLoadingArtifacts] = useState(false)
  const [showUploaded, setShowUploaded] = useState(false)

  // Fetch uploaded artifacts
  const fetchArtifacts = async () => {
    setLoadingArtifacts(true)
    try {
      const response = await api.get('/artifacts', {
        params: {
          gap_id: formData.gap_id || undefined,
          policy_id: formData.policy_id || undefined,
          control_id: formData.control_id || undefined
        }
      })
      setUploadedArtifacts(response.data || [])
    } catch (err) {
      console.error('Error fetching artifacts:', err)
      setUploadedArtifacts([])
    } finally {
      setLoadingArtifacts(false)
    }
  }

  // Load artifacts on mount and when filters change
  useEffect(() => {
    if (showUploaded) {
      fetchArtifacts()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showUploaded, formData.gap_id, formData.policy_id, formData.control_id])

  const handleFileChange = (e) => {
    setFile(e.target.files[0])
    if (e.target.files[0]) {
      setFormData({ ...formData, name: e.target.files[0].name })
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file) {
      alert('Please select a file')
      return
    }

    setUploading(true)
    try {
      const uploadData = new FormData()
      uploadData.append('file', file)
      uploadData.append('name', formData.name)
      if (formData.description) {
        uploadData.append('description', formData.description)
      }
      uploadData.append('artifact_type', formData.artifact_type)
      if (formData.policy_id) {
        uploadData.append('policy_id', formData.policy_id)
      }
      if (formData.gap_id) {
        uploadData.append('gap_id', formData.gap_id)
      }
      if (formData.control_id) {
        uploadData.append('control_id', formData.control_id)
      }

      await api.post('/artifacts/upload', uploadData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      
      alert('Artifact uploaded successfully!')
      
      // Reset form
      setFile(null)
      setFormData({
        name: '',
        description: '',
        artifact_type: 'document',
        policy_id: '',
        gap_id: '',
        control_id: ''
      })
      
      // Refresh uploaded artifacts list if it's visible
      if (showUploaded) {
        fetchArtifacts()
      } else {
        // Show uploaded artifacts section after successful upload
        setShowUploaded(true)
        fetchArtifacts()
      }
    } catch (err) {
      alert(err.response?.data?.detail || 'Error uploading artifact')
    } finally {
      setUploading(false)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  const formatFileSize = (bytes) => {
    if (!bytes) return 'N/A'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const handleDownload = async (artifact) => {
    try {
      if (artifact.id) {
        // Use the download endpoint for authenticated access
        const response = await api.get(`/artifacts/${artifact.id}/download`, {
          responseType: 'blob'
        })
        
        // Create blob URL and trigger download
        const blob = new Blob([response.data])
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = artifact.name || 'download'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
      } else if (artifact.file_path) {
        // Fallback to direct URL
        const fileUrl = `http://localhost:8000/${artifact.file_path}`
        window.open(fileUrl, '_blank')
      } else if (artifact.file_url) {
        window.open(artifact.file_url, '_blank')
      } else {
        alert('File not available for download')
      }
    } catch (err) {
      console.error('Download error:', err)
      // Fallback to direct URL if download endpoint fails
      if (artifact.file_path) {
        const fileUrl = `http://localhost:8000/${artifact.file_path}`
        window.open(fileUrl, '_blank')
      } else {
        alert('Error downloading file. Please try again.')
      }
    }
  }

  const handleView = (artifact) => {
    // Open in new tab or navigate to view page
    if (artifact.id) {
      // Use the download endpoint for viewing (browser will handle PDF/images)
      const fileUrl = `http://localhost:8000/api/v1/artifacts/${artifact.id}/download`
      window.open(fileUrl, '_blank')
    } else if (artifact.file_path) {
      // Fallback to direct static file URL
      const fileUrl = `http://localhost:8000/${artifact.file_path}`
      window.open(fileUrl, '_blank')
    } else if (artifact.file_url) {
      window.open(artifact.file_url, '_blank')
    } else {
      alert('File not available for viewing')
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Artifact Upload</h1>
        <p className="text-muted-foreground">Upload documents and evidence for policies, controls, and gaps</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload Form */}
        <Card>
          <CardHeader>
            <CardTitle>Upload Artifact</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">File</label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                  <input
                    type="file"
                    onChange={handleFileChange}
                    className="hidden"
                    id="file-upload"
                  />
                  <label htmlFor="file-upload" className="cursor-pointer">
                    {file ? (
                      <div className="flex items-center justify-center gap-2">
                        <FileText className="h-8 w-8 text-primary" />
                        <span>{file.name}</span>
                      </div>
                    ) : (
                      <div>
                        <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                        <p className="text-sm text-muted-foreground">Click to upload or drag and drop</p>
                      </div>
                    )}
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Name</label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  placeholder="Artifact name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  placeholder="Artifact description"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Type</label>
                <select
                  value={formData.artifact_type}
                  onChange={(e) => setFormData({ ...formData, artifact_type: e.target.value })}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="document">Document</option>
                  <option value="evidence">Evidence</option>
                  <option value="report">Report</option>
                  <option value="screenshot">Screenshot</option>
                  <option value="certificate">Certificate</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Policy ID (optional)</label>
                  <Input
                    type="number"
                    value={formData.policy_id}
                    onChange={(e) => setFormData({ ...formData, policy_id: e.target.value })}
                    placeholder="Policy ID"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Gap ID (optional)</label>
                  <Input
                    type="number"
                    value={formData.gap_id}
                    onChange={(e) => setFormData({ ...formData, gap_id: e.target.value })}
                    placeholder="Gap ID"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Control ID (optional)</label>
                  <Input
                    type="number"
                    value={formData.control_id}
                    onChange={(e) => setFormData({ ...formData, control_id: e.target.value })}
                    placeholder="Control ID"
                  />
                </div>
              </div>

              <Button type="submit" className="w-full" disabled={uploading}>
                {uploading ? 'Uploading...' : 'Upload Artifact'}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Uploaded Artifacts Section */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Uploaded Artifacts</CardTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setShowUploaded(!showUploaded)
                  if (!showUploaded) {
                    fetchArtifacts()
                  }
                }}
              >
                {showUploaded ? 'Hide' : 'View Uploaded'}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {showUploaded ? (
              loadingArtifacts ? (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
                  <p className="text-sm text-muted-foreground">Loading artifacts...</p>
                </div>
              ) : uploadedArtifacts.length > 0 ? (
                <div className="space-y-3 max-h-[600px] overflow-y-auto">
                  {uploadedArtifacts.map((artifact) => (
                    <div
                      key={artifact.id}
                      className="p-4 border border-gray-200 rounded-lg hover:border-gray-300 hover:shadow-sm transition-all bg-white"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <FileText className="h-4 w-4 text-gray-500 flex-shrink-0" />
                            <p className="text-sm font-semibold text-gray-900 truncate">{artifact.name}</p>
                          </div>
                          {artifact.description && (
                            <p className="text-xs text-gray-600 mt-1 line-clamp-2">{artifact.description}</p>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2 mt-2 flex-wrap">
                        <span className="text-xs font-medium px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                          {artifact.artifact_type}
                        </span>
                        <div className="flex items-center gap-1 text-xs text-gray-500">
                          <Clock className="h-3 w-3" />
                          <span>{formatDate(artifact.created_at)}</span>
                        </div>
                        {artifact.file_size && (
                          <span className="text-xs text-gray-500">
                            {formatFileSize(artifact.file_size)}
                          </span>
                        )}
                        {artifact.gap_id && (
                          <span className="text-xs text-gray-500">Gap: {artifact.gap_id}</span>
                        )}
                        {artifact.policy_id && (
                          <span className="text-xs text-gray-500">Policy: {artifact.policy_id}</span>
                        )}
                        {artifact.control_id && (
                          <span className="text-xs text-gray-500">Control: {artifact.control_id}</span>
                        )}
                      </div>
                      
                      <div className="flex items-center gap-2 mt-3">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleView(artifact)}
                          className="flex-1 text-xs"
                        >
                          <Eye className="h-3 w-3 mr-1" />
                          View
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDownload(artifact)}
                          className="flex-1 text-xs"
                        >
                          <Download className="h-3 w-3 mr-1" />
                          Download
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <FileText className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-sm font-medium text-gray-600">No artifacts uploaded yet</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {formData.gap_id || formData.policy_id || formData.control_id
                      ? 'No artifacts found for the selected filters'
                      : 'Upload your first artifact to get started'}
                  </p>
                </div>
              )
            ) : (
              <div className="text-center py-8">
                <CheckCircle className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                <p className="text-sm text-gray-600">Click "View Uploaded" to see your artifacts</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
