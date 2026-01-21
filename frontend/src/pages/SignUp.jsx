import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { authService } from '@/lib/auth'

export default function SignUp() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirm_password: '',
    first_name: '',
    last_name: '',
    phone: '',
    company_name: '',
    company_domain: '',
    company_industry: '',
    company_size: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    // Validate password confirmation
    if (formData.password !== formData.confirm_password) {
      setError('Passwords do not match')
      setLoading(false)
      return
    }

    try {
      await authService.signup(formData)
      navigate('/signin')
    } catch (err) {
      console.error('Signup error:', err)
      const errorMessage = err.response?.data?.detail || err.message || 'Sign up failed. Please try again.'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 py-12 px-4">
      <Card className="w-full max-w-2xl shadow-xl border-0 rounded-2xl overflow-hidden">
        <CardHeader className="bg-gradient-to-r from-primary/10 to-primary/5 border-b">
          <CardTitle className="text-2xl font-bold">Create Account</CardTitle>
          <CardDescription className="text-base">Sign up to get started with SANCHALAN</CardDescription>
        </CardHeader>
        <CardContent className="p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="p-4 text-sm text-red-600 bg-red-50 rounded-lg border border-red-200">
                {error}
              </div>
            )}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">First Name</label>
                <Input
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleChange}
                  placeholder="John"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Last Name</label>
                <Input
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  placeholder="Doe"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Email *</label>
              <Input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Password *</label>
              <Input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                required
                placeholder="••••••••"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Confirm Password *</label>
              <Input
                type="password"
                name="confirm_password"
                value={formData.confirm_password}
                onChange={handleChange}
                required
                placeholder="••••••••"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Company Name *</label>
              <Input
                name="company_name"
                value={formData.company_name}
                onChange={handleChange}
                required
                placeholder="Enter company name or join existing company"
              />
              <p className="text-xs text-muted-foreground mt-1">
                If the company exists, you'll join it. Otherwise, a new company will be created.
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Industry *</label>
              <select
                name="company_industry"
                value={formData.company_industry}
                onChange={handleChange}
                required
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Select Industry</option>
                <option value="BFSI">BFSI</option>
                <option value="TELECOM">TELECOM</option>
                <option value="HEALTHCARE">HEALTHCARE</option>
                <option value="MANUFACTURING">MANUFACTURING</option>
              </select>
            </div>
            <Button type="submit" className="w-full rounded-lg py-6 text-base font-semibold bg-primary hover:bg-primary/90" disabled={loading}>
              {loading ? 'Creating account...' : 'Sign Up'}
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              Already have an account?{' '}
              <Link to="/signin" className="text-primary hover:underline font-medium">
                Sign in
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
