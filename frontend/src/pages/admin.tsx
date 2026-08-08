import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  ShieldAlert,
  Plus,
  Boxes,
  Users,
  ScrollText,
  AlertTriangle,
  CheckCircle2,
  Trash2,
  RefreshCw,
  Search,
  Download,
  FileSpreadsheet,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { useAuth } from '@/hooks/use-auth'
import { getCategoriesApi, listProductsApi, createProductApi, getRealCustomersApi, getRealLogsApi } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'

export function AdminPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const [activeTab, setActiveTab] = useState<'inventory' | 'customers' | 'logs'>('inventory')
  const [showAddModal, setShowAddModal] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  const exportInventoryCSV = () => {
    if (!products?.length) {
      toast({ title: 'No Data', description: 'Inventory catalog is empty.' })
      return
    }
    const headers = ['Product ID', 'Name', 'SKU', 'Barcode', 'Stock', 'Price (INR)', 'Status']
    const rows = products.map((p) => [
      p.id,
      `"${p.name.replace(/"/g, '""')}"`,
      p.sku || '',
      p.barcode || '',
      p.stock ?? 0,
      p.price ?? 0,
      (p.stock || 0) < 20 ? 'Low Stock' : 'Optimal',
    ])
    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `smartcart_inventory_report_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
    toast({ title: 'Inventory Report Exported', description: 'Downloaded CSV inventory report.' })
  }

  const exportAuditLogCSV = () => {
    const headers = ['Event ID', 'Action', 'Detail', 'User', 'Timestamp', 'Severity']
    const rows = logs.map((l) => [
      l.id,
      l.action,
      `"${l.detail.replace(/"/g, '""')}"`,
      l.user,
      `"${l.time}"`,
      l.severity,
    ])
    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `smartcart_audit_report_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
    toast({ title: 'Audit Report Exported', description: 'Downloaded CSV audit log report.' })
  }

  // Form state for creating a product
  const [formData, setFormData] = useState({
    name: '',
    sku: '',
    barcode: '',
    brand: '',
    description: '',
    category_id: '',
    initial_stock: 50,
    price: 0,
    image_url: '',
  })

  // Queries
  const { data: categories } = useQuery({
    queryKey: ['admin-categories'],
    queryFn: getCategoriesApi,
  })

  const { data: products, isLoading } = useQuery({
    queryKey: ['admin-products'],
    queryFn: () => listProductsApi(0, 100),
  })

  // Mutation to add product
  const addProductMutation = useMutation({
    mutationFn: (body: typeof formData) => createProductApi(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-products'] })
      queryClient.invalidateQueries({ queryKey: ['products'] })
      queryClient.invalidateQueries({ queryKey: ['featured-products'] })
      toast({
        title: 'Product Created',
        description: 'Successfully registered product in the catalog database.',
      })
      setShowAddModal(false)
      setFormData({
        name: '',
        sku: '',
        barcode: '',
        brand: '',
        description: '',
        category_id: '',
        initial_stock: 50,
        price: 0,
        image_url: '',
      })
    },
    onError: (err: any) => {
      toast({
        title: 'Creation Failed',
        description: err.message || 'Check SKU/Barcode uniqueness or fields.',
        variant: 'destructive',
      })
    },
  })

  // Security check: Only allow admins
  if (user?.role !== 'admin') {
    return (
      <div className="mx-auto max-w-md px-6 py-24 text-center flex flex-col items-center justify-center gap-6">
        <div className="w-16 h-16 bg-destructive/10 text-destructive rounded-full flex items-center justify-center shadow-sm">
          <ShieldAlert className="h-6 w-6" />
        </div>
        <h2 className="text-2xl font-bold text-foreground">Access Denied</h2>
        <p className="text-sm text-muted-foreground leading-relaxed">
          This panel is restricted to system administrators only. Please authenticate with administrative privileges to continue.
        </p>
        <Button variant="secondary" className="w-full rounded-xl py-6" onClick={() => navigate('/')}>
          Return Home
        </Button>
      </div>
    )
  }

  const handleAddSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.name || !formData.sku || !formData.category_id) {
      toast({
        title: 'Invalid Fields',
        description: 'Please specify name, SKU, and category.',
        variant: 'destructive',
      })
      return
    }
    addProductMutation.mutate(formData)
  }

  // Pre-fill fields for speed demo
  const generateRandomSKU = () => {
    const randomNum = Math.floor(1000 + Math.random() * 9000)
    setFormData((prev) => ({
      ...prev,
      sku: `SC-ADM-${randomNum}`,
      barcode: `890${randomNum}${Math.floor(100000 + Math.random() * 900000)}`,
    }))
  }

  const { data: customers = [] } = useQuery({
    queryKey: ['admin-customers'],
    queryFn: getRealCustomersApi,
  })

  const { data: logs = [] } = useQuery({
    queryKey: ['admin-logs'],
    queryFn: getRealLogsApi,
  })

  return (
    <div className="mx-auto max-w-7xl px-6 py-10">
      <div className="flex justify-between items-center flex-wrap gap-4 border-b pb-6">
        <div>
          <h1 className="text-3xl font-sans font-extrabold text-foreground">Admin Console</h1>
          <p className="text-xs text-muted-foreground mt-1">Supervise inventory stock parameters, client profiles, and system audit logs.</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" className="rounded-xl font-semibold uppercase text-xs tracking-widest py-5 px-4 gap-2 border-border" onClick={exportInventoryCSV}>
            <FileSpreadsheet className="h-4 w-4 text-emerald-600" /> Export Inventory CSV
          </Button>
          <Button variant="gradient" className="rounded-xl font-semibold uppercase text-xs tracking-widest py-5 px-5 gap-2" onClick={() => setShowAddModal(true)}>
            <Plus className="h-4 w-4" /> Add New Product
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="mt-8 flex justify-between items-center flex-wrap gap-4 border-b border-black/[0.04] pb-4">
        <div className="flex gap-3">
          <button
            onClick={() => setActiveTab('inventory')}
            className={`flex items-center gap-2 text-xs font-bold uppercase tracking-wider px-4 py-2.5 rounded-xl transition ${
              activeTab === 'inventory' ? 'bg-primary text-primary-foreground shadow-sm' : 'text-muted-foreground hover:bg-black/[0.03] hover:text-foreground'
            }`}
          >
            <Boxes className="h-4 w-4" /> Inventory ({products?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('customers')}
            className={`flex items-center gap-2 text-xs font-bold uppercase tracking-wider px-4 py-2.5 rounded-xl transition ${
              activeTab === 'customers' ? 'bg-primary text-primary-foreground shadow-sm' : 'text-muted-foreground hover:bg-black/[0.03] hover:text-foreground'
            }`}
          >
            <Users className="h-4 w-4" /> Customers ({customers.length})
          </button>
          <button
            onClick={() => setActiveTab('logs')}
            className={`flex items-center gap-2 text-xs font-bold uppercase tracking-wider px-4 py-2.5 rounded-xl transition ${
              activeTab === 'logs' ? 'bg-primary text-primary-foreground shadow-sm' : 'text-muted-foreground hover:bg-black/[0.03] hover:text-foreground'
            }`}
          >
            <ScrollText className="h-4 w-4" /> Security Log
          </button>
        </div>

        {activeTab === 'inventory' && (
          <div className="relative min-w-[240px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Search SKU or Product..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 text-xs h-9 rounded-xl border-border bg-background"
            />
          </div>
        )}
      </div>

      {/* Tab Panels */}
      <div className="mt-6 bg-card border border-border rounded-3xl shadow-sm overflow-hidden">
        {activeTab === 'inventory' && (
          <div className="overflow-x-auto w-full">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-black/[0.02] border-b text-muted-foreground font-bold">
                  <th className="p-4 uppercase tracking-wider">Product Name</th>
                  <th className="p-4 uppercase tracking-wider">SKU</th>
                  <th className="p-4 uppercase tracking-wider">Barcode</th>
                  <th className="p-4 uppercase tracking-wider">Stock</th>
                  <th className="p-4 uppercase tracking-wider">Price</th>
                  <th className="p-4 uppercase tracking-wider">Status</th>
                  <th className="p-4 uppercase tracking-wider text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-black/[0.04]">
                {isLoading ? (
                  <tr>
                    <td colSpan={7} className="p-10 text-center text-muted-foreground">Loading inventory data...</td>
                  </tr>
                ) : (
                  products
                    ?.filter((p) =>
                      searchQuery
                        ? p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          (p.sku && p.sku.toLowerCase().includes(searchQuery.toLowerCase()))
                        : true
                    )
                    ?.map((p) => {
                    const isLow = (p.stock || 0) < 20
                    return (
                      <tr key={p.id} className="hover:bg-black/[0.01]">
                        <td className="p-4 font-bold text-foreground max-w-xs truncate">{p.name}</td>
                        <td className="p-4 font-mono text-muted-foreground">{p.sku}</td>
                        <td className="p-4 font-mono text-muted-foreground">{p.barcode || '—'}</td>
                        <td className="p-4 font-bold text-foreground">{p.stock ?? '—'}</td>
                        <td className="p-4 font-bold text-foreground">₹{p.price || '—'}</td>
                        <td className="p-4">
                          <Badge success={!isLow} warning={isLow} className="text-[10px]">
                            {isLow ? 'Low Stock' : 'Optimal'}
                          </Badge>
                        </td>
                        <td className="p-4 text-right">
                          <Button
                            size="sm"
                            variant="outline"
                            className="rounded-lg text-[11px] h-7 px-2.5 gap-1"
                            onClick={async () => {
                              const qty = prompt(`Restock ${p.name} (Add units):`, '50')
                              if (qty && !isNaN(Number(qty))) {
                                try {
                                  const { restockProductApi } = await import('@/lib/api')
                                  await restockProductApi(p.id, Number(qty))
                                  queryClient.invalidateQueries({ queryKey: ['admin-products'] })
                                  toast({ title: 'Stock Restocked', description: `Added ${qty} units to ${p.name}.` })
                                } catch {
                                  toast({ title: 'Restock Failed', variant: 'destructive' })
                                }
                              }
                            }}
                          >
                            <Plus className="h-3 w-3" /> Restock
                          </Button>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'customers' && (
          <div className="overflow-x-auto w-full">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-black/[0.02] border-b text-muted-foreground font-bold">
                  <th className="p-4 uppercase tracking-wider">Name</th>
                  <th className="p-4 uppercase tracking-wider">Email Address</th>
                  <th className="p-4 uppercase tracking-wider">Total Orders</th>
                  <th className="p-4 uppercase tracking-wider">Spent Amount</th>
                  <th className="p-4 uppercase tracking-wider">Segment</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-black/[0.04]">
                {customers.map((c) => (
                  <tr key={c.id} className="hover:bg-black/[0.01]">
                    <td className="p-4 font-bold text-foreground">{c.name}</td>
                    <td className="p-4 text-muted-foreground">{c.email}</td>
                    <td className="p-4 font-bold text-foreground">{c.orders}</td>
                    <td className="p-4 font-bold text-foreground">₹{c.spent.toLocaleString()}</td>
                    <td className="p-4">
                      <Badge success={c.status === 'vip'} info={c.status === 'new' || c.status === 'active'} warning={c.status === 'dormant'} className="text-[10px] uppercase">
                        {c.status}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'logs' && (
          <div className="overflow-x-auto w-full">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-black/[0.02] border-b text-muted-foreground font-bold">
                  <th className="p-4 uppercase tracking-wider">Event ID</th>
                  <th className="p-4 uppercase tracking-wider">Action</th>
                  <th className="p-4 uppercase tracking-wider">Detail</th>
                  <th className="p-4 uppercase tracking-wider">Actor</th>
                  <th className="p-4 uppercase tracking-wider">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-black/[0.04]">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-black/[0.01]">
                    <td className="p-4 font-mono font-semibold text-foreground">{log.id}</td>
                    <td className="p-4 font-bold text-foreground">{log.action}</td>
                    <td className="p-4 text-muted-foreground max-w-sm truncate">{log.detail}</td>
                    <td className="p-4 text-muted-foreground">{log.user}</td>
                    <td className="p-4 text-muted-foreground">{log.time}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Product Modal Drawer */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass border border-white/10 max-w-[500px] w-full rounded-3xl p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold text-foreground">Add Product</h2>
              <Button variant="ghost" size="icon" className="rounded-full" onClick={() => setShowAddModal(false)}>
                ✕
              </Button>
            </div>

            <form onSubmit={handleAddSubmit} className="space-y-4">
              <div>
                <Label className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Product Name</Label>
                <Input
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Sony WH-1000XM4"
                  className="mt-1.5 py-5 rounded-xl bg-card border-black/10"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="flex justify-between items-center">
                    <Label className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">SKU ID</Label>
                    <button type="button" onClick={generateRandomSKU} className="text-[10px] text-secondary font-semibold hover:underline">
                      Gen SKU
                    </button>
                  </div>
                  <Input
                    required
                    value={formData.sku}
                    onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                    placeholder="SC-ELC-002"
                    className="mt-1.5 py-5 rounded-xl bg-card border-black/10 font-mono"
                  />
                </div>
                <div>
                  <Label className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Barcode</Label>
                  <Input
                    value={formData.barcode}
                    onChange={(e) => setFormData({ ...formData, barcode: e.target.value })}
                    placeholder="890123456789"
                    className="mt-1.5 py-5 rounded-xl bg-card border-black/10 font-mono"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Brand</Label>
                  <Input
                    value={formData.brand}
                    onChange={(e) => setFormData({ ...formData, brand: e.target.value })}
                    placeholder="Sony"
                    className="mt-1.5 py-5 rounded-xl bg-card border-black/10"
                  />
                </div>
                <div>
                  <Label className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Initial Stock</Label>
                  <Input
                    type="number"
                    required
                    value={formData.initial_stock}
                    onChange={(e) => setFormData({ ...formData, initial_stock: Number(e.target.value) })}
                    placeholder="50"
                    className="mt-1.5 py-5 rounded-xl bg-card border-black/10"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Price (INR)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    required
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: Number(e.target.value) })}
                    placeholder="299.99"
                    className="mt-1.5 py-5 rounded-xl bg-card border-black/10"
                  />
                </div>
                <div>
                  <Label className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Image URL</Label>
                  <Input
                    value={formData.image_url}
                    onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
                    placeholder="https://example.com/image.jpg"
                    className="mt-1.5 py-5 rounded-xl bg-card border-black/10"
                  />
                </div>
              </div>

              <div>
                <Label className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Category Selection</Label>
                <select
                  required
                  value={formData.category_id}
                  onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
                  className="mt-1.5 w-full h-11 bg-card border border-black/10 rounded-xl px-3 outline-none text-sm"
                >
                  <option value="">Select Category</option>
                  {categories?.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <Label className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Product Description</Label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Details and specifications of this product..."
                  className="mt-1.5 w-full h-20 bg-card border border-black/10 rounded-xl p-3 text-sm outline-none resize-none"
                />
              </div>

              <div className="flex gap-4 pt-4">
                <Button type="button" variant="secondary" className="flex-1 rounded-xl py-5" onClick={() => setShowAddModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" variant="gradient" className="flex-1 rounded-xl font-semibold uppercase text-xs tracking-widest" disabled={addProductMutation.isPending}>
                  {addProductMutation.isPending ? 'Registering...' : 'Save Product'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
