import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card'
import api from '@/lib/api'
import { CheckCircle2, Circle, Building2, Users, Shield, Layers, FileText, CheckCircle } from 'lucide-react'

const steps = [
  { name: 'Company Details', icon: Building2 },
  { name: 'Departments', icon: Users },
  { name: 'Roles & Access', icon: Shield },
  { name: 'Framework Selection', icon: Layers },
  { name: 'Framework Controls', icon: Shield },
  { name: 'Policy Upload', icon: FileText },
  { name: 'Completion Screen', icon: CheckCircle }
]

export default function Onboarding() {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState(0)
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)

  // Form data
  const [companyData, setCompanyData] = useState({ name: 'Acme Inc.', domain: 'example.com', industry: '', size: '' })
  const [departments, setDepartments] = useState([{ name: '', description: '' }])
  const [selectedDepartment, setSelectedDepartment] = useState('')
  const [roles, setRoles] = useState([{ name: '', description: '', permissions: '' }])
  const [selectedRole, setSelectedRole] = useState('')
  const [frameworks, setFrameworks] = useState([{ name: '', description: '', version: '', category: '' }])
  const [selectedFrameworks, setSelectedFrameworks] = useState([])
  const [expandedCategories, setExpandedCategories] = useState({})
  const [uploadedPolicies, setUploadedPolicies] = useState([])
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef(null)
  const [iso27001Controls, setIso27001Controls] = useState([])
  const [iso27001FrameworkId, setIso27001FrameworkId] = useState(null)
  const [selectedControls, setSelectedControls] = useState([])
  const [loadingControls, setLoadingControls] = useState(false)
  const [controlsSaved, setControlsSaved] = useState(false)

  useEffect(() => {
    fetchStatus()
  }, [])

  useEffect(() => {
    // Fetch ISO 27001 controls when ISO 27001 is selected and we're on Framework Controls step
    if (currentStep === 4 && selectedFrameworks.includes('ISO 27001') && iso27001Controls.length === 0) {
      fetchISO27001Controls()
    }
  }, [currentStep, selectedFrameworks])
  
  // Debug: Monitor selectedControls changes
  useEffect(() => {
    console.log('[Onboarding] selectedControls changed:', {
      count: selectedControls.length,
      ids: selectedControls,
      types: selectedControls.map(id => typeof id)
    })
  }, [selectedControls])

  const fetchISO27001Controls = async () => {
    setLoadingControls(true)
    try {
      const response = await api.get('/frameworks/iso27001/control-tree')
      // Store framework ID from response
      setIso27001FrameworkId(response.data.framework_id)
      // Filter for A.5, A.6, A.7, A.8 groups
      const targetGroups = ['A.5', 'A.6', 'A.7', 'A.8']
      const filteredTree = response.data.tree.filter(group => 
        targetGroups.some(code => group.code && group.code.startsWith(code))
      )
      
      // Extract all control IDs for validation
      const allControlIds = []
      filteredTree.forEach(group => {
        if (group.children) {
          group.children.forEach(control => {
            if (control.type === 'control' && control.id) {
              allControlIds.push(Number(control.id))
            }
          })
        }
      })
      
      // Log for debugging
      console.log('[Onboarding] ===== FETCHED ISO 27001 CONTROLS =====')
      console.log('[Onboarding] Framework ID:', response.data.framework_id)
      console.log('[Onboarding] Groups count:', filteredTree.length)
      console.log('[Onboarding] Total controls:', allControlIds.length)
      console.log('[Onboarding] Control IDs sample:', allControlIds.slice(0, 10))
      console.log('[Onboarding] Sample control:', filteredTree[0]?.children?.[0])
      console.log('[Onboarding] =====================================')
      
      setIso27001Controls(filteredTree)
    } catch (err) {
      console.error('Error fetching ISO 27001 controls:', err)
    } finally {
      setLoadingControls(false)
    }
  }

  const handleControlToggle = (controlId) => {
    // Ensure controlId is a valid integer
    const id = typeof controlId === 'string' ? parseInt(controlId, 10) : Number(controlId)
    
    // Validate ID
    if (isNaN(id) || id <= 0) {
      console.error('[Onboarding] Invalid control ID in toggle:', controlId, 'Type:', typeof controlId)
      return
    }
    
    setSelectedControls(prev => {
      // Normalize all IDs to integers for comparison
      const normalizedPrev = prev.map(pid => {
        const numId = typeof pid === 'string' ? parseInt(pid, 10) : Number(pid)
        return isNaN(numId) || numId <= 0 ? null : numId
      }).filter(pid => pid !== null)
      
      if (normalizedPrev.includes(id)) {
        const filtered = normalizedPrev.filter(prevId => prevId !== id)
        console.log('[Onboarding] Control deselected:', id, 'Remaining:', filtered.length)
        return filtered
      } else {
        const added = [...normalizedPrev, id]
        console.log('[Onboarding] Control selected:', id, 'Total selected:', added.length)
        return added
      }
    })
  }

  const handleSaveControls = async () => {
    console.log('[Onboarding] ===== SAVE CONTROLS CLICKED =====')
    console.log('[Onboarding] selectedControls state:', selectedControls)
    console.log('[Onboarding] selectedControls length:', selectedControls.length)
    console.log('[Onboarding] selectedControls types:', selectedControls.map(id => ({ id, type: typeof id })))
    
    if (selectedControls.length === 0) {
      alert('Please select at least one control before saving.')
      return
    }

    setLoading(true)
    try {
      // Store selected controls IMMEDIATELY - don't let them get cleared
      // Normalize and validate all IDs
      const controlsToSave = selectedControls
        .map(id => {
          const numId = typeof id === 'string' ? parseInt(id, 10) : Number(id)
          if (isNaN(numId) || numId <= 0) {
            console.warn('[Onboarding] Invalid control ID filtered:', id, 'Type:', typeof id)
            return null
          }
          return numId
        })
        .filter(id => id !== null && id > 0)
      
      console.log('[Onboarding] ===== VALIDATION =====')
      console.log('[Onboarding] Original selectedControls:', selectedControls)
      console.log('[Onboarding] Normalized controlsToSave:', controlsToSave)
      console.log('[Onboarding] Valid controls count:', controlsToSave.length)
      
      // Validate we have controls before proceeding
      if (controlsToSave.length === 0) {
        console.error('[Onboarding] ❌ No valid control IDs after normalization!')
        console.error('[Onboarding] Original selectedControls:', selectedControls)
        alert('No valid control IDs found. The selected controls may have invalid IDs. Please refresh the page and reselect controls.')
        setLoading(false)
        return
      }
      
      // Ensure ISO 27001 framework is seeded first
      // After seeding, refresh controls to get current IDs (seed function now preserves IDs)
      try {
        await api.post('/frameworks/seed/iso27001')
        console.log('[Onboarding] Framework seeded successfully')
        
        // Always fetch fresh controls after seeding to ensure we have current IDs
        const controlsResponse = await api.get('/frameworks/iso27001/control-tree')
        const targetGroups = ['A.5', 'A.6', 'A.7', 'A.8']
        const filteredTree = controlsResponse.data.tree.filter(group => 
          targetGroups.some(code => group.code && group.code.startsWith(code))
        )
        
        setIso27001FrameworkId(controlsResponse.data.framework_id)
        setIso27001Controls(filteredTree)
        console.log('[Onboarding] Controls refreshed, framework ID:', controlsResponse.data.framework_id)
        
        // After refreshing controls, validate that selected controls still exist
        // Extract all valid control IDs from refreshed controls
        const allValidControlIds = new Set()
        filteredTree.forEach(group => {
          if (group.children) {
            group.children.forEach(control => {
              if (control.type === 'control' && control.id) {
                allValidControlIds.add(Number(control.id))
              }
            })
          }
        })
        
        // Filter selected controls to only include those that still exist
        const validSelectedControls = controlsToSave.filter(id => {
          const isValid = allValidControlIds.has(id)
          if (!isValid) {
            console.warn('[Onboarding] Control ID no longer valid after refresh:', id)
          }
          return isValid
        })
        
        // Update controlsToSave with validated IDs
        if (validSelectedControls.length !== controlsToSave.length) {
          console.warn('[Onboarding] Some selected controls are no longer valid after refresh')
          console.warn('[Onboarding] Original count:', controlsToSave.length, 'Valid count:', validSelectedControls.length)
          
          // If we lost all controls, clear selection and ask user to reselect
          if (validSelectedControls.length === 0 && controlsToSave.length > 0) {
            alert('Selected controls are no longer valid. This may happen if controls were recreated. Please reselect controls.')
            setSelectedControls([])
            setLoading(false)
            return
          }
          
          // Update to use only valid controls
          controlsToSave.length = 0
          controlsToSave.push(...validSelectedControls)
          setSelectedControls(validSelectedControls)
          console.log('[Onboarding] Updated selectedControls to valid IDs:', validSelectedControls)
        }
      } catch (err) {
        // Framework might already exist, that's okay - continue
        console.log('[Onboarding] Framework seeding check:', err.response?.data || 'Framework may already exist')
        
        // Still try to get framework ID if we don't have it
        if (!iso27001FrameworkId) {
          try {
            const controlsResponse = await api.get('/frameworks/iso27001/control-tree')
            setIso27001FrameworkId(controlsResponse.data.framework_id)
            console.log('[Onboarding] Framework ID set from control-tree:', controlsResponse.data.framework_id)
          } catch (e) {
            console.error('[Onboarding] Could not fetch framework ID:', e)
          }
        }
      }
      
      // controlsToSave is already normalized above, use it directly
      const normalizedControls = controlsToSave
      
      // PART 1: Add console log before API call
      console.log('[Onboarding] ===== SENDING TO API =====')
      console.log('[Onboarding] Normalized control IDs:', normalizedControls)
      console.log('[Onboarding] Framework ID:', iso27001FrameworkId)
      console.log('[Onboarding] Controls count:', normalizedControls.length)
      
      // PART 1: Build payload with framework_id and controls as numbers
      const payload = {
        framework_id: iso27001FrameworkId || null,  // Use framework_id if available
        framework: 'ISO27001',  // Fallback framework name
        controls: normalizedControls  // Array of control IDs as numbers
      }
      
      console.log('[Onboarding] Sending payload to API:', payload)
      const response = await api.post('/onboarding/controls/selection', payload)
      console.log('[Onboarding] API Response:', response)
      console.log('[Onboarding] Response data:', response.data)
      
      // Verify response is successful - axios automatically throws for non-2xx, so if we get here, it's successful
      // Mark controls as saved - this allows progression to next step
      setControlsSaved(true)
      console.log('[Onboarding] ✅ Set controlsSaved to true')
      console.log('[Onboarding] ✅ controlsSaved state updated, user can now proceed')
      
      // Show success message from backend
      const controlsCount = response.data?.controls_count || 0
      const successMessage = response.data?.message || `Successfully saved ${controlsCount} control(s)!`
      
      console.log('[Onboarding] Success message:', successMessage)
      console.log('[Onboarding] Controls count from backend:', controlsCount)
      console.log('[Onboarding] Selected controls count:', normalizedControls.length)
      
      if (controlsCount > 0) {
        // Check if some controls were filtered out
        if (normalizedControls.length > controlsCount) {
          alert(`${successMessage}\n\nNote: ${normalizedControls.length - controlsCount} control(s) were invalid and not saved.\n\n${controlsCount} valid control(s) saved. You can now proceed to the next step.`)
        } else {
          alert(`${successMessage}\n\nYou can now proceed to the next step.`)
        }
      } else {
        alert('No valid controls were saved. Please select valid controls and try again.')
        setControlsSaved(false)
        return
      }
    } catch (err) {
      console.error('[Onboarding] ❌ Error saving controls:', err)
      console.error('[Onboarding] Error response:', err.response)
      console.error('[Onboarding] Error data:', err.response?.data)
      
      // Mark as not saved on error
      setControlsSaved(false)
      
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to save controls. Please try again.'
      
      // If error mentions mapping issues, provide helpful message
      if (errorMsg.includes('not mapped correctly') || errorMsg.includes('contact admin')) {
        alert(`${errorMsg}\n\nThis usually means the control mappings need to be fixed. Please contact support or try refreshing the page.`)
        // Refresh controls to get latest IDs
        await fetchISO27001Controls()
      } else if (errorMsg.includes('do not exist') || errorMsg.includes('Missing IDs') || errorMsg.includes('Invalid control IDs')) {
        alert(`${errorMsg}\n\nPlease refresh the page and reselect controls.`)
        // Refresh controls
        await fetchISO27001Controls()
        setSelectedControls([])
      } else {
        alert(`Error: ${errorMsg}\n\nPlease check the console for more details.`)
      }
    } finally {
      setLoading(false)
    }
  }

  const fetchStatus = async () => {
    try {
      const response = await api.get('/onboarding/status')
      setStatus(response.data)
      if (response.data.current_step === 'completed') {
        navigate('/dashboard')
      }
    } catch (err) {
      console.error('Error fetching status:', err)
    }
  }


  const handleNext = async () => {
    setLoading(true)
    try {
      switch (currentStep) {
        case 0:
          // Validate required fields for Company Details
          if (!companyData.name || !companyData.name.trim()) {
            alert('Company Name is required')
            setLoading(false)
            return
          }
          if (!companyData.industry || !companyData.industry.trim()) {
            alert('Industry is required')
            setLoading(false)
            return
          }
          
          // Send all company data fields
          const companyUpdateData = {
            name: companyData.name,
            domain: companyData.domain || null,
            industry: companyData.industry,
            size: companyData.size || null
          }
          
          console.log('[Onboarding] Sending company data:', companyUpdateData)
          const response = await api.post('/onboarding/company', companyUpdateData)
          console.log('[Onboarding] Company update response:', response.data)
          break
        case 1:
          await api.post('/onboarding/departments', departments)
          break
        case 2:
          await api.post('/onboarding/roles', roles)
          break
        case 3:
          await api.post('/onboarding/frameworks', frameworks)
          break
        case 4:
          // Check if ISO 27001 is selected
          if (selectedFrameworks.includes('ISO 27001')) {
            // Ensure ISO 27001 framework is seeded first
            try {
              await api.post('/frameworks/seed/iso27001')
            } catch (err) {
              // Framework might already exist, that's okay
              console.log('Framework seeding:', err.response?.data || 'Framework may already exist')
            }
            
            // Check if controls are saved - if controlsSaved is true, allow proceeding
            console.log('[Onboarding] Step 4 - Checking controls saved status:')
            console.log('  - controlsSaved:', controlsSaved)
            console.log('  - selectedControls.length:', selectedControls.length)
            console.log('  - selectedControls:', selectedControls)
            
            // FIX: If controls are selected but not saved, automatically save them
            if (!controlsSaved && selectedControls.length > 0) {
              console.log('[Onboarding] Controls selected but not saved - auto-saving...')
              try {
                // Auto-save the selected controls
                const controlsToSave = [...selectedControls]
                const normalizedControls = controlsToSave.map(id => Number(id)).filter(id => !isNaN(id) && id > 0)
                
                if (normalizedControls.length === 0) {
                  alert('Please select valid controls before proceeding.')
                  setLoading(false)
                  return
                }
                
                const payload = {
                  framework_id: iso27001FrameworkId || null,
                  framework: 'ISO27001',
                  controls: normalizedControls
                }
                
                console.log('[Onboarding] Auto-saving controls:', payload)
                const saveResponse = await api.post('/onboarding/controls/selection', payload)
                console.log('[Onboarding] Auto-save response:', saveResponse.data)
                
                // Mark as saved
                setControlsSaved(true)
                console.log('[Onboarding] ✅ Auto-saved controls, set controlsSaved to true')
              } catch (saveErr) {
                console.error('[Onboarding] ❌ Auto-save failed:', saveErr)
                const errorMsg = saveErr.response?.data?.detail || saveErr.message || 'Failed to save controls'
                alert(`Error saving controls: ${errorMsg}\n\nPlease click "Save Selected Controls" button and try again.`)
                setLoading(false)
                return
              }
            } else if (!controlsSaved && selectedControls.length === 0) {
              // No controls selected and not saved
              alert('Please select and save at least one control before proceeding.')
              setLoading(false)
              return
            }
            
            // If we get here, controls are saved (either already saved or just auto-saved)
            console.log('[Onboarding] ✅ Controls are saved, allowing progression to next step')
          }
          break
        case 5:
          // Policies step - optional, can proceed without uploading
          // Policies are already uploaded via the upload button
          break
        case 6:
          // Completion screen - navigate to dashboard
          navigate('/dashboard')
          return
      }
      
      // Only advance to next step if no errors occurred
      console.log('[Onboarding] Step completed successfully, advancing from step', currentStep)
      if (currentStep < steps.length - 1) {
        const nextStep = currentStep + 1
        console.log('[Onboarding] Moving to step', nextStep)
        setCurrentStep(nextStep)
      }
      await fetchStatus()
    } catch (err) {
      console.error('[Onboarding] Error in handleNext:', err)
      console.error('[Onboarding] Error response:', err.response)
      console.error('[Onboarding] Error data:', err.response?.data)
      const errorMessage = err.response?.data?.detail || err.response?.data?.message || err.message || 'An error occurred. Please try again.'
      alert(`Error: ${errorMessage}`)
      // Don't advance step on error - stay on current step
      setLoading(false)
      return
    } finally {
      setLoading(false)
    }
  }

  const addDepartment = () => setDepartments([...departments, { name: '', description: '' }])
  const addRole = () => setRoles([...roles, { name: '', description: '', permissions: '' }])
  const addFramework = () => setFrameworks([...frameworks, { name: '', description: '', version: '', category: '' }])

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files)
    if (files.length === 0) return
    
    handleFileUpload(files)
    // Reset file input
    e.target.value = ''
  }

  const handleFileUpload = async (files) => {
    setUploading(true)
    try {
      const policiesToUpload = []
      
      for (const file of files) {
        // Read file content
        const content = await readFileContent(file)
        
        // Extract filename without extension as title
        const fileName = file.name.replace(/\.[^/.]+$/, '')
        
        policiesToUpload.push({
          title: fileName,
          description: `Uploaded policy: ${file.name}`,
          content: content,
          policy_number: null,
          version: '1.0',
          framework_id: null,
          control_id: null
        })
      }
      
      // Upload policies to backend
      const response = await api.post('/onboarding/policies/upload', policiesToUpload)
      setUploadedPolicies([...uploadedPolicies, ...response.data])
      
      alert(`Successfully uploaded ${files.length} policy file(s)!`)
    } catch (err) {
      console.error('Error uploading policies:', err)
      alert(err.response?.data?.detail || 'Failed to upload policies. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  const readFileContent = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      
      reader.onload = (e) => {
        const content = e.target.result
        resolve(content)
      }
      
      reader.onerror = (e) => {
        reject(new Error(`Failed to read file: ${file.name}`))
      }
      
      // For PDF and DOCX files, we can't extract text content directly in the browser
      // Show a note that these files will be uploaded but content extraction may be limited
      if (file.type === 'application/pdf' || file.type.includes('word') || file.type.includes('document')) {
        // For binary files, we'll store a note that content needs server-side processing
        resolve(`[Note: ${file.name} uploaded. Full text extraction requires server-side processing. The file has been uploaded and can be processed later.]`)
      } else {
        // Read text files normally
        reader.readAsText(file)
      }
    })
  }

  const triggerFileInput = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click()
    }
  }

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Company Name *</label>
              <Input
                value={companyData.name}
                onChange={(e) => setCompanyData({ ...companyData, name: e.target.value })}
                placeholder="Acme Inc."
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Company Domain</label>
              <Input
                value={companyData.domain}
                onChange={(e) => setCompanyData({ ...companyData, domain: e.target.value })}
                placeholder="example.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Industry *</label>
              <select
                value={companyData.industry}
                onChange={(e) => setCompanyData({ ...companyData, industry: e.target.value })}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                required
              >
                <option value="">Select Industry</option>
                <option value="BFSI">BFSI</option>
                <option value="TELECOM">TELECOM</option>
                <option value="HEALTHCARE">HEALTHCARE</option>
                <option value="MANUFACTURING">MANUFACTURING</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Company Size</label>
              <select
                value={companyData.size}
                onChange={(e) => setCompanyData({ ...companyData, size: e.target.value })}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Select size</option>
                <option value="1–50">1–50</option>
                <option value="50–200">50–200</option>
                <option value="200–500">200–500</option>
                <option value="500+">500+</option>
              </select>
            </div>
          </div>
        )
      case 1:
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Select Department</label>
              <select
                value={selectedDepartment}
                onChange={(e) => {
                  setSelectedDepartment(e.target.value)
                  if (e.target.value && departments.length === 0) {
                    setDepartments([{ name: e.target.value, description: '' }])
                  } else if (e.target.value && departments[0].name !== e.target.value) {
                    setDepartments([{ name: e.target.value, description: '' }])
                  }
                }}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Choose Department</option>
                <option value="HR">HR</option>
                <option value="IT">IT</option>
                <option value="SECURITY">SECURITY</option>
                <option value="OPERATIONS">OPERATIONS</option>
                <option value="FINANCE">FINANCE</option>
                <option value="LEGAL">LEGAL</option>
              </select>
            </div>
            {departments.map((dept, idx) => (
              <div key={idx} className="border p-4 rounded-md">
                <Input
                  placeholder="Department Name"
                  value={dept.name}
                  onChange={(e) => {
                    const newDepts = [...departments]
                    newDepts[idx].name = e.target.value
                    setDepartments(newDepts)
                  }}
                  className="mb-2"
                />
                <Input
                  placeholder="Description"
                  value={dept.description}
                  onChange={(e) => {
                    const newDepts = [...departments]
                    newDepts[idx].description = e.target.value
                    setDepartments(newDepts)
                  }}
                />
              </div>
            ))}
            <Button type="button" variant="outline" onClick={addDepartment}>Add Department</Button>
          </div>
        )
      case 2:
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Select Role</label>
              <select
                value={selectedRole}
                onChange={(e) => {
                  setSelectedRole(e.target.value)
                  if (e.target.value && roles.length === 0) {
                    setRoles([{ name: e.target.value, description: '', permissions: '' }])
                  } else if (e.target.value && roles[0].name !== e.target.value) {
                    setRoles([{ name: e.target.value, description: '', permissions: '' }])
                  }
                }}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Choose Role</option>
                <option value="Org Admin">Org Admin</option>
                <option value="Compliance Manager">Compliance Manager</option>
                <option value="Department Manager">Department Manager</option>
                <option value="Auditor">Auditor</option>
                <option value="Contributor">Contributor</option>
              </select>
            </div>
            {roles.map((role, idx) => (
              <div key={idx} className="border p-4 rounded-md">
                <Input
                  placeholder="Role Name"
                  value={role.name}
                  onChange={(e) => {
                    const newRoles = [...roles]
                    newRoles[idx].name = e.target.value
                    setRoles(newRoles)
                  }}
                  className="mb-2"
                />
                <Input
                  placeholder="Description"
                  value={role.description}
                  onChange={(e) => {
                    const newRoles = [...roles]
                    newRoles[idx].description = e.target.value
                    setRoles(newRoles)
                  }}
                />
              </div>
            ))}
            <Button type="button" variant="outline" onClick={addRole}>Add Role</Button>
          </div>
        )
      case 3:
        const frameworkOptions = ["ISO 27001", "SOC 2 Type II", "DPDP", "GDPR", "HIPAA", "PCI DSS", "ISO 9001"]
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Select Frameworks</label>
              <select
                multiple
                value={selectedFrameworks}
                onChange={(e) => {
                  const selected = Array.from(e.target.selectedOptions, option => option.value)
                  setSelectedFrameworks(selected)
                  setFrameworks(selected.map(name => ({ name, description: '', version: '', category: '' })))
                }}
                className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                size={7}
              >
                {frameworkOptions.map((fw) => (
                  <option key={fw} value={fw}>{fw}</option>
                ))}
              </select>
              <p className="text-xs text-muted-foreground mt-1">Hold Ctrl (or Cmd on Mac) to select multiple</p>
            </div>
            {frameworks.map((fw, idx) => (
              <div key={idx} className="border p-4 rounded-md">
                <Input
                  placeholder="Framework Name"
                  value={fw.name}
                  onChange={(e) => {
                    const newFws = [...frameworks]
                    newFws[idx].name = e.target.value
                    setFrameworks(newFws)
                  }}
                  className="mb-2"
                />
                <Input
                  placeholder="Description"
                  value={fw.description}
                  onChange={(e) => {
                    const newFws = [...frameworks]
                    newFws[idx].description = e.target.value
                    setFrameworks(newFws)
                  }}
                />
              </div>
            ))}
            <Button type="button" variant="outline" onClick={addFramework}>Add Framework</Button>
          </div>
        )
      case 4:
        // Check if ISO 27001 was selected
        const hasISO27001 = selectedFrameworks.includes('ISO 27001')
        
        return (
          <div className="space-y-4">
            <div className="text-center mb-6">
              <p className="text-lg mb-2 font-semibold">Framework Controls (ISO 27001, SOC 2, etc.)</p>
              {hasISO27001 ? (
                <p className="text-muted-foreground text-sm">Select controls from ISO 27001:2022 framework groups A.5, A.6, A.7, A.8</p>
              ) : (
                <p className="text-muted-foreground text-sm">Framework controls will be configured based on your selected frameworks</p>
              )}
            </div>
            {hasISO27001 && (
              <div className="space-y-4">
                <h3 className="font-medium text-base mb-3">ISO 27001 Explorer</h3>
                {loadingControls ? (
                  <div className="text-center py-8">
                    <p className="text-muted-foreground">Loading controls...</p>
                  </div>
                ) : iso27001Controls.length > 0 ? (
                  <>
                    {iso27001Controls.map((group) => (
                      <div key={group.id} className="border rounded-lg overflow-hidden">
                        <button
                          type="button"
                          onClick={() => setExpandedCategories({
                            ...expandedCategories,
                            [group.id]: !expandedCategories[group.id]
                          })}
                          className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
                        >
                          <span className="font-medium">{group.code} - {group.name}</span>
                          <span className="text-gray-500">
                            {expandedCategories[group.id] ? '▼' : '▶'}
                          </span>
                        </button>
                        {expandedCategories[group.id] && (
                          <div className="p-4 border-t bg-white">
                            {group.children && group.children.length > 0 ? (
                              <div className="space-y-2">
                                {group.children.map((control) => {
                                  // Ensure we only use controls (type === "control"), not groups
                                  if (control.type !== 'control') {
                                    return null
                                  }
                                  // PART 1: Ensure we use the REAL database ID (control.id)
                                  // Convert to number to ensure it's a valid ID
                                  const controlId = typeof control.id === 'string' ? parseInt(control.id, 10) : Number(control.id)
                                  
                                  // Skip if control ID is invalid
                                  if (isNaN(controlId) || controlId <= 0) {
                                    console.warn('[Onboarding] Invalid control ID:', control.id, control)
                                    return null
                                  }
                                  
                                  return (
                                    <div key={control.id} className="flex items-start space-x-3 p-2 hover:bg-gray-50 rounded">
                                      <input
                                        type="checkbox"
                                        value={controlId}  // Use normalized controlId (number)
                                        checked={selectedControls.includes(controlId)}
                                        onChange={(e) => {
                                          console.log('[Onboarding] Checkbox changed:', {
                                            controlId,
                                            controlCode: control.code,
                                            checked: e.target.checked,
                                            currentSelected: selectedControls.length
                                          })
                                          handleControlToggle(controlId)
                                        }}
                                        className="mt-1 h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
                                      />
                                      <div className="flex-1">
                                        <label className="text-sm font-medium cursor-pointer" onClick={() => handleControlToggle(controlId)}>
                                          {control.code} - {control.name}
                                        </label>
                                        {control.description && (
                                          <p className="text-xs text-muted-foreground mt-1">{control.description}</p>
                                        )}
                                      </div>
                                    </div>
                                  )
                                })}
                              </div>
                            ) : (
                              <p className="text-sm text-muted-foreground">No controls available in this group.</p>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                    <div className="flex items-center justify-between pt-4 border-t">
                      <p className="text-sm text-muted-foreground">
                        {selectedControls.length} control(s) selected
                      </p>
                      <Button
                        type="button"
                        onClick={handleSaveControls}
                        disabled={loading || selectedControls.length === 0}
                        className="px-6"
                      >
                        {loading ? 'Saving...' : 'Save Selected Controls'}
                      </Button>
                    </div>
                    {controlsSaved && (
                      <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                        <p className="text-sm text-green-800">✓ Controls saved successfully!</p>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-center py-8 border rounded-lg bg-yellow-50">
                    <p className="text-muted-foreground">
                      No controls found. Please ensure ISO 27001 framework is seeded.
                    </p>
                  </div>
                )}
              </div>
            )}
            {!hasISO27001 && selectedFrameworks.length > 0 && (
              <div className="text-center py-8 border rounded-lg bg-gray-50">
                <p className="text-muted-foreground">
                  Controls for {selectedFrameworks.join(', ')} will be configured when you proceed.
                </p>
              </div>
            )}
            {selectedFrameworks.length === 0 && (
              <div className="text-center py-8 border rounded-lg bg-yellow-50">
                <p className="text-muted-foreground">
                  Please select frameworks in the previous step to configure controls.
                </p>
              </div>
            )}
          </div>
        )
      case 5:
        return (
          <div className="text-center py-8">
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.doc,.docx,.txt"
              onChange={handleFileSelect}
              className="hidden"
            />
            <div className="mb-6">
              <Button
                type="button"
                onClick={triggerFileInput}
                disabled={uploading}
                className="px-8 py-6 text-base font-semibold bg-primary hover:bg-primary/90 rounded-lg shadow-md hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploading ? 'Uploading...' : 'Upload Policies'}
              </Button>
            </div>
            {uploadedPolicies.length > 0 && (
              <div className="mt-6 text-left max-w-2xl mx-auto">
                <p className="text-sm font-medium mb-2">Uploaded Policies ({uploadedPolicies.length}):</p>
                <div className="space-y-2">
                  {uploadedPolicies.map((policy, idx) => (
                    <div key={policy.id || idx} className="p-3 bg-green-50 border border-green-200 rounded-lg">
                      <p className="text-sm font-medium text-green-800">{policy.title}</p>
                      {policy.policy_number && (
                        <p className="text-xs text-green-600">Policy #: {policy.policy_number}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
            <p className="text-muted-foreground text-sm mt-4">
               Supported formats: PDF, DOC, DOCX, TXT
            </p>
          </div>
        )
      case 6:
        return (
          <div className="text-center py-8">
            <CheckCircle2 className="h-16 w-16 text-green-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">Onboarding Complete!</h2>
            <p className="text-muted-foreground mb-6">You're all set to start using SANCHALAN.</p>
            <Button
              onClick={() => navigate('/dashboard')}
              className="px-6 py-2"
            >
              Go to Dashboard
            </Button>
          </div>
        )
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <Card className="shadow-xl border-0 rounded-2xl overflow-hidden">
          <CardHeader className="bg-gradient-to-r from-primary/10 to-primary/5 border-b">
            <CardTitle className="text-2xl font-bold">Onboarding Wizard</CardTitle>
          </CardHeader>
          <CardContent className="p-8">
            <div className="mb-8">
              <div className="flex items-center justify-between mb-6 overflow-x-auto pb-4">
                {steps.map((step, idx) => {
                  const Icon = step.icon
                  return (
                    <div key={idx} className="flex items-center flex-1 min-w-[120px]">
                      <div className="flex flex-col items-center">
                        <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all ${
                          idx < currentStep 
                            ? 'bg-primary border-primary text-white' 
                            : idx === currentStep
                            ? 'bg-primary/10 border-primary text-primary'
                            : 'bg-gray-100 border-gray-300 text-gray-400'
                        }`}>
                          {idx < currentStep ? (
                            <CheckCircle2 className="h-5 w-5" />
                          ) : (
                            <Icon className="h-5 w-5" />
                          )}
                        </div>
                        <span className={`mt-2 text-xs text-center ${idx <= currentStep ? 'text-primary font-semibold' : 'text-gray-400'}`}>
                          {step.name}
                        </span>
                      </div>
                      {idx < steps.length - 1 && (
                        <div className={`flex-1 h-0.5 mx-2 mt-[-20px] ${idx < currentStep ? 'bg-primary' : 'bg-gray-200'}`} />
                      )}
                    </div>
                  )
                })}
              </div>
              {status && (
                <div className="text-center">
                  <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                    <div 
                      className="bg-primary h-2 rounded-full transition-all duration-300"
                      style={{ width: `${status.completion_percentage}%` }}
                    />
                  </div>
                  <p className="text-sm text-muted-foreground font-medium">
                    Progress: {status.completion_percentage}%
                  </p>
                </div>
              )}
            </div>
            <div className="min-h-[400px] bg-white rounded-lg p-6 shadow-sm">
              {renderStep()}
            </div>
            <div className="flex justify-between mt-8 pt-6 border-t">
              <Button
                variant="outline"
                onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
                disabled={currentStep === 0 || loading}
                className="rounded-lg px-6"
              >
                Previous
              </Button>
              <Button 
                type="button"
                onClick={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  console.log('[Onboarding] Next button clicked, current step:', currentStep, 'loading:', loading)
                  handleNext()
                }} 
                disabled={loading}
                className="rounded-lg px-6 bg-primary hover:bg-primary/90"
              >
                {loading ? 'Loading...' : currentStep === steps.length - 1 ? 'Finish' : 'Next'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
