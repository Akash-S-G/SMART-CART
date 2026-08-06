import type {
  Category,
  Product,
  Order,
  Address,
  SavedCard,
  AppNotification,
  Customer,
  InventoryRow,
  ActivityEvent,
  DetectionLog,
} from '@/types/api'

export const gradientFor = (i: number) =>
  `linear-gradient(140deg, hsl(${(i * 47) % 360} 70% 45%), hsl(${(i * 83 + 40) % 360} 70% 30%))`

export const categories: Category[] = [
  { id: 'c1', name: 'Electronics', slug: 'electronics', icon: 'zap', product_count: 142, gradient: 'hsl(215 90% 50%)' },
  { id: 'c2', name: 'Fashion', slug: 'fashion', icon: 'shirt', product_count: 230, gradient: 'hsl(330 80% 52%)' },
  { id: 'c3', name: 'Home & Living', slug: 'home-living', icon: 'home', product_count: 118, gradient: 'hsl(40 85% 50%)' },
  { id: 'c4', name: 'Beauty', slug: 'beauty', icon: 'sparkles', product_count: 96, gradient: 'hsl(275 80% 55%)' },
  { id: 'c5', name: 'Sports & Fitness', slug: 'sports', icon: 'dumbbell', product_count: 74, gradient: 'hsl(150 75% 42%)' },
  { id: 'c6', name: 'Groceries', slug: 'groceries', icon: 'shopping-cart', product_count: 320, gradient: 'hsl(95 70% 42%)' },
  { id: 'c7', name: 'Gaming', slug: 'gaming', icon: 'gamepad', product_count: 88, gradient: 'hsl(260 85% 55%)' },
  { id: 'c8', name: 'Accessories', slug: 'accessories', icon: 'watch', product_count: 64, gradient: 'hsl(200 85% 50%)' },
]

const img = (seed: number, label: string) =>
  `https://images.unsplash.com/photo-${seed}?auto=format&fit=crop&w=900&q=80`

