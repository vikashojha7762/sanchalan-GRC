import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts'
import api from '@/lib/api'
import { 
  AlertTriangle, 
  CheckCircle, 
  FileText, 
  TrendingUp, 
  TrendingDown,
  Shield,
  Target,
  ArrowRight,
  Upload,
  Eye,
  Activity
} from 'lucide-react'

// Severity colors - Professional palette
const SEVERITY_COLORS = {
  'CRITICAL': '#DC2626',  // Red
  'HIGH': '#F97316',      // Orange
  'MEDIUM': '#F59E0B',    // Amber
  'LOW': '#10B981',       // Green
  'INFO': '#3B82F6',      // Blue
  'MINOR': '#6B7280'      // Gray
}

// Status colors for compliance readiness
const getReadinessStatus = (score) => {
  if (score === null || score === undefined) return { label: 'Not Started', color: '#6B7280', bg: 'bg-gray-50' }
  if (score >= 80) return { label: 'Mature', color: '#10B981', bg: 'bg-green-50' }
  if (score >= 50) return { label: 'Improving', color: '#F59E0B', bg: 'bg-amber-50' }
  return { label: 'Early', color: '#F97316', bg: 'bg-orange-50' }
}

// Circular progress component
const CircularProgress = ({ percentage, size = 120, strokeWidth = 10 }) => {
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const offset = circumference - (percentage / 100) * circumference
  const status = getReadinessStatus(percentage)
  
  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#E5E7EB"
          strokeWidth={strokeWidth}
          fill="none"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={status.color}
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-500"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold" style={{ color: status.color }}>
          {percentage !== null && percentage !== undefined ? `${Math.round(percentage)}%` : 'N/A'}
        </span>
        <span className="text-xs font-medium text-gray-600 mt-1">{status.label}</span>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    fetchSummary()
  }, [])

  const fetchSummary = async () => {
    try {
      const response = await api.get('/dashboard/summary')
      setSummary(response.data)
    } catch (err) {
      console.error('Error fetching summary:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Activity className="h-8 w-8 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  if (!summary) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <p className="text-muted-foreground">No data available</p>
      </div>
    )
  }

  // Calculate metrics
  const complianceScore = summary.compliance_score || 0
  const readinessStatus = getReadinessStatus(complianceScore)
  const closedGaps = summary.gaps_by_status?.closed || 0
  const openGaps = summary.total_gaps - closedGaps
  const highRiskItems = (summary.gaps_by_severity?.high || 0) + (summary.gaps_by_severity?.critical || 0)
  const inRemediation = summary.gaps_by_status?.in_remediation || 0
  
  // Calculate controls covered (simplified: based on policies vs controls)
  const controlsCovered = summary.total_controls > 0 
    ? Math.min(100, Math.round((summary.total_policies / summary.total_controls) * 100))
    : 0

  // Prepare severity data for chart
  const severityData = Object.entries(summary.gaps_by_severity || {})
    .map(([key, value]) => {
      const severityKey = key.toUpperCase()
      return {
        name: key.charAt(0).toUpperCase() + key.slice(1).toLowerCase(),
        value: value || 0,
        severity: severityKey,
        color: SEVERITY_COLORS[severityKey] || SEVERITY_COLORS['INFO']
      }
    })
    .filter(item => item.value > 0)
    .sort((a, b) => {
      const order = { 'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4, 'MINOR': 5 }
      return (order[a.severity] || 99) - (order[b.severity] || 99)
    })

  const totalGaps = severityData.reduce((sum, item) => sum + item.value, 0)

  // Get top 3 high-risk gaps for "What to Fix Next"
  const topRisks = summary.recent_gaps
    ?.filter(gap => gap.severity === 'high' || gap.severity === 'critical')
    .slice(0, 3) || []

  // Trend indicators (mock data - in production, calculate from historical data)
  const gapTrend = openGaps > 0 ? 'up' : 'neutral'
  const controlsTrend = 'up'
  const evidenceTrend = 'up'

  return (
    <div className="space-y-8 pb-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Compliance Dashboard</h1>
          <p className="text-muted-foreground mt-1">Monitor your governance, risk, and compliance posture</p>
        </div>
        <Button
          variant="outline"
          onClick={() => navigate("/reports/risk-gap")}
          className="flex items-center gap-2"
        >
          <FileText className="h-4 w-4" />
          View Reports
        </Button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Compliance Readiness */}
        <Card className="border border-gray-200 shadow-sm hover:shadow-md transition-shadow bg-white">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600 mb-1">Compliance Readiness</p>
                <div className="flex items-center gap-2 mt-2">
                  <span className={`text-xs font-semibold px-2 py-1 rounded-full ${readinessStatus.bg}`} style={{ color: readinessStatus.color }}>
                    {readinessStatus.label}
                  </span>
                </div>
              </div>
              <div className="p-2 rounded-lg bg-gradient-to-br from-blue-50 to-indigo-50">
                <Target className="h-5 w-5 text-blue-600" />
              </div>
            </div>
            <CircularProgress percentage={complianceScore} size={100} strokeWidth={8} />
          </CardContent>
        </Card>

        {/* Open Gaps */}
        <Card className="border border-gray-200 shadow-sm hover:shadow-md transition-shadow bg-white">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600 mb-1">Open Gaps</p>
                <p className="text-3xl font-bold text-gray-900">{openGaps}</p>
              </div>
              <div className="p-2 rounded-lg bg-gradient-to-br from-orange-50 to-red-50">
                <AlertTriangle className="h-5 w-5 text-orange-600" />
              </div>
            </div>
            <div className="flex items-center gap-1 mt-3">
              {gapTrend === 'up' ? (
                <TrendingUp className="h-4 w-4 text-orange-600" />
              ) : gapTrend === 'down' ? (
                <TrendingDown className="h-4 w-4 text-green-600" />
              ) : null}
              <span className={`text-xs font-medium ${gapTrend === 'up' ? 'text-orange-600' : gapTrend === 'down' ? 'text-green-600' : 'text-gray-500'}`}>
                {inRemediation > 0 ? `${inRemediation} in remediation` : 'No change'}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* High Risk Items */}
        <Card className="border border-gray-200 shadow-sm hover:shadow-md transition-shadow bg-white">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600 mb-1">High Risk Items</p>
                <p className="text-3xl font-bold text-gray-900">{highRiskItems}</p>
              </div>
              <div className="p-2 rounded-lg bg-gradient-to-br from-red-50 to-rose-50">
                <Shield className="h-5 w-5 text-red-600" />
              </div>
            </div>
            <div className="mt-3">
              <span className="text-xs font-medium text-gray-500">
                {summary.gaps_by_severity?.critical || 0} critical, {summary.gaps_by_severity?.high || 0} high
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Controls Covered */}
        <Card className="border border-gray-200 shadow-sm hover:shadow-md transition-shadow bg-white">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600 mb-1">Controls Covered</p>
                <p className="text-3xl font-bold text-gray-900">{controlsCovered}%</p>
              </div>
              <div className="p-2 rounded-lg bg-gradient-to-br from-green-50 to-emerald-50">
                <CheckCircle className="h-5 w-5 text-green-600" />
              </div>
            </div>
            <div className="flex items-center gap-1 mt-3">
              {controlsTrend === 'up' ? (
                <TrendingUp className="h-4 w-4 text-green-600" />
              ) : null}
              <span className="text-xs font-medium text-gray-500">
                {summary.total_policies} policies active
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Active Frameworks */}
        <Card className="border border-gray-200 shadow-sm hover:shadow-md transition-shadow bg-white">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600 mb-1">Active Frameworks</p>
                <p className="text-3xl font-bold text-gray-900">{summary.total_frameworks}</p>
              </div>
              <div className="p-2 rounded-lg bg-gradient-to-br from-purple-50 to-pink-50">
                <FileText className="h-5 w-5 text-purple-600" />
              </div>
            </div>
            <div className="mt-3">
              <span className="text-xs font-medium text-gray-500">
                {summary.total_controls} total controls
              </span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Primary Risk Visualization - Stacked Bar Chart */}
        <Card className="lg:col-span-2 border border-gray-200 shadow-sm bg-white">
          <CardHeader className="border-b border-gray-200 bg-gray-50">
            <CardTitle className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Activity className="h-5 w-5 text-gray-600" />
              Risk Overview
            </CardTitle>
            <p className="text-sm text-gray-600 mt-1">Gaps by severity level</p>
          </CardHeader>
          <CardContent className="pt-6">
            {totalGaps > 0 ? (
              <div className="w-full">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={severityData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" opacity={0.5} />
                    <XAxis 
                      dataKey="name" 
                      tick={{ fill: '#6B7280', fontSize: 12 }}
                      stroke="#9CA3AF"
                    />
                    <YAxis 
                      tick={{ fill: '#6B7280', fontSize: 12 }}
                      stroke="#9CA3AF"
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#fff', 
                        border: '1px solid #E5E7EB',
                        borderRadius: '6px',
                        padding: '8px 12px',
                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                      }}
                      formatter={(value) => [`${value} gaps`, '']}
                    />
                    <Bar 
                      dataKey="value" 
                      radius={[6, 6, 0, 0]}
                      label={{ 
                        position: 'top', 
                        fill: '#374151',
                        fontSize: 12,
                        fontWeight: 600,
                        formatter: (value) => value > 0 ? value : ''
                      }}
                    >
                      {severityData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
                
                {/* Legend */}
                <div className="mt-6 grid grid-cols-2 md:grid-cols-3 gap-3">
                  {severityData.map((item, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <div 
                        className="w-4 h-4 rounded border border-gray-200"
                        style={{ backgroundColor: item.color }}
                      />
                      <span className="text-sm font-medium text-gray-700">{item.name}</span>
                      <span className="text-sm font-semibold text-gray-900 ml-auto">{item.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                <p className="text-sm font-medium text-gray-600">No gaps identified</p>
                <p className="text-xs text-gray-500 mt-1">All controls are compliant</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* What to Fix Next - Action Panel */}
        <Card className="border border-gray-200 shadow-sm bg-white">
          <CardHeader className="border-b border-gray-200 bg-gray-50">
            <CardTitle className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <Target className="h-5 w-5 text-gray-600" />
              What to Fix Next
            </CardTitle>
            <p className="text-sm text-gray-600 mt-1">Priority actions</p>
          </CardHeader>
          <CardContent className="pt-6">
            {topRisks.length > 0 ? (
              <div className="space-y-4">
                {topRisks.map((gap, index) => (
                  <div 
                    key={gap.id} 
                    className="p-4 border border-gray-200 rounded-lg hover:border-orange-300 hover:shadow-sm transition-all bg-white"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <p className="text-sm font-semibold text-gray-900 line-clamp-2">{gap.title}</p>
                        <div className="flex items-center gap-2 mt-2">
                          <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                            gap.severity === 'critical' 
                              ? 'bg-red-100 text-red-700' 
                              : 'bg-orange-100 text-orange-700'
                          }`}>
                            {gap.severity.toUpperCase()}
                          </span>
                          <span className="text-xs text-gray-500">{gap.status}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 mt-3">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => navigate(`/gaps`)}
                        className="flex-1 text-xs"
                      >
                        <Eye className="h-3 w-3 mr-1" />
                        View Gap
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => navigate(`/artifacts`)}
                        className="flex-1 text-xs"
                      >
                        <Upload className="h-3 w-3 mr-1" />
                        Upload Evidence
                      </Button>
                    </div>
                  </div>
                ))}
                {topRisks.length < 3 && (
                  <Button
                    variant="outline"
                    className="w-full mt-2"
                    onClick={() => navigate('/gaps')}
                  >
                    View All Gaps
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </Button>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <CheckCircle className="h-10 w-10 text-green-500 mx-auto mb-3" />
                <p className="text-sm font-medium text-gray-600">No high-priority items</p>
                <p className="text-xs text-gray-500 mt-1">All critical gaps are addressed</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Trends & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Gaps */}
        <Card className="border border-gray-200 shadow-sm bg-white">
          <CardHeader className="border-b border-gray-200 bg-gray-50">
            <CardTitle className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-gray-600" />
              Recent Gaps
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            {summary.recent_gaps && summary.recent_gaps.length > 0 ? (
              <div className="space-y-3">
                {summary.recent_gaps.slice(0, 5).map((gap) => (
                  <div 
                    key={gap.id} 
                    className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:border-gray-300 hover:shadow-sm transition-all cursor-pointer"
                    onClick={() => navigate('/gaps')}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{gap.title}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                          gap.severity === 'critical' 
                            ? 'bg-red-100 text-red-700'
                            : gap.severity === 'high'
                            ? 'bg-orange-100 text-orange-700'
                            : gap.severity === 'medium'
                            ? 'bg-amber-100 text-amber-700'
                            : 'bg-gray-100 text-gray-700'
                        }`}>
                          {gap.severity}
                        </span>
                        <span className="text-xs text-gray-500">{gap.status}</span>
                      </div>
                    </div>
                    <ArrowRight className="h-4 w-4 text-gray-400 ml-2 flex-shrink-0" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <CheckCircle className="h-10 w-10 text-green-500 mx-auto mb-3" />
                <p className="text-sm text-gray-600">No recent gaps</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Policies */}
        <Card className="border border-gray-200 shadow-sm bg-white">
          <CardHeader className="border-b border-gray-200 bg-gray-50">
            <CardTitle className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <FileText className="h-5 w-5 text-gray-600" />
              Recent Policies
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            {summary.recent_policies && summary.recent_policies.length > 0 ? (
              <div className="space-y-3">
                {summary.recent_policies.slice(0, 5).map((policy) => (
                  <div 
                    key={policy.id} 
                    className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:border-gray-300 hover:shadow-sm transition-all cursor-pointer"
                    onClick={() => navigate('/approvals')}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{policy.title}</p>
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded mt-1 inline-block ${
                        policy.status === 'approved'
                          ? 'bg-green-100 text-green-700'
                          : policy.status === 'under_review'
                          ? 'bg-amber-100 text-amber-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}>
                        {policy.status.replace('_', ' ')}
                      </span>
                    </div>
                    <ArrowRight className="h-4 w-4 text-gray-400 ml-2 flex-shrink-0" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <FileText className="h-10 w-10 text-gray-400 mx-auto mb-3" />
                <p className="text-sm text-gray-600">No recent policies</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
