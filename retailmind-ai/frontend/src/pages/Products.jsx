import { useState, useEffect } from 'react'
import { useTheme } from '../context/ThemeContext'
import { Plus, Search, Edit2, Trash2, Package } from 'lucide-react'
import api from '../services/api'
import toast from 'react-hot-toast'

export default function Products() {
  const { dark } = useTheme()
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editing, setEditing] = useState(null)
  const [search, setSearch] = useState('')
  const [form, setForm] = useState({ name: '', brand: '', category_id: '', price: '', discount: '0', stock_quantity: '', image_url: '' })

  useEffect(() => {
    fetchProducts()
    fetchCategories()
  }, [])

  const fetchProducts = async () => {
    try {
      const res = await api.get('/api/products')
      setProducts(res.data.products || [])
    } catch (err) { toast.error('Failed to load products') }
    finally { setLoading(false) }
  }

  const fetchCategories = async () => {
    try {
      const res = await api.get('/api/categories')
      setCategories(res.data.categories || [])
    } catch (err) {}
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      if (editing) {
        await api.put(`/api/products/${editing.id}`, form)
        toast.success('Product updated')
      } else {
        await api.post('/api/products', form)
        toast.success('Product created')
      }
      setShowModal(false)
      setEditing(null)
      setForm({ name: '', brand: '', category_id: '', price: '', discount: '0', stock_quantity: '', image_url: '' })
      fetchProducts()
    } catch (err) { toast.error(err.response?.data?.error || 'Failed to save product') }
  }

  const handleEdit = (product) => {
    setEditing(product)
    setForm({
      name: product.name, brand: product.brand || '', category_id: product.category_id || '',
      price: product.price, discount: product.discount, stock_quantity: product.stock_quantity, image_url: product.image_url || ''
    })
    setShowModal(true)
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this product?')) return
    try {
      await api.delete(`/api/products/${id}`)
      toast.success('Product deleted')
      fetchProducts()
    } catch (err) { toast.error('Failed to delete') }
  }

  const filtered = products.filter(p =>
    p.name.toLowerCase().includes(search.toLowerCase()) ||
    (p.brand || '').toLowerCase().includes(search.toLowerCase())
  )

  const cardBg = dark ? 'bg-gray-800/60 border-gray-700/50' : 'bg-white border-gray-200'
  const inputCls = `w-full px-3 py-2 rounded-lg border text-sm ${dark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'}`

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div></div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Products</h1>
          <p className={`text-sm ${dark ? 'text-gray-400' : 'text-gray-500'}`}>{products.length} products in inventory</p>
        </div>
        <button onClick={() => { setEditing(null); setForm({ name: '', brand: '', category_id: '', price: '', discount: '0', stock_quantity: '', image_url: '' }); setShowModal(true) }}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-sm font-medium hover:shadow-lg transition">
          <Plus className="w-4 h-4" /> Add Product
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className={`absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 ${dark ? 'text-gray-500' : 'text-gray-400'}`} />
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search products..."
          className={`w-full pl-10 pr-4 py-3 rounded-xl border ${dark ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-200'}`} />
      </div>

      {/* Products Grid */}
      {filtered.length === 0 ? (
        <div className={`text-center py-16 rounded-xl border ${cardBg}`}>
          <Package className="w-12 h-12 mx-auto text-gray-500 mb-3" />
          <p className="text-gray-500">No products found. Add your first product!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map(product => (
            <div key={product.id} className={`rounded-xl p-5 border ${cardBg} hover:shadow-lg transition`}>
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-semibold">{product.name}</h3>
                  <p className={`text-sm ${dark ? 'text-gray-400' : 'text-gray-500'}`}>{product.brand || 'No brand'} • {product.category_name || 'Uncategorized'}</p>
                </div>
                <div className="flex gap-1">
                  <button onClick={() => handleEdit(product)} className={`p-1.5 rounded-lg ${dark ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}><Edit2 className="w-4 h-4" /></button>
                  <button onClick={() => handleDelete(product.id)} className="p-1.5 rounded-lg hover:bg-red-500/10 text-red-500"><Trash2 className="w-4 h-4" /></button>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-lg font-bold text-indigo-500">₹{product.final_price.toFixed(2)}</span>
                {product.discount > 0 && (
                  <>
                    <span className={`text-sm line-through ${dark ? 'text-gray-600' : 'text-gray-400'}`}>₹{product.price.toFixed(2)}</span>
                    <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-green-500/10 text-green-500">{product.discount}% off</span>
                  </>
                )}
              </div>
              <div className={`mt-3 text-sm ${product.stock_quantity < 10 ? 'text-red-500' : dark ? 'text-gray-400' : 'text-gray-500'}`}>
                Stock: {product.stock_quantity} units
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className={`w-full max-w-lg rounded-2xl p-6 border ${dark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
            <h2 className="text-xl font-bold mb-4">{editing ? 'Edit Product' : 'Add Product'}</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <input className={inputCls} placeholder="Product Name *" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required />
              <input className={inputCls} placeholder="Brand" value={form.brand} onChange={e => setForm({ ...form, brand: e.target.value })} />
              <select className={inputCls} value={form.category_id} onChange={e => setForm({ ...form, category_id: e.target.value || '' })}>
                <option value="">Select Category</option>
                {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
              <div className="grid grid-cols-3 gap-3">
                <input className={inputCls} type="number" step="0.01" placeholder="Price *" value={form.price} onChange={e => setForm({ ...form, price: e.target.value })} required />
                <input className={inputCls} type="number" step="0.01" placeholder="Discount %" value={form.discount} onChange={e => setForm({ ...form, discount: e.target.value })} />
                <input className={inputCls} type="number" placeholder="Stock" value={form.stock_quantity} onChange={e => setForm({ ...form, stock_quantity: e.target.value })} />
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowModal(false)} className={`flex-1 py-2.5 rounded-xl border ${dark ? 'border-gray-600 hover:bg-gray-700' : 'border-gray-300 hover:bg-gray-50'}`}>Cancel</button>
                <button type="submit" className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