export const products: Product[] = [
  {
    id: 'p1', sku: 'NV-HP-01', name: 'Nova Wireless Noise-Cancelling Headphones', brand: 'Nova', category_id: 'c1',
    category_name: 'Electronics', price: 249, compare_at_price: 329, stock: 42, rating: 4.8, review_count: 1240,
    tags: ['Best Seller', 'AI Picked'], is_active: true,
    description: 'Immersive spatial audio with adaptive active noise cancellation and AI-tuned EQ profiles.',
    images: [img(1505743614, 'headphones'), img(1505743616, 'headphones'), img(1505743621, 'headphones')],
  },
  {
    id: 'p2', sku: 'LX-SM-02', name: 'Aurum Smartwatch Series 7', brand: 'Aurum', category_id: 'c1',
    category_name: 'Electronics', price: 199, compare_at_price: 259, stock: 18, rating: 4.6, review_count: 890,
    tags: ['Trending'], is_active: true,
    description: 'Health-tracking smartwatch with AMOLED display, GPS, and AI sleep analysis.',
    images: [img(1523275335684, 'watch'), img(1523275335682, 'watch')],
  },
  {
    id: 'p3', sku: 'FX-SN-03', name: 'Cloudflow Running Shoes', brand: 'Cloudflow', category_id: 'c5',
    category_name: 'Sports & Fitness', price: 129, compare_at_price: 149, stock: 76, rating: 4.7, review_count: 2100,
    tags: ['New'], is_active: true,
    description: 'Featherlight responsive running shoes engineered for long-distance comfort.',
    images: [img(1542291026, 'shoes'), img(1542291024, 'shoes')],
  },
  {
    id: 'p4', sku: 'HM-LC-04', name: 'Lumina Ceramic Lamp', brand: 'Lumina', category_id: 'c3',
    category_name: 'Home & Living', price: 89, stock: 31, rating: 4.5, review_count: 450,
    tags: [], is_active: true,
    description: 'Hand-finished ceramic lamp with warm 2700K ambient glow and smart dimming.',
    images: [img(1507473885765, 'lamp'), img(1519947480111, 'lamp')],
  },
  {
    id: 'p5', sku: 'BT-RS-05', name: 'Velvet Radiance Serum', brand: 'Velvet', category_id: 'c4',
    category_name: 'Beauty', price: 54, compare_at_price: 69, stock: 5, rating: 4.4, review_count: 320,
    tags: ['Low Stock'], is_active: true,
    description: 'Vitamin-C radiance serum with hyaluronic acid for a luminous, dewy complexion.',
    images: [img(1620916560564, 'serum'), img(1620916560563, 'serum')],
  },
  {
    id: 'p6', sku: 'GM-PC-06', name: 'Vertex Gaming Laptop 15"', brand: 'Vertex', category_id: 'c7',
    category_name: 'Gaming', price: 1699, stock: 12, rating: 4.9, review_count: 610,
    tags: ['Premium'], is_active: true,
    description: 'RTX-class gaming laptop with 165Hz display, RGB keyboard, and AI frame boosting.',
    images: [img(1593642632823, 'laptop'), img(1593642634505, 'laptop')],
  },
  {
    id: 'p7', sku: 'FX-JK-07', name: 'Alpine Technical Jacket', brand: 'Alpine', category_id: 'c2',
    category_name: 'Fashion', price: 159, compare_at_price: 199, stock: 47, rating: 4.6, review_count: 520,
    tags: [], is_active: true,
    description: 'Weatherproof technical shell with thermal lining and stealth-pockets.',
    images: [img(1591047139829, 'jacket'), img(1591047139828, 'jacket')],
  },
  {
    id: 'p8', sku: 'GR-SD-08', name: 'Organic Morning Coffee 1kg', brand: 'Roastcraft', category_id: 'c6',
    category_name: 'Groceries', price: 24, stock: 4, rating: 4.8, review_count: 940,
    tags: ['Low Stock', 'AI Picked'], is_active: true,
    description: 'Single-origin medium roast with notes of chocolate and hazelnut. Certified organic.',
    images: [img(1447933603670, 'coffee'), img(1495474472287, 'coffee')],
  },
  {
    id: 'p9', sku: 'LX-PD-09', name: 'AirPods Max Style ANC Earbuds', brand: 'Nova', category_id: 'c1',
    category_name: 'Electronics', price: 79, stock: 120, rating: 4.3, review_count: 1300,
    tags: ['Value'], is_active: true,
    description: 'Affordable true-wireless earbuds with ANC, aptX, and 30h battery in a compact case.',
    images: [img(1590658268037, 'earbuds'), img(1606220838313, 'earbuds')],
  },
  {
    id: 'p10', sku: 'HM-TW-10', name: 'Nestwood Coffee Table', brand: 'Nestwood', category_id: 'c3',
    category_name: 'Home & Living', price: 220, stock: 0, rating: 4.7, review_count: 180,
    tags: [], is_active: true,
    description: 'Solid oak coffee table with a minimalist silhouette and hidden storage drawer.',
    images: [img(1538688525198, 'table'), img(1538688525197, 'table')],
  },
  {
    id: 'p11', sku: 'BT-PL-11', name: 'Botanical Repair Shampoo', brand: 'Velvet', category_id: 'c4',
    category_name: 'Beauty', price: 32, stock: 64, rating: 4.2, review_count: 210,
    tags: [], is_active: true,
    description: 'Sulfate-free repair shampoo with botanical oils for strengthened, glossy hair.',
    images: [img(1541643600914, 'shampoo'), img(1556228578, 'shampoo')],
  },
  {
    id: 'p12', sku: 'GM-CT-12', name: 'Aegis Mechanical Keyboard', brand: 'Vertex', category_id: 'c7',
    category_name: 'Gaming', price: 119, compare_at_price: 149, stock: 28, rating: 4.8, review_count: 780,
    tags: ['Best Seller'], is_active: true,
    description: 'Hot-swappable mechanical keyboard with per-key RGB and gasket mount.',
    images: [img(1587829741301, 'keyboard'), img(1587829741300, 'keyboard')],
  },
]

export const emptyProduct = products[9]
export const featuredProduct = products[0]

