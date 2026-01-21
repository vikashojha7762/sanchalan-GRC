import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { authService } from '@/lib/auth'

export default function SignIn() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [industry, setIndustry] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const industryOptions = [
    { value: 'BFSI', label: 'BFSI' },
    { value: 'TELECOM', label: 'TELECOM' },
    { value: 'HEALTHCARE', label: 'HEALTHCARE' },
    { value: 'MANUFACTURING', label: 'MANUFACTURING' }
  ]

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    if (!industry) {
      setError('Please select an industry')
      setLoading(false)
      return
    }

    try {
      await authService.login(email, password, industry)
      navigate('/onboarding')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 py-12 px-4">
      <Card className="w-full max-w-md shadow-xl border-0 rounded-2xl overflow-hidden">
        <CardHeader className="bg-gradient-to-r from-primary/10 to-primary/5 border-b">
          <CardTitle className="text-2xl font-bold">Sign In</CardTitle>
          <CardDescription className="text-base">Enter your credentials to access SANCHALAN</CardDescription>
        </CardHeader>
        <CardContent className="p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="p-4 text-sm text-red-600 bg-red-50 rounded-lg border border-red-200">
                {error}
              </div>
            )}
            <div>
              <label className="block text-sm font-medium mb-1">Email</label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Password</label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="••••••••"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Select Industry *</label>
              <select
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                required
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">Choose Industry</option>
                {industryOptions.map((ind) => (
                  <option key={ind.value} value={ind.value}>
                    {ind.label}
                  </option>
                ))}
              </select>
            </div>
            <Button type="submit" className="w-full rounded-lg py-6 text-base font-semibold bg-primary hover:bg-primary/90" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              Don't have an account?{' '}
              <Link to="/signup" className="text-primary hover:underline font-medium">
                Sign up
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
