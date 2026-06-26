/**
 * Player — reproductor simple con seek expuesto.
 *
 * Si hay URL de grabación, usa <video controls>. Si NO hay grabación, muestra
 * un placeholder elegante pero igual permite el "seek visual": mantiene un
 * estado de currentTime simulado que los chips actualizan.
 *
 * Expone un handle imperativo con seekTo(seconds).
 */
import {
  forwardRef,
  useImperativeHandle,
  useRef,
  useState,
} from "react";
import { Film } from "lucide-react";
import { formatTime } from "./TimestampChip";

export interface PlayerHandle {
  seekTo: (seconds: number) => void;
}

interface PlayerProps {
  recordingUrl?: string;
  durationSeconds?: number;
  /** Notifica el tiempo actual (para sincronizar la cinta). */
  onTimeChange?: (seconds: number) => void;
}

const Player = forwardRef<PlayerHandle, PlayerProps>(function Player(
  { recordingUrl, durationSeconds = 0, onTimeChange },
  ref,
) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [simTime, setSimTime] = useState(0);
  const hasVideo = Boolean(recordingUrl);

  useImperativeHandle(ref, () => ({
    seekTo(seconds: number) {
      if (hasVideo && videoRef.current) {
        videoRef.current.currentTime = seconds;
        void videoRef.current.play().catch(() => {
          /* autoplay puede estar bloqueado; no pasa nada */
        });
      } else {
        setSimTime(seconds);
      }
      onTimeChange?.(seconds);
    },
  }));

  if (hasVideo) {
    return (
      <video
        ref={videoRef}
        src={recordingUrl}
        controls
        className="aspect-video w-full rounded-card border border-line bg-ink"
        onTimeUpdate={(e) =>
          onTimeChange?.((e.target as HTMLVideoElement).currentTime)
        }
      />
    );
  }

  // Placeholder elegante con cabezal simulado.
  const pct =
    durationSeconds > 0
      ? Math.min(100, (simTime / durationSeconds) * 100)
      : 0;

  return (
    <div className="flex aspect-video w-full flex-col items-center justify-center gap-3 rounded-card border border-dashed border-line bg-white p-6 text-center">
      <Film className="h-8 w-8 text-inkSoft" aria-hidden="true" />
      <p className="text-sm font-medium text-ink">
        Grabación no disponible en demo
      </p>
      <p className="max-w-sm text-xs text-inkSoft">
        Puedes navegar la clase desde los timestamps: cada marca de evidencia
        mueve el cabezal a su momento.
      </p>
      <div className="mt-2 w-full max-w-md">
        <div className="relative h-2 w-full overflow-hidden rounded-full bg-line">
          <div
            className="absolute left-0 top-0 h-full bg-evidence transition-all"
            style={{ width: `${pct}%` }}
          />
        </div>
        <div className="mt-1 flex justify-between font-mono text-xs text-inkSoft">
          <span>{formatTime(simTime)}</span>
          <span>{formatTime(durationSeconds)}</span>
        </div>
      </div>
    </div>
  );
});

export default Player;
