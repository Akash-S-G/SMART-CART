import { useState, useRef, useMemo, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Upload,
  Info,
  ScanLine,
  Verified,
  ArrowRight,
  ShoppingCart,
  Cpu,
  Trash2,
  AlertCircle,
  HelpCircle,
  FileImage,
  RefreshCw,
  Plus,
  Minus,
  ArrowLeft,
  Camera,
  Video,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { detectImageApi, listProductsApi } from '@/lib/api'
import { useCart } from '@/hooks/use-cart'
import { useToast } from '@/components/ui/use-toast'
import type { DetectionResult } from '@/types/api'

export function ScannerPage() {
  const navigate = useNavigate()
  const { addItem } = useCart()
  const { toast } = useToast()

  const [scanMode, setScanMode] = useState<'upload' | 'camera'>('upload')
  const [file, setFile] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [scanning, setScanning] = useState(false)
  const [isCameraActive, setIsCameraActive] = useState(false)

  const [results, setResults] = useState<{
    detections: DetectionResult[]
    imageWidth: number
    imageHeight: number
  } | null>(null)

  // Track quantity per item index
  const [detectedQtys, setDetectedQtys] = useState<Record<number, number>>({})

  const [hoveredBoxIdx, setHoveredBoxIdx] = useState<number | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } },
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
      setIsCameraActive(true)
      toast({ title: 'Live Camera Active', description: 'Point your camera at groceries to scan.' })
    } catch {
      toast({
        title: 'Camera Access Denied',
        description: 'Unable to access WebCam. Please use photo upload mode.',
        variant: 'destructive',
      })
      setScanMode('upload')
    }
  }

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
    setIsCameraActive(false)
  }

  const captureFrame = () => {
    if (!videoRef.current) return
    const video = videoRef.current
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth || 640
    canvas.height = video.videoHeight || 480
    const ctx = canvas.getContext('2d')
    if (ctx) {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
      canvas.toBlob((blob) => {
        if (blob) {
          const frameFile = new File([blob], 'camera_snapshot.jpg', { type: 'image/jpeg' })
          setImagePreview(canvas.toDataURL('image/jpeg'))
          triggerScan(frameFile)
        }
      }, 'image/jpeg')
    }
  }

  useEffect(() => {
    return () => {
      stopCamera()
    }
  }, [])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0]
    if (selected) {
      setFile(selected)
      setImagePreview(URL.createObjectURL(selected))
      setResults(null)
      setDetectedQtys({})
      triggerScan(selected)
    }
  }

  const triggerScan = async (selectedFile: File) => {
    setScanning(true)
    try {
      const data = await detectImageApi(selectedFile)
      let finalDetections = data.detections || []

      if (finalDetections.length === 0) {
        toast({
          title: 'No Objects Detected',
          description: 'No grocery products were recognized in this image. Try uploading a clearer photo.',
          variant: 'default',
        })
      }

      const initialQtys: Record<number, number> = {}
      finalDetections.forEach((_, idx) => {
        initialQtys[idx] = 1
      })
      setDetectedQtys(initialQtys)

      setResults({
        detections: finalDetections,
        imageWidth: data.image_width || 640,
        imageHeight: data.image_height || 480,
      })

      if (finalDetections.length > 0) {
        toast({
          title: 'Scan Complete',
          description: `Successfully identified ${finalDetections.length} product(s) from real vision model.`,
        })
      }
    } catch (err: any) {
      toast({
        title: 'Scan Failed',
        description: err?.message || 'Unable to connect to AI vision server.',
        variant: 'destructive',
      })
    } finally {
      setScanning(false)
    }
  }

  const handleQtyChange = (index: number, change: number) => {
    setDetectedQtys((prev) => {
      const current = prev[index] || 1
      const next = current + change

      if (next <= 0) {
        // Remove item from detections list
        if (results) {
          const updatedDetections = results.detections.filter((_, idx) => idx !== index)

          // Re-map remaining quantities to correct shift indexing
          const nextQtys: Record<number, number> = {}
          updatedDetections.forEach((_, newIdx) => {
            const oldIdx = newIdx >= index ? newIdx + 1 : newIdx
            nextQtys[newIdx] = prev[oldIdx] || 1
          })

          setResults({
            ...results,
            detections: updatedDetections,
          })
          setDetectedQtys(nextQtys)
        }
        return prev
      }

      return {
        ...prev,
        [index]: next,
      }
    })
  }

  const handleProcessItems = async () => {
    if (!results || results.detections.length === 0) return

    let addedCount = 0
    let failedCount = 0

    for (let i = 0; i < results.detections.length; i++) {
      const d = results.detections[i]
      const p = d.matched_product
      const qty = detectedQtys[i] || 1

      if (p && qty > 0) {
        try {
          await addItem(p.id, qty)
          addedCount++
        } catch (err) {
          failedCount++
        }
      }
    }

    if (failedCount > 0 && addedCount === 0) {
      toast({
        title: 'Authentication Required',
        description: 'Please sign in to add these items to your cart.',
        variant: 'destructive',
      })
    } else {
      toast({
        title: 'Cart Updated',
        description: `Successfully added identified items to your shopping cart.`,
      })
      navigate('/checkout')
    }
  }

  const detectedItems = useMemo(() => {
    if (!results) return []
    return results.detections.map((d, index) => {
      const p = d.matched_product
      return {
        index,
        name: p?.name || d.object_type || 'Unknown Product',
        price: p?.price || 0,
        confidence: Math.round(d.confidence * 100),
        thumbnail: p?.images?.[0] || 'https://images.unsplash.com/photo-1505743614?auto=format&fit=crop&w=900&q=80',
        productId: p?.id || '',
      }
    })
  }, [results])

  const totalAmount = useMemo(() => {
    return detectedItems.reduce((sum, item) => sum + item.price * (detectedQtys[item.index] || 1), 0)
  }, [detectedItems, detectedQtys])

  return (
    <div className="mx-auto max-w-7xl px-6 py-10">
      <Button
        variant="ghost"
        onClick={() => navigate(-1)}
        className="mb-4 rounded-xl text-xs font-semibold gap-1.5 px-3 py-1.5 h-auto text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back
      </Button>
      <div className="max-w-2xl">
        <Badge variant="ai" className="gap-1.5 px-3 py-1">
          <ScanLine className="h-3.5 w-3.5 text-secondary" /> AI Vision Engine
        </Badge>
        <h1 className="mt-4 text-4xl font-sans font-extrabold tracking-tight text-foreground">
          Computer Vision Checkout
        </h1>
        <div className="flex justify-between items-end flex-wrap gap-4 mt-6">
          <div className="flex gap-2 bg-black/[0.04] p-1.5 rounded-2xl border border-border">
            <button
              onClick={() => {
                setScanMode('upload')
                stopCamera()
              }}
              className={`flex items-center gap-2 text-xs font-bold px-4 py-2 rounded-xl transition ${
                scanMode === 'upload' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Upload className="h-3.5 w-3.5" /> Upload Snapshot
            </button>
            <button
              onClick={() => {
                setScanMode('camera')
                startCamera()
              }}
              className={`flex items-center gap-2 text-xs font-bold px-4 py-2 rounded-xl transition ${
                scanMode === 'camera' ? 'bg-primary text-primary-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Camera className="h-3.5 w-3.5" /> Live WebCam Stream
            </button>
          </div>
        </div>
      </div>

      <div className="mt-8 grid gap-8 lg:grid-cols-[1fr_400px]">
        {/* Left: Scanner Visualizer */}
        <div className="flex flex-col gap-6">
          <div className="relative rounded-3xl border border-border bg-card/40 p-4 shadow-sm flex items-center justify-center min-h-[380px] overflow-hidden group">
            {scanMode === 'camera' ? (
              <div className="relative w-full max-w-full overflow-hidden rounded-2xl border border-black/10 flex flex-col items-center">
                <video ref={videoRef} autoPlay playsInline muted className="w-full max-h-[480px] object-cover rounded-2xl" />
                <div className="absolute top-4 left-4 z-10">
                  <Badge variant="ai" className="gap-1.5 px-3 py-1 bg-red-600/90 text-white border-none animate-pulse">
                    <Video className="h-3.5 w-3.5" /> Live Camera
                  </Badge>
                </div>
                <div className="absolute bottom-4 inset-x-0 flex justify-center gap-3 z-10">
                  <Button variant="gradient" onClick={captureFrame} disabled={scanning} className="rounded-2xl shadow-xl font-bold uppercase text-xs px-6 py-5 gap-2">
                    <ScanLine className="h-4 w-4" /> Snap & Analyze Basket
                  </Button>
                  <Button variant="secondary" onClick={stopCamera} className="rounded-2xl font-bold uppercase text-xs px-4 py-5">
                    Stop Stream
                  </Button>
                </div>
              </div>
            ) : imagePreview ? (
              <div className="relative max-w-full max-h-[500px] overflow-hidden rounded-2xl border border-black/10">
                <img src={imagePreview} alt="Basket Snapshot" className="max-w-full max-h-[500px] object-contain" />

                {scanning && (
                  <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-transparent via-secondary to-transparent shadow-[0_0_12px_rgba(235,94,85,1)] animate-laser pointer-events-none" />
                )}

                {results && !scanning && (
                  <svg
                    className="absolute inset-0 w-full h-full pointer-events-none"
                    viewBox={`0 0 ${results.imageWidth} ${results.imageHeight}`}
                    preserveAspectRatio="none"
                  >
                    {results.detections.map((d, idx) => {
                      let x = 0, y = 0, w = 0, h = 0
                      if (d.bbox) {
                        x = d.bbox.x
                        y = d.bbox.y
                        w = d.bbox.width
                        h = d.bbox.height
                      } else if (Array.isArray((d as any).detection?.bbox)) {
                        const bbox = (d as any).detection.bbox
                        x = bbox[0]
                        y = bbox[1]
                        w = bbox[2] - bbox[0]
                        h = bbox[3] - bbox[1]
                      } else {
                        return null
                      }

                      const isHovered = hoveredBoxIdx === idx
                      return (
                        <g key={idx}>
                          <rect
                            x={x}
                            y={y}
                            width={w}
                            height={h}
                            className={`transition-all duration-200 fill-transparent stroke-2 ${
                              isHovered ? 'stroke-secondary fill-secondary/10' : 'stroke-primary fill-transparent'
                            }`}
                          />
                          <foreignObject x={x} y={y - 25} width={Math.max(w, 120)} height={25}>
                            <div
                              className={`text-[10px] font-bold px-1.5 py-0.5 rounded-t text-white transition-colors duration-200 inline-block truncate ${
                                isHovered ? 'bg-secondary' : 'bg-primary'
                              }`}
                            >
                              {d.matched_product?.name || d.object_type} ({Math.round(d.confidence * 100)}%)
                            </div>
                          </foreignObject>
                        </g>
                      )
                    })}
                  </svg>
                )}
              </div>
            ) : (
              <div
                onClick={() => fileInputRef.current?.click()}
                className="flex flex-col items-center justify-center py-20 text-center cursor-pointer w-full"
              >
                <div className="w-16 h-16 bg-black/[0.03] text-muted-foreground flex items-center justify-center rounded-2xl mb-4 group-hover:scale-105 transition-transform duration-300">
                  <Upload className="h-6 w-6" />
                </div>
                <h3 className="font-bold text-foreground text-base">Select image files to analyze</h3>
                <p className="text-xs text-muted-foreground max-w-sm mt-1 leading-relaxed">
                  Support JPEG or PNG captures. Ensure objects are placed horizontally without occlusion.
                </p>
                <Button variant="secondary" className="mt-6 rounded-xl">
                  Browse Files
                </Button>
              </div>
            )}

            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept="image/*"
              className="hidden"
            />
          </div>

          {imagePreview && !scanning && (
            <div className="flex gap-4">
              <Button
                variant="secondary"
                className="flex-1 rounded-xl py-5"
                onClick={() => fileInputRef.current?.click()}
              >
                <RefreshCw className="h-4 w-4 mr-2" /> Reselect Image
              </Button>
              <Button
                variant="destructive"
                className="rounded-xl px-5"
                onClick={() => {
                  setFile(null)
                  setImagePreview(null)
                  setResults(null)
                  setDetectedQtys({})
                }}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>

        {/* Right: Detected Products Summary */}
        <div className="flex flex-col gap-6">
          <div className="glass border border-white/5 rounded-3xl p-6 shadow-sm">
            <div className="flex justify-between items-center mb-6 border-b border-black/[0.06] pb-4">
              <div className="flex items-center gap-2">
                <Badge success className="px-2.5 py-0.5">
                  <Verified className="h-3 w-3" /> Identified
                </Badge>
                <span className="text-sm font-bold text-foreground">{detectedItems.length} items</span>
              </div>
              {scanning && (
                <span className="flex items-center gap-1.5 text-xs text-secondary font-semibold animate-pulse">
                  <LoaderIcon className="h-3.5 w-3.5 animate-spin" /> Processing
                </span>
              )}
            </div>

            {detectedItems.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground text-xs leading-relaxed flex flex-col items-center gap-3">
                <FileImage className="h-10 w-10 text-muted-foreground/30" />
                <span>Upload an image to display neural prediction matches.</span>
              </div>
            ) : (
              <ul className="divide-y divide-black/[0.04] max-h-[350px] overflow-y-auto pr-2">
                {detectedItems.map((item) => (
                  <li
                    key={item.index}
                    onMouseEnter={() => setHoveredBoxIdx(item.index)}
                    onMouseLeave={() => setHoveredBoxIdx(null)}
                    className={`flex items-center gap-4 py-3.5 transition-colors rounded-xl px-2 ${
                      hoveredBoxIdx === item.index ? 'bg-black/[0.03]' : ''
                    }`}
                  >
                    <img src={item.thumbnail} alt={item.name} className="w-12 h-12 rounded-xl object-cover border border-black/5" />
                    <div className="min-w-0 flex-1">
                      <p className="font-bold text-sm text-foreground truncate">{item.name}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[10px] text-muted-foreground">Conf: {item.confidence}%</span>
                        {item.confidence < 70 && (
                          <Badge warning className="text-[9px] px-1.5 py-0">Low Confidence</Badge>
                        )}
                        <span className="text-muted-foreground/30">·</span>
                        
                        {/* Interactive Quantity Adjuster */}
                        <div className="flex items-center bg-black/[0.03] p-0.5 rounded-lg border">
                          <button
                            type="button"
                            onClick={() => handleQtyChange(item.index, -1)}
                            className="p-1 text-muted-foreground hover:text-foreground transition-colors"
                            aria-label="Decrease quantity"
                          >
                            <Minus className="h-3 w-3" />
                          </button>
                          <span className="w-5 text-center font-mono text-xs font-bold text-foreground">
                            {detectedQtys[item.index] || 1}
                          </span>
                          <button
                            type="button"
                            onClick={() => handleQtyChange(item.index, 1)}
                            className="p-1 text-muted-foreground hover:text-foreground transition-colors"
                            aria-label="Increase quantity"
                          >
                            <Plus className="h-3 w-3" />
                          </button>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-sm text-foreground">₹{item.price * (detectedQtys[item.index] || 1)}</p>
                      <span className="text-[10px] text-success font-semibold">Match</span>
                    </div>
                  </li>
                ))}
              </ul>
            )}

            <div className="border-t border-black/[0.06] pt-4 mt-6 flex justify-between items-center text-sm">
              <span className="text-muted-foreground">Subtotal Estimate</span>
              <span className="font-black text-lg text-foreground">₹{totalAmount.toFixed(2)}</span>
            </div>
          </div>

          <Button
            variant="gradient"
            size="lg"
            className="w-full py-6 rounded-xl text-sm uppercase tracking-widest font-semibold gap-2"
            disabled={detectedItems.length === 0 || scanning}
            onClick={handleProcessItems}
          >
            <ShoppingCart className="h-4 w-4" /> Add All to Cart <ArrowRight className="h-4 w-4" />
          </Button>

          <div className="rounded-2xl border border-black/[0.08] bg-card/50 p-5 flex gap-3.5 items-start">
            <Info className="h-5 w-5 text-warning shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h5 className="font-bold text-foreground text-xs uppercase tracking-wider">Analysis notes</h5>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                YOLO vision models extract product bounding dimensions. Matches with validation score below 80% are flagged as guest elements requiring human audit.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function LoaderIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  )
}