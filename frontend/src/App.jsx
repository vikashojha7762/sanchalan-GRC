import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { authService } from './lib/auth'
import SignIn from './pages/SignIn'
import SignUp from './pages/SignUp'
import Onboarding from './pages/Onboarding'
import Dashboard from './pages/Dashboard'
import GapManagement from './pages/GapManagement'
import ArtifactUpload from './pages/ArtifactUpload'
import Approvals from './pages/Approvals'
import ChatAssistant from './pages/ChatAssistant'
import GapAnalysis from './pages/GapAnalysis'
import RiskGapReport from './pages/RiskGapReport'
import KnowledgeBase from './pages/KnowledgeBase'
import Layout from './components/Layout'

function PrivateRoute({ children }) {
  return authService.isAuthenticated() ? children : <Navigate to="/signin" />
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/signin" element={<SignIn />} />
        <Route path="/signup" element={<SignUp />} />
        <Route
          path="/onboarding"
          element={
            <PrivateRoute>
              <Onboarding />
            </PrivateRoute>
          }
        />
        <Route
          path="/dashboard"
          element={
            <PrivateRoute>
              <Layout>
                <Dashboard />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/gaps"
          element={
            <PrivateRoute>
              <Layout>
                <GapManagement />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/artifacts"
          element={
            <PrivateRoute>
              <Layout>
                <ArtifactUpload />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/approvals"
          element={
            <PrivateRoute>
              <Layout>
                <Approvals />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/chat"
          element={
            <PrivateRoute>
              <Layout>
                <ChatAssistant />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/gap-analysis"
          element={
            <PrivateRoute>
              <Layout>
                <GapAnalysis />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/reports/risk-gap"
          element={
            <PrivateRoute>
              <Layout>
                <RiskGapReport />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route
          path="/knowledge-base"
          element={
            <PrivateRoute>
              <Layout>
                <KnowledgeBase />
              </Layout>
            </PrivateRoute>
          }
        />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
