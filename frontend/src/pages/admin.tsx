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
  Pencil,
  Upload,
  Barcode,
  Loader2,
  ImageIcon,
  ExternalLink,
  PackageX,
  TrendingUp,
  PackageCheck,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { useAuth } from '@/hooks/use-auth'
import {
  getCategoriesApi,
  listProductsApi,
  createProductApi,
  updateProductApi,
  deleteProductApi,
  uploadProductImageApi,
  bulkUploadProductsApi,
  generateBarcodeApi,
  getOrderSlipApi,
  listAdminOrdersApi,
  getRealCustomersApi,
  getRealLogsApi,
} from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'

type ProductRow = {
  id: string
  name: string
  sku: string
  barcode?: string | null
  brand?: string | null
  description?: string | null
  category_id: string
  category_name?: string
  is_active: boolean
  price?: number
  stock?: number
  images?: string[]
}

const BULK_TEMPLATE = [
  'name,sku,category_id,initial_stock,price,brand,barcode,image_url',
  'Sample Milk,SC-Demo-001,<CATEGORY_ID>,50,45.0,Amul,,https://example.com/milk.jpg',
  'Sample Bread,SC-Demo-002,<CATEGORY_ID>,30,30.0,Britannia,,https://example.com/bread.jpg',
].join('\n')

