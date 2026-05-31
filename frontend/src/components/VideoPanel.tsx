import { useLatestVideo } from "../hooks/useDigest";
import { api } from "../api/client";

export function VideoPanel({ onClose }: { onClose: () => void }) {
  const { data: video, isLoading, isError, refetch } = useLatestVideo();

  const isMp4 = video?.media_url?.endsWith(".mp4");

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <h2>Daily Summary Video</h2>
          <button className="close" onClick={onClose}>
            ✕
          </button>
        </div>

        {isLoading && <p className="state">Loading…</p>}

        {isError && (
          <div className="state">
            <p>No video generated yet.</p>
            <button
              className="video-btn"
              onClick={async () => {
                await api.generateVideo();
                setTimeout(() => refetch(), 4000);
              }}
            >
              Generate now
            </button>
          </div>
        )}

        {video && (
          <>
            {isMp4 ? (
              <video controls className="player" src={video.media_url!} />
            ) : (
              <div className="script-fallback">
                <p className="dim">
                  Video assets not rendered (install the <code>video</code> extra
                  to enable MP4). Showing the generated script:
                </p>
              </div>
            )}
            <details className="script-box" open={!isMp4}>
              <summary>Narration script</summary>
              <pre>{video.script}</pre>
            </details>
          </>
        )}
      </div>
    </div>
  );
}
