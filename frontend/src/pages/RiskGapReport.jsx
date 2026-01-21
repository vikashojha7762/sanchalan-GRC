import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import api from '@/lib/api'
import { AlertTriangle, Download, FileText, FileSpreadsheet, Loader2 } from 'lucide-react'

export default function RiskGapReport() {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    fetchReport()
  }, [])

  const fetchReport = async () => {
    try {
      setLoading(true)
      const res = await api.get('/reports/risk-gap')
      setReport(res.data)
      setError(null)
    } catch (err) {
      console.error('Error fetching risk-gap report:', err)
      setError(err.response?.data?.detail || 'Failed to fetch risk-gap report')
    } finally {
      setLoading(false)
    }
  }

  const getSeverityColor = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-red-100 text-red-800 border-red-300'
      case 'HIGH':
        return 'bg-orange-100 text-orange-800 border-orange-300'
      case 'MEDIUM':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'LOW':
        return 'bg-blue-100 text-blue-800 border-blue-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const getRiskScoreColor = (score) => {
    if (score >= 80) return 'text-red-600 font-bold'
    if (score >= 60) return 'text-orange-600 font-semibold'
    if (score >= 40) return 'text-yellow-600'
    return 'text-blue-600'
  }

  const exportToPDF = () => {
    // TODO: Implement PDF export
    alert('PDF export functionality coming soon!')
  }

  const exportToExcel = () => {
    // TODO: Implement Excel export
    alert('Excel export functionality coming soon!')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader2 className="h-12 w-12 text-primary mx-auto mb-4 animate-spin" />
          <p className="text-lg font-medium">Loading Risk & Gap Report...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Risk & Gap Report</h1>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
              <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5" />
              <div>
                <p className="font-medium text-red-800">Error</p>
                <p className="text-sm text-red-600 mt-1">{error}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!report) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Risk & Gap Report</h1>
        </div>
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">No report data available</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Risk & Gap Report</h1>
          <p className="text-muted-foreground">Comprehensive risk assessment and gap analysis</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={exportToPDF}
            className="flex items-center gap-2"
          >
            <FileText className="h-4 w-4" />
            Export PDF
          </Button>
          <Button
            variant="outline"
            onClick={exportToExcel}
            className="flex items-center gap-2"
          >
            <FileSpreadsheet className="h-4 w-4" />
            Export Excel
          </Button>
        </div>
      </div>

      {/* Summary Card */}
      <Card>
        <CardHeader>
          <CardTitle>Report Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-sm font-medium text-blue-800">Total Controls</p>
              <p className="text-2xl font-bold text-blue-900 mt-2">{report.summary.total_controls}</p>
            </div>
            <div className="p-4 bg-red-50 rounded-lg border border-red-200">
              <p className="text-sm font-medium text-red-800">Total Gaps</p>
              <p className="text-2xl font-bold text-red-900 mt-2">{report.summary.total_gaps}</p>
            </div>
            <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
              <p className="text-sm font-medium text-orange-800">High Risk</p>
              <p className="text-2xl font-bold text-orange-900 mt-2">{report.summary.high_risk}</p>
            </div>
            <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <p className="text-sm font-medium text-yellow-800">Medium Risk</p>
              <p className="text-2xl font-bold text-yellow-900 mt-2">{report.summary.medium_risk}</p>
            </div>
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <p className="text-sm font-medium text-blue-800">Low Risk</p>
              <p className="text-2xl font-bold text-blue-900 mt-2">{report.summary.low_risk}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Risks Table */}
      <Card>
        <CardHeader>
          <CardTitle>Risk & Gap Details</CardTitle>
        </CardHeader>
        <CardContent>
          {report.risks && report.risks.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-gray-50 border-b-2 border-gray-200">
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Framework</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Control</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Status</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Severity</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Risk</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Reason</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {report.risks.map((r, i) => (
                    <tr key={i} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3 text-sm font-medium">{r.framework}</td>
                      <td className="px-4 py-3 text-sm">
                        <div>
                          <span className="font-medium">{r.control_code}</span>
                          <p className="text-xs text-muted-foreground mt-1">{r.control_name}</p>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <span className="px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800">
                          {r.gap_status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <span className={`px-2 py-1 rounded text-xs font-medium border ${getSeverityColor(r.severity)}`}>
                          {r.severity}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <span className={`font-medium ${getRiskScoreColor(r.risk_score)}`}>
                          {r.risk_score}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 max-w-md">
                        <p className="truncate" title={r.risk_description}>
                          {r.risk_description}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          Area: {r.impacted_area}
                        </p>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 max-w-md">
                        <p className="truncate" title={r.recommended_action}>
                          {r.recommended_action}
                        </p>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 border rounded-lg bg-yellow-50">
              <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-3" />
              <p className="font-medium text-yellow-800 mb-1">No Risks Found</p>
              <p className="text-sm text-yellow-600">
                No gaps identified. Your compliance status looks good!
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