export function AdminPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const [activeTab, setActiveTab] = useState<'inventory' | 'orders' | 'customers' | 'logs'>('inventory')
  const [searchQuery, setSearchQuery] = useState('')
  const [showAdd, setShowAdd] = useState(false)
  const [editing, setEditing] = useState<ProductRow | null>(null)
  const [showBulk, setShowBulk] = useState(false)

  const { data: categories = [] } = useQuery({ queryKey: ['admin-categories'], queryFn: getCategoriesApi })
  const { data: products = [], isLoading } = useQuery({
    queryKey: ['admin-products'],
    queryFn: () => listProductsApi(0, 200) as Promise<ProductRow[]>,
  })
  const { data: customers = [] } = useQuery({ queryKey: ['admin-customers'], queryFn: getRealCustomersApi })
  const { data: logs = [] } = useQuery({ queryKey: ['admin-logs'], queryFn: getRealLogsApi })

  // mutations
  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['admin-products'] })
    queryClient.invalidateQueries({ queryKey: ['products'] })
  }

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteProductApi(id),
    onSuccess: () => { invalidate(); toast({ title: 'Product deleted' }) },
    onError: (e: any) => toast({ title: 'Delete failed', description: e?.message, variant: 'destructive' }),
  })

  const refresh = () => invalidate()

  if (user?.role !== 'admin') {
    return (
      <div className="mx-auto max-w-md px-6 py-24 text-center flex flex-col items-center justify-center gap-6">
        <div className="w-16 h-16 bg-destructive/10 text-destructive rounded-full flex items-center justify-center shadow-sm">
          <ShieldAlert className="h-6 w-6" />
        </div>
        <h2 className="text-2xl font-bold text-foreground">Access Denied</h2>
        <p className="text-sm text-muted-foreground leading-relaxed">
          This panel is restricted to system administrators only.
        </p>
        <Button variant="secondary" className="w-full rounded-xl py-6" onClick={() => navigate('/')}>
          Return Home
        </Button>
      </div>
    )
  }

  const filtered = products.filter((p) =>
    searchQuery
      ? p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.sku.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (p.barcode || '').includes(searchQuery)
      : true,
  )

  const downloadBulkTemplate = () => {
    const cat = categories[0]?.id || '<CATEGORY_ID>'
    const csv = BULK_TEMPLATE.replaceAll('<CATEGORY_ID>', cat)
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'smartcart_bulk_template.csv'
    a.click()
    URL.revokeObjectURL(url)
  }

  const exportInventoryCSV = () => {
    if (!products.length) { toast({ title: 'No Data' }); return }
    const headers = ['Product ID', 'Name', 'SKU', 'Barcode', 'Stock', 'Price (INR)', 'Status']
    const rows = products.map((p) => [p.id, `"${p.name.replace(/"/g, '""')}"`, p.sku || '', p.barcode || '', p.stock ?? 0, p.price ?? 0, (p.stock ?? 0) < 20 ? 'Low Stock' : 'Optimal'])
    const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `smartcart_inventory_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const exportAuditCSV = () => {
    const headers = ['Event ID', 'Action', 'Detail', 'User', 'Timestamp', 'Severity']
    const rows = logs.map((l: any) => [l.id, l.action, `"${l.detail.replace(/"/g, '""')}"`, l.user, `"${l.time}"`, l.severity])
    const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `smartcart_audit_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="mx-auto max-w-7xl px-6 py-10">
      <div className="flex justify-between items-center flex-wrap gap-4 border-b pb-6">
        <div>
          <h1 className="text-3xl font-sans font-extrabold text-foreground">Admin Console</h1>
          <p className="text-xs text-muted-foreground mt-1">Inventory, orders, customers & system logs.</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" className="rounded-xl font-semibold uppercase text-xs tracking-widest py-5 px-4 gap-2 border-border" onClick={exportInventoryCSV}>
            <FileSpreadsheet className="h-4 w-4 text-emerald-600" /> Export Inventory
          </Button>
          {activeTab === 'inventory' && (
            <>
              <Button variant="outline" className="rounded-xl font-semibold uppercase text-xs tracking-widest py-5 px-4 gap-2" onClick={() => setShowBulk(true)}>
                <Upload className="h-4 w-4" /> Bulk Upload
              </Button>
              <Button variant="gradient" className="rounded-xl font-semibold uppercase text-xs tracking-widest py-5 px-5 gap-2" onClick={() => { setEditing(null); setShowAdd(true) }}>
                <Plus className="h-4 w-4" /> Add Product
              </Button>
            </>
          )}
        </div>
      </div>

      <div className="mt-8 flex justify-between items-center flex-wrap gap-4 border-b border-black/[0.04] pb-4">
        <div className="flex gap-3">
          <TabBtn active={activeTab === 'inventory'} onClick={() => setActiveTab('inventory')} icon={<Boxes className="h-4 w-4" />} label={`Inventory (${products.length})`} />
          <TabBtn active={activeTab === 'orders'} onClick={() => setActiveTab('orders')} icon={<ScrollText className="h-4 w-4" />} label="Orders & Slips" />
          <TabBtn active={activeTab === 'customers'} onClick={() => setActiveTab('customers')} icon={<Users className="h-4 w-4" />} label={`Customers (${customers.length})`} />
          <TabBtn active={activeTab === 'logs'} onClick={() => setActiveTab('logs')} icon={<AlertTriangle className="h-4 w-4" />} label="Security Log" />
        </div>
        {activeTab === 'inventory' && (
          <div className="relative min-w-[240px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input type="text" placeholder="Search name / SKU / barcode" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-9 text-xs h-9 rounded-xl border-border bg-background" />
          </div>
        )}
      </div>

      <div className="mt-6 bg-card border border-border rounded-3xl shadow-sm overflow-hidden">
        {activeTab === 'inventory' && (
          <InventoryDashboardView
            products={products}
            searchQuery={searchQuery}
            loading={isLoading}
            onEdit={(p) => { setEditing(p); setShowAdd(true) }}
            onDelete={(id) => deleteMutation.mutate(id)}
          />
        )}
        {activeTab === 'orders' && <OrdersSlipsTab />}
        {activeTab === 'customers' && <CustomersTable rows={customers} />}
        {activeTab === 'logs' && <LogsTable rows={logs} onExport={exportAuditCSV} />}
      </div>

      {showAdd && (
        <ProductModal
          editing={editing}
          categories={categories}
          onClose={() => { setShowAdd(false); setEditing(null) }}
          onDone={() => { setShowAdd(false); setEditing(null); invalidate() }}
        />
      )}
      {showBulk && <BulkModal onClose={() => setShowBulk(false)} onDone={() => { setShowBulk(false); invalidate() }} onTemplate={downloadBulkTemplate} />}
    </div>
  )
}

function TabBtn({ active, onClick, icon, label }: { active: boolean; onClick: () => void; icon: React.ReactNode; label: string }) {
  return (
    <button onClick={onClick} className={`flex items-center gap-2 text-xs font-bold uppercase tracking-wider px-4 py-2.5 rounded-xl transition ${active ? 'bg-primary text-primary-foreground shadow-sm' : 'text-muted-foreground hover:bg-black/[0.03] hover:text-foreground'}`}>
      {icon} {label}
    </button>
  )
}

function InventoryDashboardView({
  products,
  searchQuery,
  loading,
  onEdit,
  onDelete,
}: {
  products: ProductRow[]
  searchQuery: string
  loading: boolean
  onEdit: (p: ProductRow) => void
  onDelete: (id: string) => void
}) {
  const navigate = useNavigate()

  if (loading) return <div className="p-10 text-center text-muted-foreground text-sm">Loading inventory metrics…</div>

  const totalSkus = products.length
  const lowStockProducts = products.filter((p) => (p.stock ?? 0) > 0 && (p.stock ?? 0) < 20)
  const outOfStockProducts = products.filter((p) => (p.stock ?? 0) === 0)
  const totalValuation = products.reduce((acc, p) => acc + (p.price ?? 0) * (p.stock ?? 0), 0)

  const searchedProducts = searchQuery
    ? products.filter(
        (p) =>
          p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          p.sku.toLowerCase().includes(searchQuery.toLowerCase()) ||
          (p.barcode || '').includes(searchQuery),
      )
    : []

  return (
    <div className="p-6 space-y-8">
      {/* Top Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-background border border-border rounded-2xl p-5 flex items-center justify-between shadow-sm">
          <div>
            <p className="text-xs uppercase font-bold text-muted-foreground tracking-wider">Total SKUs</p>
            <p className="text-2xl font-black text-foreground mt-1">{totalSkus}</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
            <Boxes className="h-5 w-5" />
          </div>
        </div>

        <div className="bg-background border border-border rounded-2xl p-5 flex items-center justify-between shadow-sm">
          <div>
            <p className="text-xs uppercase font-bold text-muted-foreground tracking-wider">Stock Valuation</p>
            <p className="text-2xl font-black text-foreground mt-1">₹{totalValuation.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-600 flex items-center justify-center">
            <TrendingUp className="h-5 w-5" />
          </div>
        </div>

        <div className="bg-background border border-border rounded-2xl p-5 flex items-center justify-between shadow-sm">
          <div>
            <p className="text-xs uppercase font-bold text-muted-foreground tracking-wider">Low Stock Items</p>
            <p className="text-2xl font-black text-amber-600 mt-1">{lowStockProducts.length}</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-600 flex items-center justify-center">
            <AlertTriangle className="h-5 w-5" />
          </div>
        </div>

        <div className="bg-background border border-border rounded-2xl p-5 flex items-center justify-between shadow-sm">
          <div>
            <p className="text-xs uppercase font-bold text-muted-foreground tracking-wider">Out of Stock</p>
            <p className="text-2xl font-black text-destructive mt-1">{outOfStockProducts.length}</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-destructive/10 text-destructive flex items-center justify-center">
            <PackageX className="h-5 w-5" />
          </div>
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-primary/5 border border-primary/20 rounded-2xl p-4 flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <ImageIcon className="h-5 w-5 text-primary shrink-0" />
          <p className="text-xs text-foreground font-medium">
            <strong>Product Image & Catalog Controls:</strong> Product image uploading, editing, and deletion are now managed on each individual Product Page.
          </p>
        </div>
      </div>

      {/* Quick Search Lookup Results */}
      {searchQuery && (
        <div className="space-y-3">
          <h3 className="text-sm font-bold uppercase tracking-wider text-foreground flex items-center gap-2">
            <Search className="h-4 w-4 text-primary" /> Search Results ({searchedProducts.length})
          </h3>
          {searchedProducts.length === 0 ? (
            <div className="p-6 text-center text-muted-foreground text-xs bg-background border rounded-2xl">
              No products found matching "{searchQuery}".
            </div>
          ) : (
            <div className="border border-border rounded-2xl overflow-hidden bg-background">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-black/[0.02] border-b text-muted-foreground font-bold">
                    <th className="p-3">Product Name</th>
                    <th className="p-3">SKU</th>
                    <th className="p-3">Barcode</th>
                    <th className="p-3">Price</th>
                    <th className="p-3">Stock</th>
                    <th className="p-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-black/[0.04]">
                  {searchedProducts.map((p) => (
                    <tr key={p.id} className="hover:bg-black/[0.01]">
                      <td className="p-3 font-bold text-foreground">{p.name}</td>
                      <td className="p-3 font-mono text-muted-foreground">{p.sku}</td>
                      <td className="p-3 font-mono text-muted-foreground">{p.barcode || '—'}</td>
                      <td className="p-3 font-bold text-foreground">₹{p.price ?? '—'}</td>
                      <td className="p-3 font-bold text-foreground">{p.stock ?? '—'}</td>
                      <td className="p-3 text-right flex justify-end gap-2">
                        <Button
                          size="sm"
                          variant="gradient"
                          className="rounded-lg text-[11px] h-7 px-3 gap-1"
                          onClick={() => navigate(`/product/${p.id}`)}
                        >
                          Product Page <ExternalLink className="h-3 w-3" />
                        </Button>
                        <Button size="sm" variant="outline" className="rounded-lg text-[11px] h-7 px-2" onClick={() => onEdit(p)}>
                          <Pencil className="h-3 w-3" />
                        </Button>
                        <Button size="sm" variant="outline" className="rounded-lg text-[11px] h-7 px-2 text-destructive" onClick={() => onDelete(p.id)}>
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Critical Stock & Reorder Alerts Table */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold uppercase tracking-wider text-foreground flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-500" /> Low Stock & Critical Inventory Alerts ({lowStockProducts.length + outOfStockProducts.length})
        </h3>
        {[...outOfStockProducts, ...lowStockProducts].length === 0 ? (
          <div className="p-8 text-center text-muted-foreground text-xs bg-background border rounded-2xl flex flex-col items-center gap-2">
            <PackageCheck className="h-8 w-8 text-emerald-500" />
            <span className="font-semibold text-foreground">Inventory Levels Optimal</span>
            <span>All product stock levels are above the threshold limit (20 units).</span>
          </div>
        ) : (
          <div className="border border-border rounded-2xl overflow-hidden bg-background">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-black/[0.02] border-b text-muted-foreground font-bold">
                  <th className="p-3">Product Name</th>
                  <th className="p-3">SKU</th>
                  <th className="p-3">Current Stock</th>
                  <th className="p-3">Price</th>
                  <th className="p-3">Status</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-black/[0.04]">
                {[...outOfStockProducts, ...lowStockProducts].map((p) => {
                  const isZero = (p.stock ?? 0) === 0
                  return (
                    <tr key={p.id} className="hover:bg-black/[0.01]">
                      <td className="p-3 font-bold text-foreground">{p.name}</td>
                      <td className="p-3 font-mono text-muted-foreground">{p.sku}</td>
                      <td className="p-3 font-bold text-foreground">{p.stock ?? 0}</td>
                      <td className="p-3 font-bold text-foreground">₹{p.price ?? '—'}</td>
                      <td className="p-3">
                        <Badge warning={!isZero} destructive={isZero} className="text-[10px] uppercase">
                          {isZero ? 'Out of Stock' : 'Low Stock'}
                        </Badge>
                      </td>
                      <td className="p-3 text-right flex justify-end gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          className="rounded-lg text-[11px] h-7 px-3 gap-1"
                          onClick={() => navigate(`/product/${p.id}`)}
                        >
                          Product Page <ExternalLink className="h-3 w-3" />
                        </Button>
                        <Button size="sm" variant="outline" className="rounded-lg text-[11px] h-7 px-2" onClick={() => onEdit(p)}>
                          <Pencil className="h-3 w-3" />
                        </Button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function CustomersTable({ rows }: { rows: any[] }) {
  return (
    <div className="overflow-x-auto w-full">
      <table className="w-full text-left text-xs border-collapse">
        <thead><tr className="bg-black/[0.02] border-b text-muted-foreground font-bold">
          <th className="p-4 uppercase tracking-wider">Name</th><th className="p-4 uppercase tracking-wider">Email</th>
          <th className="p-4 uppercase tracking-wider">Orders</th><th className="p-4 uppercase tracking-wider">Spent</th><th className="p-4 uppercase tracking-wider">Segment</th>
        </tr></thead>
        <tbody className="divide-y divide-black/[0.04]">
          {rows.map((c) => (
            <tr key={c.id} className="hover:bg-black/[0.01]">
              <td className="p-4 font-bold text-foreground">{c.name}</td>
              <td className="p-4 text-muted-foreground">{c.email}</td>
              <td className="p-4 font-bold text-foreground">{c.orders}</td>
              <td className="p-4 font-bold text-foreground">₹{c.spent?.toLocaleString()}</td>
              <td className="p-4"><Badge success={c.status === 'vip' || c.status === 'active'} warning={c.status === 'dormant'} className="text-[10px] uppercase">{c.status}</Badge></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function LogsTable({ rows, onExport }: { rows: any[]; onExport: () => void }) {
  return (
    <div className="overflow-x-auto w-full">
      <div className="flex justify-end p-3">
        <Button variant="outline" size="sm" className="rounded-lg text-[11px]" onClick={onExport}><Download className="h-3 w-3 mr-1" /> Export</Button>
      </div>
      <table className="w-full text-left text-xs border-collapse">
        <thead><tr className="bg-black/[0.02] border-b text-muted-foreground font-bold">
          <th className="p-4 uppercase tracking-wider">Event</th><th className="p-4 uppercase tracking-wider">Action</th>
          <th className="p-4 uppercase tracking-wider">Detail</th><th className="p-4 uppercase tracking-wider">Actor</th><th className="p-4 uppercase tracking-wider">Time</th>
        </tr></thead>
        <tbody className="divide-y divide-black/[0.04]">
          {rows.map((l) => (
            <tr key={l.id} className="hover:bg-black/[0.01]">
              <td className="p-4 font-mono font-semibold text-foreground">{l.id}</td>
              <td className="p-4 font-bold text-foreground">{l.action}</td>
              <td className="p-4 text-muted-foreground max-w-sm truncate">{l.detail}</td>
              <td className="p-4 text-muted-foreground">{l.user}</td>
              <td className="p-4 text-muted-foreground">{l.time}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ProductModal({ editing, categories, onClose, onDone }: {
  editing: ProductRow | null
  categories: { id: string; name: string }[]
  onClose: () => void
  onDone: () => void
}) {
  const { toast } = useToast()
  const [form, setForm] = useState({
    name: editing?.name || '',
    sku: editing?.sku || '',
    barcode: editing?.barcode || '',
    brand: editing?.brand || '',
    description: editing?.description || '',
    category_id: editing?.category_id || '',
    price: editing?.price ?? 0,
    stock: editing?.stock ?? 0,
    is_active: editing?.is_active ?? true,
    image_url: editing?.images?.[0] || '',
  })
  const [imgPreview, setImgPreview] = useState(editing?.images?.[0] || '')
  const [uploading, setUploading] = useState(false)
  const [genBc, setGenBc] = useState(false)
  const [saving, setSaving] = useState(false)

  const onFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const { image_url } = await uploadProductImageApi(file)
      setForm((f) => ({ ...f, image_url }))
      setImgPreview(image_url)
      toast({ title: 'Image uploaded' })
    } catch (err: any) {
      toast({ title: 'Upload failed', description: err?.message, variant: 'destructive' })
    } finally { setUploading(false) }
  }

  const onGenerateBarcode = async () => {
    setGenBc(true)
    try {
      const res = await generateBarcodeApi(form.barcode || undefined)
      setForm((f) => ({ ...f, barcode: res.barcode }))
      toast({ title: `Barcode: ${res.barcode}` })
    } catch (err: any) {
      toast({ title: 'Barcode gen failed', variant: 'destructive' })
    } finally { setGenBc(false) }
  }

  const handleSave = async () => {
    if (!form.name || !form.sku || !form.category_id) {
      toast({ title: 'Name, SKU & Category required', variant: 'destructive' }); return
    }
    setSaving(true)
    const body: any = {
      name: form.name,
      sku: form.sku,
      barcode: form.barcode || null,
      brand: form.brand || null,
      description: form.description || null,
      category_id: form.category_id,
      price: Number(form.price) || 0,
      stock: Number(form.stock) || 0,
      is_active: form.is_active,
      image_url: form.image_url || null,
    }
    try {
      if (editing) {
        await updateProductApi(editing.id, body)
        toast({ title: 'Product updated' })
      } else {
        await createProductApi(body)
        toast({ title: 'Product created' })
      }
      onDone()
    } catch (err: any) {
      toast({ title: 'Save failed', description: err?.message, variant: 'destructive' })
    } finally { setSaving(false) }
  }

  return (
    <ModalShell title={editing ? 'Edit Product' : 'Add Product'} onClose={onClose}>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Product Name"><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Product name" /></Field>
        <Field label="SKU"><Input value={form.sku} onChange={(e) => setForm({ ...form, sku: e.target.value })} placeholder="SC-ELC-001" /></Field>
        <Field label="Brand"><Input value={form.brand} onChange={(e) => setForm({ ...form, brand: e.target.value })} placeholder="Brand" /></Field>
        <Field label="Barcode">
          <div className="flex gap-2">
            <Input value={form.barcode} onChange={(e) => setForm({ ...form, barcode: e.target.value })} placeholder="890123456789" />
            <Button variant="outline" size="sm" onClick={onGenerateBarcode} disabled={genBc}>{genBc ? <Loader2 className="h-3 w-3 animate-spin" /> : <Barcode className="h-3 w-3" />}</Button>
          </div>
        </Field>
        <Field label="Price (INR)"><Input type="number" step="0.01" value={form.price} onChange={(e) => setForm({ ...form, price: Number(e.target.value) })} /></Field>
        <Field label="Stock"><Input type="number" value={form.stock} onChange={(e) => setForm({ ...form, stock: Number(e.target.value) })} /></Field>
        <Field label="Category" full>
          <select value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })} className="w-full h-11 bg-card border border-black/10 rounded-xl px-3 outline-none text-sm">
            <option value="">Select Category</option>
            {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </Field>
        <Field label="Image (upload)" full>
          <div className="flex items-center gap-3">
            <div className="w-16 h-16 rounded-xl border overflow-hidden bg-black/[0.03]">
              {imgPreview ? <img src={imgPreview} alt="" className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center text-muted-foreground"><ImageIcon className="h-5 w-5" /></div>}
            </div>
            <div>
              <input type="file" accept="image/*" onChange={onFile} className="block text-xs" />
              {uploading && <p className="text-[11px] text-muted-foreground mt-1">Uploading…</p>}
              <p className="text-[10px] text-muted-foreground mt-1">Uploads to CDN, replaces URL field.</p>
            </div>
          </div>
        </Field>
        <Field label="Description" full>
          <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={2} className="w-full bg-card border border-black/10 rounded-xl p-3 text-sm outline-none" />
        </Field>
        <label className="col-span-2 flex items-center gap-2 text-xs">
          <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} /> Active (visible to customers)
        </label>
      </div>
      <div className="flex justify-end gap-2 mt-5">
        <Button variant="ghost" onClick={onClose}>Cancel</Button>
        <Button variant="gradient" onClick={handleSave} disabled={saving}>{saving ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Save Product'}</Button>
      </div>
    </ModalShell>
  )
}

function Field({ label, children, full }: { label: string; children: React.ReactNode; full?: boolean }) {
  return (
    <div className={full ? 'col-span-2' : ''}>
      <Label className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">{label}</Label>
      <div className="mt-1.5">{children}</div>
    </div>
  )
}

function ModalShell({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="glass border border-white/10 max-w-[640px] w-full max-h-[90vh] overflow-y-auto rounded-3xl p-6 shadow-2xl space-y-5">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-bold text-foreground">{title}</h2>
          <Button variant="ghost" size="icon" className="rounded-full" onClick={onClose}>✕</Button>
        </div>
        {children}
      </div>
    </div>
  )
}

function BulkModal({ onClose, onDone, onTemplate }: { onClose: () => void; onDone: () => void; onTemplate: () => void }) {
  const { toast } = useToast()
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<{ created: number; failed: number; errors: string[] } | null>(null)

  const handleUpload = async () => {
    if (!file) { toast({ title: 'Choose a CSV first', variant: 'destructive' }); return }
    setBusy(true)
    try {
      const res = await bulkUploadProductsApi(file)
      setResult(res)
      toast({ title: `Created ${res.created} products`, description: res.failed ? `${res.failed} failed` : undefined })
      if (res.created > 0) onDone()
    } catch (err: any) {
      toast({ title: 'Bulk upload failed', description: err?.message, variant: 'destructive' })
    } finally { setBusy(false) }
  }

  return (
    <ModalShell title="Bulk Upload Products" onClose={onClose}>
      <p className="text-xs text-muted-foreground">Upload a CSV with columns: <code className="font-mono">name,sku,category_id,initial_stock,price,brand,barcode,image_url</code>. The first row is the header.</p>
      <div className="flex items-center gap-3 mt-3">
        <input type="file" accept=".csv,text/csv" onChange={(e) => setFile(e.target.files?.[0] || null)} className="text-xs" />
        <Button variant="outline" size="sm" onClick={onTemplate}>Download Template</Button>
      </div>
      {result && (
        <div className="mt-3 text-xs rounded-xl border border-black/10 p-3 bg-black/[0.02]">
          <p>Created: <b>{result.created}</b> · Failed: <b>{result.failed}</b></p>
          {result.errors.length > 0 && <ul className="mt-1 list-disc pl-4 text-destructive">{result.errors.slice(0, 5).map((e, i) => <li key={i}>{e}</li>)}</ul>}
        </div>
      )}
      <div className="flex justify-end gap-2 mt-5">
        <Button variant="ghost" onClick={onClose}>Cancel</Button>
        <Button variant="gradient" onClick={handleUpload} disabled={busy}>{busy ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Upload CSV'}</Button>
      </div>
    </ModalShell>
  )
}

function OrdersSlipsTab() {
  const { toast } = useToast()
  const { data, isLoading } = useQuery({ queryKey: ['admin-orders'], queryFn: () => listAdminOrdersApi(1, 50) as Promise<any> })
  const orders = data?.items || []
  const [busyId, setBusyId] = useState<string | null>(null)

  const download = async (id: string) => {
    setBusyId(id)
    try { await getOrderSlipApi(id); toast({ title: 'Slip downloaded (PDF)' }) }
    catch (err: any) { toast({ title: 'Slip failed', description: err?.message, variant: 'destructive' }) }
    finally { setBusyId(null) }
  }

  if (isLoading) return <div className="p-10 text-center text-muted-foreground text-sm">Loading orders…</div>
  if (!orders.length) return <div className="p-10 text-center text-muted-foreground text-sm">No orders found.</div>
  return (
    <div className="overflow-x-auto w-full">
      <table className="w-full text-left text-xs border-collapse">
        <thead><tr className="bg-black/[0.02] border-b text-muted-foreground font-bold">
          <th className="p-4 uppercase tracking-wider">Order #</th><th className="p-4 uppercase tracking-wider">Status</th>
          <th className="p-4 uppercase tracking-wider">Total</th><th className="p-4 uppercase tracking-wider text-right">Slip</th>
        </tr></thead>
        <tbody className="divide-y divide-black/[0.04]">
          {orders.map((o: any) => (
            <tr key={o.id} className="hover:bg-black/[0.01]">
              <td className="p-4 font-mono font-semibold text-foreground">{o.order_number}</td>
              <td className="p-4"><Badge success className="text-[10px] uppercase">{o.status}</Badge></td>
              <td className="p-4 font-bold text-foreground">₹{o.total_amount}</td>
              <td className="p-4 text-right">
                <Button size="sm" variant="outline" className="rounded-lg text-[11px] h-7 px-2.5 gap-1" onClick={() => download(o.id)} disabled={busyId === o.id}>
                  {busyId === o.id ? <Loader2 className="h-3 w-3 animate-spin" /> : <Download className="h-3 w-3" />} Customer + Shop Copy
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}



