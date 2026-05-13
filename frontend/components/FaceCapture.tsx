'use client';

import { useEffect, useRef, useState } from 'react';

export type CameraSource = 'laptop' | 'external';

interface Props {
  onCapture: (blob: Blob, source: CameraSource) => void;
  onError?: (msg: string) => void;
  disabled?: boolean;
}

export default function FaceCapture({ onCapture, onError, disabled }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [source, setSource] = useState<CameraSource>('laptop');
  const [ready, setReady] = useState(false);
  const [captured, setCaptured] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);

  useEffect(() => {
    if (source === 'laptop') {
      startCamera();
    } else {
      stopCamera();
    }
    return () => stopCamera();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [source]);

  async function startCamera() {
    stopCamera();
    setCaptured(false);
    setPreview(null);
    setReady(false);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => setReady(true);
      }
    } catch {
      onError?.('Нет доступа к камере ноутбука.');
    }
  }

  function stopCamera() {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setReady(false);
  }

  function handleCapture() {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d')?.drawImage(video, 0, 0);

    canvas.toBlob((blob) => {
      if (!blob) { onError?.('Не удалось захватить кадр.'); return; }
      const url = URL.createObjectURL(blob);
      setPreview(url);
      setCaptured(true);
      stopCamera();
      onCapture(blob, source);
    }, 'image/jpeg', 0.92);
  }

  function handleRetake() {
    if (preview) URL.revokeObjectURL(preview);
    setPreview(null);
    setCaptured(false);
    startCamera();
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Выбор источника */}
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => setSource('laptop')}
          className={`flex-1 py-1.5 rounded-lg text-sm font-medium transition-colors ${
            source === 'laptop'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          Ноутбук
        </button>
        <button
          type="button"
          onClick={() => setSource('external')}
          className={`flex-1 py-1.5 rounded-lg text-sm font-medium transition-colors ${
            source === 'external'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          Камера УК
        </button>
      </div>

      {/* Область камеры */}
      {source === 'external' ? (
        <div className="flex flex-col items-center justify-center h-48 rounded-xl border-2 border-dashed border-gray-300 bg-gray-50 text-gray-400 gap-2">
          <svg className="w-10 h-10 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M15 10l4.553-2.276A1 1 0 0121 8.723v6.554a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />
          </svg>
          <span className="text-sm font-medium">Камера УК не подключена</span>
          <span className="text-xs">Функция будет доступна после подключения</span>
        </div>
      ) : (
        <div className="relative rounded-xl overflow-hidden bg-black aspect-video">
          {!captured ? (
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
            />
          ) : (
            preview && (
              <img src={preview} alt="Снимок" className="w-full h-full object-cover" />
            )
          )}
          {!ready && !captured && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/60 text-white text-sm">
              Запуск камеры…
            </div>
          )}
          {/* прицел */}
          {ready && !captured && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="w-36 h-44 rounded-full border-2 border-white/50" />
            </div>
          )}
        </div>
      )}

      <canvas ref={canvasRef} className="hidden" />

      {/* Кнопки */}
      {source === 'laptop' && (
        <div className="flex gap-2">
          {!captured ? (
            <button
              type="button"
              onClick={handleCapture}
              disabled={!ready || disabled}
              className="flex-1 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium
                         hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Сделать фото
            </button>
          ) : (
            <button
              type="button"
              onClick={handleRetake}
              disabled={disabled}
              className="flex-1 py-2 rounded-lg bg-gray-200 text-gray-700 text-sm font-medium
                         hover:bg-gray-300 disabled:opacity-50 transition-colors"
            >
              Переснять
            </button>
          )}
        </div>
      )}
    </div>
  );
}
