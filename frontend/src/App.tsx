import { Routes, Route } from 'react-router-dom'
import { AppShell } from '@/components/layout/app-shell'
import { LandingPage } from '@/pages/landing'
import { ScannerPage } from '@/pages/scanner'
import { CollectionsPage } from '@/pages/collections'
import { ProductPage } from '@/pages/product'
import { CheckoutPage } from '@/pages/checkout'
import { AnalyticsPage } from '@/pages/analytics'
import { AdminPage } from '@/pages/admin'
import { ProfilePage } from '@/pages/profile'
import { OrdersPage } from '@/pages/orders'

import { RequireAuth } from '@/components/auth/require-auth'

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<LandingPage />} />
        <Route path="scanner" element={<ScannerPage />} />
        <Route path="collections" element={<CollectionsPage />} />
        <Route path="product/:id" element={<ProductPage />} />
        <Route path="checkout" element={<RequireAuth><CheckoutPage /></RequireAuth>} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="admin" element={<RequireAuth adminOnly><AdminPage /></RequireAuth>} />
        <Route path="profile" element={<RequireAuth><ProfilePage /></RequireAuth>} />
        <Route path="orders" element={<RequireAuth><OrdersPage /></RequireAuth>} />
        <Route path="*" element={<LandingPage />} />
      </Route>
    </Routes>
  )
}