import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import api from '@/lib/api'
import { Zap, Loader2, CheckCircle2, AlertTriangle, XCircle, Info } from 'lucide-react'

export default function GapAnalysis() {
  const [analyzing, setAnalyzing] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)

  const handleRunGapAnalysis = async () => {
    if (!confirm('Run AI Gap Analysis for all selected frameworks and controls? This may take a few moments.')) {
      return
    }

    setAnalyzing(true)
    setResults(null)
    setError(null)

    try {
      // PART 8: FIX FRONTEND - Use correct endpoint
      const res = await api.post('/gap-analysis/run')
      console.log('[Gap Analysis] API Response:', res.data)
      
      // Extract results - handle both single framework and multiple frameworks
      if (res.data.results) {
        // Single framework format: { framework: "...", results: [...] }
        setResults(res.data)
      } else if (res.data.frameworks && res.data.frameworks.length > 0) {
        // Multiple frameworks - use first one for now, or show all
        setResults(res.data)
      } else {
        setResults(res.data)
      }
    } catch (err) {
      console.error('Error running gap analysis:', err)
      setError(err.response?.data?.detail || 'Failed to run gap analysis. Please try again.')
    } finally {
      setAnalyzing(false)
    }
  }

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-300'
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-300'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'compliant':
        return 'bg-green-100 text-green-800 border-green-300'
      case 'non-compliant':
        return 'bg-red-100 text-red-800 border-red-300'
      case 'partially compliant':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">AI Gap Analysis</h1>
        <p className="text-muted-foreground">
          Analyze compliance gaps based on selected frameworks, controls, and uploaded policies/artifacts.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            Run Gap Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <p className="text-sm text-muted-foreground">
              This analysis will compare your selected controls against uploaded policies and artifacts to identify compliance gaps.
            </p>
            <Button
              onClick={handleRunGapAnalysis}
              disabled={analyzing}
              className="w-full sm:w-auto"
              size="lg"
            >
              {analyzing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4 mr-2" />
                  Run AI Gap Analysis
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {analyzing && (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8">
              <Loader2 className="h-12 w-12 text-primary mx-auto mb-4 animate-spin" />
              <p className="text-lg font-medium mb-2">Analyzing Controls and Policies</p>
              <p className="text-sm text-muted-foreground">
                This may take a few moments. Please do not close this page.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {error && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
              <XCircle className="h-5 w-5 text-red-600 mt-0.5" />
              <div>
                <p className="font-medium text-red-800">Error</p>
                <p className="text-sm text-red-600 mt-1">{error}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {results && (
        <div className="space-y-6">
          {/* PART 5: Show warning if warning field exists */}
          {results.warning && (
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-start gap-3 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-yellow-800">Warning</p>
                    <p className="text-sm text-yellow-600 mt-1">{results.warning}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Summary Card */}
          <Card>
            <CardHeader>
              <CardTitle>Analysis Summary</CardTitle>
            </CardHeader>
            <CardContent>
              {(() => {
                // Calculate totals from results if not provided in response
                let totalControls = results.total_controls || 0
                let gapsIdentified = results.gaps_identified || results.total_gaps || 0
                
                // If totals not in response, calculate from results
                if (totalControls === 0 || gapsIdentified === 0) {
                  let frameworksToCount = []
                  if (results.framework && results.results) {
                    frameworksToCount = [{ results: results.results }]
                  } else if (results.frameworks) {
                    frameworksToCount = results.frameworks
                  }
                  
                  totalControls = 0
                  gapsIdentified = 0
                  frameworksToCount.forEach(fw => {
                    const fwResults = fw.results || []
                    totalControls += fwResults.length
                    gapsIdentified += fwResults.filter(r => r.status === 'GAP').length
                  })
                }
                
                const compliantControls = totalControls - gapsIdentified
                
                return (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <p className="text-sm font-medium text-blue-800">Total Controls Analyzed</p>
                      <p className="text-2xl font-bold text-blue-900 mt-2">{totalControls}</p>
                    </div>
                    <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                      <p className="text-sm font-medium text-yellow-800">Gaps Identified</p>
                      <p className="text-2xl font-bold text-yellow-900 mt-2">{gapsIdentified}</p>
                    </div>
                    <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                      <p className="text-sm font-medium text-green-800">Compliant Controls</p>
                      <p className="text-2xl font-bold text-green-900 mt-2">{compliantControls}</p>
                    </div>
                  </div>
                )
              })()}
            </CardContent>
          </Card>

          {/* PART 7: TABULAR GAP RESPONSE (UI READY) */}
          {/* Extract gapResults from API response */}
          {(() => {
            // Handle both single framework and multiple frameworks response formats
            let frameworksToShow = []
            
            if (results.framework && results.results) {
              // Single framework format: { framework: "...", results: [...] }
              frameworksToShow = [{ framework: results.framework, results: results.results }]
            } else if (results.frameworks && results.frameworks.length > 0) {
              // Multiple frameworks format: { frameworks: [{ framework: "...", results: [...] }] }
              frameworksToShow = results.frameworks
            }
            
            if (frameworksToShow.length === 0) {
              // No frameworks found - show message
              return (
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center py-8 border rounded-lg bg-yellow-50">
                      <Info className="h-12 w-12 text-yellow-500 mx-auto mb-3" />
                      <p className="font-medium text-yellow-800 mb-1">No Analysis Results</p>
                      <p className="text-sm text-yellow-600">
                        {results.message || 'Please select and save controls during onboarding before running gap analysis.'}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )
            }
            
            return frameworksToShow.map((frameworkData, frameworkIdx) => {
              const gapResults = frameworkData.results || []
              const frameworkName = frameworkData.framework || 'Framework Analysis'
              
              if (gapResults.length === 0) {
                return (
                  <Card key={frameworkIdx}>
                    <CardHeader>
                      <CardTitle>{frameworkName}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-center py-8 border rounded-lg bg-yellow-50">
                        <Info className="h-12 w-12 text-yellow-500 mx-auto mb-3" />
                        <p className="font-medium text-yellow-800 mb-1">No Controls Selected</p>
                        <p className="text-sm text-yellow-600">
                          Please select and save controls during onboarding before running gap analysis.
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                )
              }
              
              return (
                <Card key={frameworkIdx}>
                  <CardHeader>
                    <CardTitle>{frameworkName}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full border-collapse">
                        <thead>
                          <tr className="bg-gray-50 border-b-2 border-gray-200">
                            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Control</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Status</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Severity</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Risk</th>
                            <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Reason</th>
                          </tr>
                        </thead>
                          <tbody>
                            {gapResults.map((r, i) => (
                              <tr key={r.control_code || i} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                                <td className="px-4 py-3 text-sm font-medium">{r.control_code || 'N/A'}</td>
                                <td className="px-4 py-3 text-sm">
                                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                                    r.status === 'GAP' 
                                      ? 'bg-red-100 text-red-800' 
                                      : r.status === 'COMPLIANT'
                                      ? 'bg-green-100 text-green-800'
                                      : 'bg-gray-100 text-gray-800'
                                  }`}>
                                    {r.status || 'N/A'}
                                  </span>
                                </td>
                                <td className="px-4 py-3 text-sm">
                                  {r.severity ? (
                                    <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(r.severity)}`}>
                                      {r.severity}
                                    </span>
                                  ) : (
                                    <span className="text-gray-400">-</span>
                                  )}
                                </td>
                                <td className="px-4 py-3 text-sm font-medium">{r.risk_score !== undefined ? r.risk_score : 0}</td>
                                <td className="px-4 py-3 text-sm text-gray-600">{r.reason || 'N/A'}</td>
                              </tr>
                            ))}
                          </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              )
            })
          })()}

        </div>
      )}
    </div>
  )
}

