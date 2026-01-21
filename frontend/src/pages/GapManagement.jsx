import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import api from '@/lib/api'
import { AlertTriangle, Plus, Search } from 'lucide-react'

export default function GapManagement() {
  const [gaps, setGaps] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedGap, setSelectedGap] = useState(null)
  const [showRemediationForm, setShowRemediationForm] = useState(false)
  const [remediationData, setRemediationData] = useState({
    title: '',
    description: '',
    action_plan: ''
  })

  useEffect(() => {
    fetchGaps()
  }, [])

  const fetchGaps = async () => {
    try {
      const response = await api.get('/gaps')
      setGaps(response.data)
    } catch (err) {
      console.error('Error fetching gaps:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateGap = async (gapId, updates) => {
    try {
      await api.patch(`/gaps/${gapId}`, updates)
      fetchGaps()
      setSelectedGap(null)
    } catch (err) {
      alert(err.response?.data?.detail || 'Error updating gap')
    }
  }

  const handleCreateRemediation = async () => {
    if (!selectedGap) return
    try {
      await api.post(`/gaps/${selectedGap.id}/remediations`, remediationData)
      setShowRemediationForm(false)
      setRemediationData({ title: '', description: '', action_plan: '' })
      fetchGaps()
    } catch (err) {
      alert(err.response?.data?.detail || 'Error creating remediation')
    }
  }

  const getSeverityColor = (severity) => {
    const colors = {
      low: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-orange-100 text-orange-800',
      critical: 'bg-red-100 text-red-800'
    }
    return colors[severity] || 'bg-gray-100 text-gray-800'
  }

  const filteredGaps = gaps.filter(gap =>
    gap.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    gap.description?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  if (loading) {
    return <div className="text-center py-8">Loading...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Gap Management</h1>
          <p className="text-muted-foreground">Identify, track, and remediate compliance gaps</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Gaps</CardTitle>
            <div className="relative w-64">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search gaps..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredGaps.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">No gaps found</p>
            ) : (
              filteredGaps.map((gap) => (
                <div
                  key={gap.id}
                  className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer"
                  onClick={() => setSelectedGap(gap)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <AlertTriangle className="h-5 w-5 text-yellow-500" />
                        <h3 className="font-semibold">{gap.title}</h3>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(gap.severity)}`}>
                          {gap.severity}
                        </span>
                        <span className="px-2 py-1 rounded text-xs bg-gray-100 text-gray-800">
                          {gap.status}
                        </span>
                      </div>
                      {gap.description && (
                        <p className="text-sm text-muted-foreground mb-2">{gap.description}</p>
                      )}
                      {gap.risk_score && (
                        <p className="text-sm">Risk Score: {gap.risk_score}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>

      {selectedGap && (
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle>Gap Details</CardTitle>
              <Button variant="outline" onClick={() => setSelectedGap(null)}>Close</Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Status</label>
              <select
                value={selectedGap.status}
                onChange={(e) => handleUpdateGap(selectedGap.id, { status: e.target.value })}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="identified">Identified</option>
                <option value="in_remediation">In Remediation</option>
                <option value="remediated">Remediated</option>
                <option value="verified">Verified</option>
                <option value="closed">Closed</option>
              </select>
            </div>
            {!showRemediationForm ? (
              <Button onClick={() => setShowRemediationForm(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Create Remediation
              </Button>
            ) : (
              <div className="space-y-4 border p-4 rounded-md">
                <h3 className="font-semibold">Create Remediation</h3>
                <Input
                  placeholder="Remediation Title"
                  value={remediationData.title}
                  onChange={(e) => setRemediationData({ ...remediationData, title: e.target.value })}
                />
                <Input
                  placeholder="Description"
                  value={remediationData.description}
                  onChange={(e) => setRemediationData({ ...remediationData, description: e.target.value })}
                />
                <textarea
                  placeholder="Action Plan"
                  value={remediationData.action_plan}
                  onChange={(e) => setRemediationData({ ...remediationData, action_plan: e.target.value })}
                  className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
                <div className="flex gap-2">
                  <Button onClick={handleCreateRemediation}>Create</Button>
                  <Button variant="outline" onClick={() => setShowRemediationForm(false)}>Cancel</Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
