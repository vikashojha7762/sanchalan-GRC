import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/Button'
import api from '@/lib/api'
import { CheckCircle, XCircle, Eye, Clock, FileText, Building2, User, Calendar, X } from 'lucide-react'

export default function Approvals() {
  const [activeTab, setActiveTab] = useState('pending')
  const [policies, setPolicies] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedPolicy, setSelectedPolicy] = useState(null)
  const [showModal, setShowModal] = useState(false)

  useEffect(() => {
    fetchPolicies()
  }, [activeTab])

  const fetchPolicies = async () => {
    setLoading(true)
    try {
      let statusParam = ''
      
      // Map tabs to status values
      if (activeTab === 'pending') {
        statusParam = 'under_review'
      } else if (activeTab === 'approved') {
        statusParam = 'approved'
      } else if (activeTab === 'rejected') {
        // Fetch rejected policies
        statusParam = 'rejected'
      }

      const response = await api.get('/policies', {
        params: statusParam ? { status: statusParam } : {}
      })
      
      // Ensure response.data is an array
      let filteredPolicies = Array.isArray(response.data) ? response.data : []
      
      setPolicies(filteredPolicies)
    } catch (err) {
      console.error('Error fetching policies:', err)
      // Better error handling
      if (err.code === 'ERR_NETWORK' || err.code === 'ERR_FAILED') {
        console.error('Network error - backend may not be running')
        alert('Unable to connect to server. Please ensure the backend is running.')
      } else {
        console.error('API error:', err.response?.data || err.message)
      }
      setPolicies([])
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (policyId) => {
    if (!confirm('Are you sure you want to approve this policy?')) {
      return
    }
    try {
      const response = await api.patch(`/policies/${policyId}`, { status: 'approved' })
      
      // Verify response was successful
      if (response && response.data) {
        // Close modal if open
        if (showModal) {
          closeModal()
        }
        // Small delay to ensure backend has processed the change
        await new Promise(resolve => setTimeout(resolve, 100))
        // Refresh policies list
        await fetchPolicies()
      }
    } catch (err) {
      console.error('Error approving policy:', err)
      const errorMessage = err.isNetworkError 
        ? err.message 
        : err.response?.data?.detail || err.message || 'Error approving policy'
      alert(errorMessage)
    }
  }

  const handleReject = async (policyId) => {
    if (!confirm('Are you sure you want to reject this policy?')) {
      return
    }
    try {
      const response = await api.patch(`/policies/${policyId}`, { status: 'rejected' })
      
      // Verify response was successful
      if (response && response.data) {
        // Close modal if open
        if (showModal) {
          closeModal()
        }
        // Small delay to ensure backend has processed the change
        await new Promise(resolve => setTimeout(resolve, 100))
        // Refresh policies list
        await fetchPolicies()
      }
    } catch (err) {
      console.error('Error rejecting policy:', err)
      const errorMessage = err.isNetworkError 
        ? err.message 
        : err.response?.data?.detail || err.message || 'Error rejecting policy'
      alert(errorMessage)
    }
  }

  const handleViewPolicy = (policy) => {
    setSelectedPolicy(policy)
    setShowModal(true)
  }

  const closeModal = () => {
    setShowModal(false)
    setSelectedPolicy(null)
  }

  const handleApproveWithModal = async (policyId) => {
    if (!confirm('Are you sure you want to approve this policy?')) {
      return
    }
    try {
      const response = await api.patch(`/policies/${policyId}`, { status: 'approved' })
      
      // Verify response was successful
      if (response && response.data) {
        // Close modal first
        closeModal()
        // Small delay to ensure backend has processed the change
        await new Promise(resolve => setTimeout(resolve, 100))
        // Switch to approved tab to show the approved policy
        setActiveTab('approved')
        // Then refresh policies list (will fetch approved policies)
        await fetchPolicies()
      }
    } catch (err) {
      console.error('Error approving policy:', err)
      const errorMessage = err.isNetworkError 
        ? err.message 
        : err.response?.data?.detail || err.message || 'Error approving policy'
      alert(errorMessage)
      // Don't close modal on error so user can retry
    }
  }

  const handleRejectWithModal = async (policyId) => {
    if (!confirm('Are you sure you want to reject this policy?')) {
      return
    }
    try {
      const response = await api.patch(`/policies/${policyId}`, { status: 'rejected' })
      
      // Verify response was successful
      if (response && response.data) {
        // Close modal first
        closeModal()
        // Small delay to ensure backend has processed the change
        await new Promise(resolve => setTimeout(resolve, 100))
        // Switch to rejected tab to show the rejected policy
        setActiveTab('rejected')
        // Then refresh policies list (will fetch rejected policies)
        await fetchPolicies()
      }
    } catch (err) {
      console.error('Error rejecting policy:', err)
      const errorMessage = err.isNetworkError 
        ? err.message 
        : err.response?.data?.detail || err.message || 'Error rejecting policy'
      alert(errorMessage)
      // Don't close modal on error so user can retry
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    })
  }

  const getStatusBadge = (status) => {
    const statusMap = {
      'under_review': {
        label: 'Pending',
        className: 'bg-yellow-100 text-yellow-800 border-yellow-200'
      },
      'approved': {
        label: 'Approved',
        className: 'bg-green-100 text-green-800 border-green-200'
      },
      'draft': {
        label: 'Draft',
        className: 'bg-gray-100 text-gray-800 border-gray-200'
      },
      'rejected': {
        label: 'Rejected',
        className: 'bg-red-100 text-red-800 border-red-200'
      },
      'published': {
        label: 'Published',
        className: 'bg-blue-100 text-blue-800 border-blue-200'
      }
    }

    const statusInfo = statusMap[status] || {
      label: status,
      className: 'bg-gray-100 text-gray-800 border-gray-200'
    }

    return (
      <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold border ${statusInfo.className}`}>
        {statusInfo.label}
      </span>
    )
  }

  const tabs = [
    { id: 'pending', label: 'Pending' },
    { id: 'approved', label: 'Approved' },
    { id: 'rejected', label: 'Rejected' }
  ]

  return (
    <div className="space-y-8 p-6">
      {/* Header Section */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">Approvals Workflow</h1>
        <p className="text-gray-600">Review and approve pending policies</p>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8" aria-label="Tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm transition-all duration-200
                ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600 font-bold'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content Section */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading policies...</p>
        </div>
      ) : policies.length === 0 ? (
        /* Empty State */
        <div className="flex items-center justify-center py-16">
          <div className="bg-gray-50 rounded-xl py-10 px-8 text-center shadow-sm max-w-md w-full">
            <div className="text-6xl mb-4">📝</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              No {activeTab} approvals
            </h3>
            <p className="text-gray-600">
              {activeTab === 'pending' 
                ? "You're all caught up!" 
                : activeTab === 'approved'
                ? "No approved policies yet."
                : "No rejected policies."}
            </p>
          </div>
        </div>
      ) : (
        /* Policy Cards Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {policies.map((policy) => (
            <div
              key={policy.id}
              className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-all duration-200 hover:border-gray-300"
            >
              {/* Card Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <FileText className="h-5 w-5 text-blue-600 flex-shrink-0" />
                    <h3 className="font-semibold text-lg text-gray-900 line-clamp-2">
                      {policy.title}
                    </h3>
                  </div>
                  {getStatusBadge(policy.status)}
                </div>
              </div>

              {/* Card Body */}
              <div className="space-y-3 mb-6">
                {/* Framework */}
                {(policy.framework || policy.framework_id) && (
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Building2 className="h-4 w-4 text-gray-400" />
                    <span className="font-medium">Framework:</span>
                    <span>{policy.framework?.name || `Framework ID: ${policy.framework_id}` || 'N/A'}</span>
                  </div>
                )}

                {/* Department - Using owner info as department proxy */}
                {(policy.owner || policy.owner_id) && (
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <User className="h-4 w-4 text-gray-400" />
                    <span className="font-medium">Submitted By:</span>
                    <span>
                      {policy.owner?.name || 
                       policy.owner?.email || 
                       `User ID: ${policy.owner_id}` || 
                       'N/A'}
                    </span>
                  </div>
                )}

                {/* Date Submitted */}
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Calendar className="h-4 w-4 text-gray-400" />
                  <span className="font-medium">Date Submitted:</span>
                  <span>{formatDate(policy.created_at)}</span>
                </div>

                {/* Policy Number */}
                {policy.policy_number && (
                  <div className="text-sm text-gray-600">
                    <span className="font-medium">Policy #:</span> {policy.policy_number}
                  </div>
                )}

                {/* Description Preview */}
                {policy.description && (
                  <p className="text-sm text-gray-600 line-clamp-2 mt-2">
                    {policy.description}
                  </p>
                )}
              </div>

              {/* Card Actions */}
              <div className="flex flex-col gap-2 pt-4 border-t border-gray-100">
                {activeTab === 'pending' && (
                  <div className="flex gap-2">
                    <Button
                      onClick={() => handleApprove(policy.id)}
                      className="flex-1 bg-green-600 hover:bg-green-700 text-white transition-all duration-200 shadow-sm hover:shadow"
                    >
                      <CheckCircle className="mr-2 h-4 w-4" />
                      Approve
                    </Button>
                    <Button
                      onClick={() => handleReject(policy.id)}
                      className="flex-1 bg-red-600 hover:bg-red-700 text-white transition-all duration-200 shadow-sm hover:shadow"
                    >
                      <XCircle className="mr-2 h-4 w-4" />
                      Reject
                    </Button>
                  </div>
                )}
                <Button
                  variant="outline"
                  onClick={() => handleViewPolicy(policy)}
                  className="w-full border-gray-300 hover:bg-gray-50 transition-all duration-200"
                >
                  <Eye className="mr-2 h-4 w-4" />
                  View Policy
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Policy View Modal */}
      {showModal && selectedPolicy && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          {/* Backdrop */}
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
            onClick={closeModal}
          ></div>
          
          {/* Modal */}
          <div className="flex min-h-full items-center justify-center p-4">
            <div className="relative bg-white rounded-xl shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
              {/* Modal Header */}
              <div className="flex items-center justify-between p-6 border-b border-gray-200">
                <div className="flex items-center gap-3">
                  <FileText className="h-6 w-6 text-blue-600" />
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900">{selectedPolicy.title}</h2>
                    {selectedPolicy.policy_number && (
                      <p className="text-sm text-gray-500">Policy #: {selectedPolicy.policy_number}</p>
                    )}
                  </div>
                </div>
                <button
                  onClick={closeModal}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>

              {/* Modal Body */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {/* Policy Info */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                      <span className="font-semibold text-gray-700">Status:</span>
                      {getStatusBadge(selectedPolicy.status)}
                    </div>
                    {(selectedPolicy.framework || selectedPolicy.framework_id) && (
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <Building2 className="h-4 w-4 text-gray-400" />
                        <span className="font-semibold">Framework:</span>
                        <span>{selectedPolicy.framework?.name || `ID: ${selectedPolicy.framework_id}` || 'N/A'}</span>
                      </div>
                    )}
                  </div>
                  <div className="space-y-2">
                    {(selectedPolicy.owner || selectedPolicy.owner_id) && (
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <User className="h-4 w-4 text-gray-400" />
                        <span className="font-semibold">Submitted By:</span>
                        <span>
                          {selectedPolicy.owner?.name || 
                           selectedPolicy.owner?.email || 
                           `User ID: ${selectedPolicy.owner_id}` || 
                           'N/A'}
                        </span>
                      </div>
                    )}
                    <div className="flex items-center gap-2 text-sm text-gray-600">
                      <Calendar className="h-4 w-4 text-gray-400" />
                      <span className="font-semibold">Date Submitted:</span>
                      <span>{formatDate(selectedPolicy.created_at)}</span>
                    </div>
                  </div>
                </div>

                {/* Description */}
                {selectedPolicy.description && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Description</h3>
                    <p className="text-gray-700 whitespace-pre-wrap">{selectedPolicy.description}</p>
                  </div>
                )}

                {/* Content */}
                {selectedPolicy.content && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Policy Content</h3>
                    <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 max-h-96 overflow-y-auto">
                      <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans">
                        {selectedPolicy.content}
                      </pre>
                    </div>
                  </div>
                )}

                {!selectedPolicy.content && !selectedPolicy.description && (
                  <div className="text-center py-8 text-gray-500">
                    <p>No content available for this policy.</p>
                  </div>
                )}
              </div>

              {/* Modal Footer */}
              <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50 rounded-b-xl">
                <Button
                  variant="outline"
                  onClick={closeModal}
                  className="border-gray-300 hover:bg-gray-100"
                >
                  Close
                </Button>
                {activeTab === 'pending' && (
                  <div className="flex gap-3">
                    <Button
                      onClick={() => handleRejectWithModal(selectedPolicy.id)}
                      className="bg-red-600 hover:bg-red-700 text-white"
                    >
                      <XCircle className="mr-2 h-4 w-4" />
                      Reject
                    </Button>
                    <Button
                      onClick={() => handleApproveWithModal(selectedPolicy.id)}
                      className="bg-green-600 hover:bg-green-700 text-white"
                    >
                      <CheckCircle className="mr-2 h-4 w-4" />
                      Approve
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
