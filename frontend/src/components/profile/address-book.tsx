import { useState, useEffect } from 'react'
import { MapPin, Plus, Trash2, Star, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useToast } from '@/components/ui/use-toast'
import { listAddressesApi, createAddressApi, deleteAddressApi, type Address } from '@/lib/api'

export function AddressBook({ selectable, onSelect }: { selectable?: boolean; onSelect?: (a: Address) => void }) {
  const { toast } = useToast()
  const [addresses, setAddresses] = useState<Address[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ line1: '', city: '', state: '', postal_code: '', country: 'India', is_default: false })
  const [saving, setSaving] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const res = await listAddressesApi()
      setAddresses(res)
    } catch {}
    setLoading(false)
  }
  useEffect(() => { load() }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.line1 || !form.city || !form.postal_code) {
      toast({ title: 'Missing fields', variant: 'destructive' })
      return
    }
    setSaving(true)
    try {
      await createAddressApi({ address_type: 'home', line1: form.line1, line2: null, city: form.city, state: form.state, country: form.country, postal_code: form.postal_code, is_default: form.is_default })
      setForm({ line1: '', city: '', state: '', postal_code: '', country: 'India', is_default: false })
      setShowForm(false)
      await load()
      toast({ title: 'Address saved' })
    } catch (e: any) {
      toast({ title: 'Failed', description: e.message, variant: 'destructive' })
    } finally { setSaving(false) }
  }

  if (loading) return <div className="flex items-center gap-2 text-xs text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" /> Loading addresses…</div>

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="font-bold text-sm flex items-center gap-1.5"><MapPin className="h-4 w-4 text-primary" /> Saved Addresses ({addresses.length})</h4>
        <Button size="sm" variant="outline" className="rounded-xl text-xs" onClick={() => setShowForm(v => !v)}><Plus className="h-3.5 w-3.5" /> {showForm ? 'Cancel' : 'Add'}</Button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="grid gap-3 p-4 border border-border rounded-2xl bg-card">
          <div><Label className="text-xs">Address Line</Label><Input value={form.line1} onChange={e => setForm({ ...form, line1: e.target.value })} placeholder="123, MG Road, Apt 4B" className="mt-1" /></div>
          <div className="grid grid-cols-2 gap-3">
            <div><Label className="text-xs">City</Label><Input value={form.city} onChange={e => setForm({ ...form, city: e.target.value })} placeholder="Bengaluru" className="mt-1" /></div>
            <div><Label className="text-xs">State</Label><Input value={form.state} onChange={e => setForm({ ...form, state: e.target.value })} placeholder="Karnataka" className="mt-1" /></div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div><Label className="text-xs">Postal Code</Label><Input value={form.postal_code} onChange={e => setForm({ ...form, postal_code: e.target.value })} placeholder="560001" className="mt-1" /></div>
            <div><Label className="text-xs">Country</Label><Input value={form.country} onChange={e => setForm({ ...form, country: e.target.value })} placeholder="India" className="mt-1" /></div>
          </div>
          <label className="flex items-center gap-2 text-xs font-semibold"><input type="checkbox" checked={form.is_default} onChange={e => setForm({ ...form, is_default: e.target.checked })} /> Set as default</label>
          <Button type="submit" size="sm" disabled={saving} className="rounded-xl">{saving ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Save Address'}</Button>
        </form>
      )}

      {addresses.length === 0 ? (
        <div className="p-6 text-center text-xs text-muted-foreground border border-dashed border-border rounded-2xl">No saved addresses yet. Add one to speed up checkout.</div>
      ) : (
        <div className="grid gap-3">
          {addresses.map(a => (
            <div key={a.id} className={`p-4 border rounded-2xl flex justify-between gap-3 ${a.is_default ? 'border-primary bg-primary/5' : 'border-border bg-card'}`}>
              <div className="text-xs leading-relaxed">
                <div className="font-bold flex items-center gap-1">{a.line1} {a.is_default && <Star className="h-3 w-3 text-amber-500 fill-amber-500" />}</div>
                <div className="text-muted-foreground">{a.city}, {a.state} {a.postal_code}, {a.country}</div>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                {selectable && onSelect && <Button size="sm" className="rounded-xl text-xs h-7" onClick={() => onSelect(a)}>Use</Button>}
                <Button size="sm" variant="ghost" className="h-7 w-7 p-0" onClick={async () => { await deleteAddressApi(a.id); await load(); toast({ title: 'Deleted' }) }}><Trash2 className="h-3.5 w-3.5" /></Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