export const orders: Order[] = [
  {
    id: 'o1', order_number: 'SC-2026-00482', status: 'delivered', subtotal: 448, discount: 80, tax: 29,
    total_amount: 397, created_at: '2026-07-18T10:30:00Z', estimated_delivery: '2026-07-22T18:00:00Z',
    items: [products[0], products[1]].map((p, i) => ({
      id: `oi${i}`, product_id: p.id, product_name: p.name, sku: p.sku,
      quantity: i === 0 ? 1 : 2, unit_price: p.price ?? 0, total_price: (p.price ?? 0) * (i === 0 ? 1 : 2),
      image_url: p.images?.[0],
    })),
  },
  {
    id: 'o2', order_number: 'SC-2026-00391', status: 'shipped', subtotal: 129, discount: 0, tax: 8,
    total_amount: 137, created_at: '2026-07-29T09:12:00Z', estimated_delivery: '2026-08-03T18:00:00Z',
    items: [{ id: 'oi', product_id: products[2].id, product_name: products[2].name, sku: products[2].sku, quantity: 1, unit_price: 129, total_price: 129, image_url: products[2].images?.[0] }],
  },
  {
    id: 'o3', order_number: 'SC-2026-00340', status: 'processing', subtotal: 116, discount: 10, tax: 7,
    total_amount: 113, created_at: '2026-08-01T14:20:00Z', estimated_delivery: '2026-08-06T18:00:00Z',
    items: [products[8], products[7]].map((p, i) => ({
      id: `oi${i}`, product_id: p.id, product_name: p.name, sku: p.sku,
      quantity: i === 0 ? 1 : 2, unit_price: p.price ?? 0, total_price: (p.price ?? 0) * (i === 0 ? 1 : 2),
      image_url: p.images?.[0],
    })),
  },
]

export const addresses: Address[] = [
  {
    id: 'addr1', label: 'Home', name: 'Aarav Mehta', phone: '+91 98765 43210',
    line1: '14, Lakeview Residency, Powai', city: 'Mumbai', state: 'Maharashtra',
    postal_code: '400076', country: 'IN', is_default: true, type: 'home',
  },
  {
    id: 'addr2', label: 'Work', name: 'Aarav Mehta', phone: '+91 98765 43210',
    line1: 'WeWork, 8th Floor, BKC', city: 'Mumbai', state: 'Maharashtra',
    postal_code: '400051', country: 'IN', type: 'work',
  },
]

export const savedCards: SavedCard[] = [
  { id: 'card1', brand: 'Visa', last4: '4242', expiry: '08/28', name: 'Aarav Mehta', is_default: true },
  { id: 'card2', brand: 'Mastercard', last4: '510510', expiry: '11/27', name: 'Aarav Mehta' },
]

export const notifications: AppNotification[] = [
  { id: 'n1', type: 'order', title: 'Order shipped 🎉', message: 'Your order SC-2026-00391 is on its way and will arrive by Aug 3.', read: false, created_at: '2026-07-30T11:00:00Z' },
  { id: 'n2', type: 'price', title: 'Price drop on Nova Headphones', message: 'Nova Headphones dropped ₹$80. It\'s the lowest price in 90 days.', read: false, created_at: '2026-07-29T18:20:00Z' },
  { id: 'n3', type: 'ai', title: 'AI picks for you this week', message: 'Based on your mood board, we curated 4 new products you might love.', read: true, created_at: '2026-07-28T08:00:00Z' },
  { id: 'n4', type: 'promo', title: 'Weekend drop is live', message: 'Extra 10% off on selected electronics this weekend.', read: true, created_at: '2026-07-27T10:00:00Z' },
]

export const customers: Customer[] = [
  { id: 'cu1', name: 'Aarav Mehta', email: 'aarav@example.com', orders: 24, spent: 12840, status: 'vip', joined: '2024-11-12' },
  { id: 'cu2', name: 'Priya Sharma', email: 'priya@example.com', orders: 18, spent: 9320, status: 'active', joined: '2025-02-03' },
  { id: 'cu3', name: 'Rohan Verma', email: 'rohan@example.com', orders: 3, spent: 1450, status: 'new', joined: '2026-06-20' },
  { id: 'cu4', name: 'Sneha Iyer', email: 'sneha@example.com', orders: 41, spent: 22100, status: 'vip', joined: '2023-08-01' },
  { id: 'cu5', name: 'Kabir Khan', email: 'kabir@example.com', orders: 0, spent: 0, status: 'dormant', joined: '2025-09-14' },
  { id: 'cu6', name: 'Meera Nair', email: 'meera@example.com', orders: 9, spent: 4300, status: 'active', joined: '2025-12-05' },
]

