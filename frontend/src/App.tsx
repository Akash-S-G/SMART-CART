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

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<LandingPage />} />
        <Route path="scanner" element={<ScannerPage />} />
        <Route path="collections" element={<CollectionsPage />} />
        <Route path="product/:id" element={<ProductPage />} />
        <Route path="checkout" element={<CheckoutPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="admin" element={<AdminPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="orders" element={<OrdersPage />} />
        <Route path="*" element={<LandingPage />} />
      </Route>
    </Routes>
  )
}