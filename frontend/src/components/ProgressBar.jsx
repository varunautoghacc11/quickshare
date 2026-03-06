export default function ProgressBar({ progress }) {
  return (
    <div className="progress-bar-wrap" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
      <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
      <span className="progress-label">{progress}%</span>
    </div>
  )
}