export const inventory: InventoryRow[] = [
  { id: 'p1', sku: 'NV-HP-01', name: 'Nova Wireless Headphones', category: 'Electronics', stock: 42, reserved: 6, reorder_level: 20, status: 'in_stock', updated_at: '2026-08-01T09:00:00Z' },
  { id: 'p2', sku: 'LX-SM-02', name: 'Aurum Smartwatch 7', category: 'Electronics', stock: 18, reserved: 2, reorder_level: 15, status: 'low', updated_at: '2026-08-01T09:00:00Z' },
  { id: 'p5', sku: 'BT-RS-05', name: 'Velvet Radiance Serum', category: 'Beauty', stock: 5, reserved: 1, reorder_level: 20, status: 'critical', updated_at: '2026-08-01T09:00:00Z' },
  { id: 'p8', sku: 'GR-SD-08', name: 'Organic Morning Coffee', category: 'Groceries', stock: 4, reserved: 0, reorder_level: 25, status: 'critical', updated_at: '2026-08-01T09:00:00Z' },
  { id: 'p10', sku: 'HM-TW-10', name: 'Nestwood Coffee Table', category: 'Home & Living', stock: 0, reserved: 0, reorder_level: 5, status: 'out', updated_at: '2026-08-01T09:00:00Z' },
  { id: 'p12', sku: 'GM-CT-12', name: 'Aegis Keyboard', category: 'Gaming', stock: 28, reserved: 4, reorder_level: 10, status: 'in_stock', updated_at: '2026-08-01T09:00:00Z' },
  { id: 'p9', sku: 'LX-PD-09', name: 'ANC Earbuds', category: 'Electronics', stock: 120, reserved: 15, reorder_level: 40, status: 'in_stock', updated_at: '2026-08-01T09:00:00Z' },
]

export const activity: ActivityEvent[] = [
  { id: 'a1', type: 'auth', user: 'Aarav Mehta', action: 'logged_in', resource: 'session', detail: 'Login from 103.21.58.4', ip: '103.21.58.4', severity: 'info', created_at: '2026-08-01T10:04:00Z' },
  { id: 'a2', type: 'inventory', user: 'System', action: 'low_stock', resource: 'inventory', detail: 'BT-RS-05 dropped below reorder level', severity: 'warning', created_at: '2026-08-01T09:41:00Z' },
  { id: 'a3', type: 'order', user: 'Priya Sharma', action: 'refunded', resource: 'order SC-2026-00312', detail: 'Refund of ₹420 issued', severity: 'info', created_at: '2026-08-01T08:55:00Z' },
  { id: 'a4', type: 'ai', user: 'A.I. Engine', action: 'detection', resource: 'vision', detail: 'Detected "Wireless Headphones" @ 97.2% confidence', severity: 'info', created_at: '2026-08-01T08:30:00Z' },
  { id: 'a5', type: 'security', user: 'System', action: 'rate_limited', resource: '/auth/login', detail: 'Multiple failed attempts from 45.12.9.3', ip: '45.12.9.3', severity: 'critical', created_at: '2026-08-01T07:15:00Z' },
  { id: 'a6', type: 'catalog', user: 'Admin', action: 'published', resource: 'product p12', detail: 'Aegis Mechanical Keyboard set live', severity: 'info', created_at: '2026-07-31T22:10:00Z' },
]

export const detectionLogs: DetectionLog[] = [
  { id: 'd1', request_id: 'req-9f1ac', object_type: 'Wireless Headphones', confidence: 0.972, status: 'matched', product_id: 'p1', latency_ms: 184, created_at: '2026-08-01T08:30:00Z' },
  { id: 'd2', request_id: 'req-8cd2e', object_type: 'Smartwatch', confidence: 0.941, status: 'matched', product_id: 'p2', latency_ms: 212, created_at: '2026-08-01T07:55:00Z' },
  { id: 'd3', request_id: 'req-77be1', object_type: 'Running Shoes', confidence: 0.888, status: 'unmatched', latency_ms: 190, created_at: '2026-08-01T07:12:00Z' },
  { id: 'd4', request_id: 'req-65ff0', object_type: 'Ceramic Lamp', confidence: 0.665, status: 'unmatched', latency_ms: 205, created_at: '2026-07-31T23:40:00Z' },
  { id: 'd5', request_id: 'req-5aa9d', object_type: 'Coffee Bag', confidence: 0.934, status: 'matched', product_id: 'p8', latency_ms: 158, created_at: '2026-07-31T19:02:00Z' },
]